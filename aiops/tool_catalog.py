"""Adapt EXISTING implementation modules to agent protocols (no reimplementations)."""
from __future__ import annotations

from aiops.registry import tool


@tool(name="file_to_text")
def file_to_text(path: str, max_tokens: int = 4000) -> str:
    """Extract compact text from a local PDF, DOCX, HTML, CSV, JSON or text file."""
    from aiops.docs.extract import to_text
    from aiops.text.ops import compact
    return compact(to_text(path), max_tokens)


@tool(name="compact_text")
def compact_text(text: str, max_tokens: int = 2000) -> str:
    """Clean text, remove boilerplate and duplicates, then trim to a budget."""
    from aiops.text.ops import compact
    return compact(text, max_tokens)


@tool(name="count_tokens")
def count_tokens(text: str) -> int:
    """Estimate tokens heuristically, using approximately four characters per token."""
    from aiops.text.ops import estimate_tokens
    return estimate_tokens(text)


@tool(name="text_diff")
def text_diff(before: str, after: str) -> str:
    """Generate a compact unified diff between two strings."""
    from aiops.text.ops import diff
    return diff(before, after)


@tool(name="job_check")
def job_check(title: str, company: str, location: str, description: str,
              config_path: str = "config.yaml") -> dict:
    """Apply existing job filters, CV selection and fit scoring rules."""
    from aiops.jobs.config import load_config
    from aiops.jobs.models import Job
    from aiops.jobs.pipeline import process
    job = process(Job(url=f"mcp://{company}/{title}", title=title,
                      company=company, location=location,
                      description=description), load_config(config_path))
    return {"status": job.status, "reasons": job.reasons,
            "cv": job.cv_version, "score": job.score,
            "matched": job.flags.get("matched_skills")}


@tool(name="srt_to_chapters")
def srt_to_chapters(srt_text: str, markers: list[str] | None = None) -> str:
    """Generate chapters from SRT subtitles using existing timestamp logic."""
    from aiops.youtube import tools as yt
    segments = yt.parse_srt(srt_text)
    chapters = (yt.chapters_from_markers(segments, markers) if markers
                else yt.chapters_by_gap(segments))
    return yt.chapters_text(chapters)


@tool(name="local_llm", tier="llm")
def local_llm(prompt: str, schema: dict | None = None) -> str | dict:
    """Run the existing cached local Ollama integration for basic extraction."""
    from aiops.core import llm
    return llm.local(prompt, schema=schema)
