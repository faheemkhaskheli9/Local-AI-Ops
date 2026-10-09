"""MCP server: lets Claude (Desktop / Code) call these tools directly.

Claude then runs a cheap, repeatable function instead of reading a whole
file into context or doing the work itself.

Add to Claude Desktop's config (Settings > Developer > Edit Config):

    {"mcpServers": {"aiops": {"command": "aiops", "args": ["mcp"]}}}

Claude Code:  claude mcp add aiops -- aiops mcp
"""
from __future__ import annotations


def build():
    try:  # mcp 2.x
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP as Server

    from aiops.docs.extract import to_text
    from aiops.text import ops

    mcp = Server("aiops")

    @mcp.tool()
    def file_to_text(path: str, max_tokens: int = 4000) -> str:
        """Read a PDF, DOCX, HTML, CSV, JSON or text file as compact plain text,
        trimmed to max_tokens. Use this instead of reading big files raw."""
        return ops.compact(to_text(path), max_tokens)

    @mcp.tool()
    def compact_text(text: str, max_tokens: int = 2000) -> str:
        """Clean text: normalize, drop boilerplate and repeated lines, trim to budget."""
        return ops.compact(text, max_tokens)

    @mcp.tool()
    def count_tokens(text: str) -> int:
        """Rough token estimate (chars / 4)."""
        return ops.estimate_tokens(text)

    @mcp.tool()
    def text_diff(before: str, after: str) -> str:
        """Unified diff between two texts."""
        return ops.diff(before, after)

    @mcp.tool()
    def job_check(title: str, company: str, location: str, description: str,
                  config_path: str = "config.yaml") -> dict:
        """Run the deterministic job checks: visa/language/title filters,
        CV version pick and fit score. Returns status, reasons, cv and score."""
        from aiops.jobs.config import load_config
        from aiops.jobs.models import Job
        from aiops.jobs.pipeline import process

        job = process(Job(url=f"mcp://{company}/{title}", title=title, company=company,
                          location=location, description=description),
                      load_config(config_path))
        return {"status": job.status, "reasons": job.reasons, "cv": job.cv_version,
                "score": job.score, "matched": job.flags.get("matched_skills")}

    @mcp.tool()
    def srt_to_chapters(srt_text: str, markers: list[str] | None = None) -> str:
        """Make a YouTube chapter list from SRT subtitles."""
        from aiops.youtube import tools as yt

        segs = yt.parse_srt(srt_text)
        chs = yt.chapters_from_markers(segs, markers) if markers else yt.chapters_by_gap(segs)
        return yt.chapters_text(chs)

    @mcp.tool()
    def local_llm(prompt: str, schema: dict | None = None) -> str | dict:
        """Ask the local Ollama model (temperature 0, cached). Use for simple
        extraction or classification to save Claude tokens."""
        from aiops.core import llm

        return llm.local(prompt, schema=schema)

    return mcp


def run() -> None:
    build().run()
