# Use AI Ops from ChatGPT, Claude, Codex and your own agents

This repository already provides an MCP stdio adapter: `aiops mcp`. It exposes `file_to_text`, `compact_text`, `count_tokens`, `text_diff`, `job_check`, `srt_to_chapters`, and `local_llm`. The same core logic also runs from the `aiops` CLI and from Python imports.

**Strategy:** use Python for deterministic transforms, Ollama for inexpensive local classification/extraction, and ChatGPT/Claude for complex decisions. Avoid sending untrimmed PDFs, full job descriptions, SRT files, and repeat prompts to expensive LLMs.

## First: install on the machine running your AI client

```bash
git clone https://github.com/faheemkhaskheli9/Local-AI-Ops.git
cd Local-AI-Ops
python -m venv .venv
# Activate it on your OS, then:
python -m pip install -e '.[mcp]'
# Optional for local inference:
ollama pull qwen2.5:7b
```

Use the absolute path to the virtual environment's `aiops` executable in production client settings. On Windows this is under `.venv\\Scripts\\aiops.exe`; on Linux/macOS under `.venv/bin/aiops`. An MCP stdio server intentionally does not print a welcome banner; its standard output carries protocol messages.

## Recommended integrations

| Client | Best mechanism | Access to local computer | Notes |
| --- | --- | --- | --- |
| Claude Code | MCP stdio or `aiops` CLI | Yes | Best for repository work and shell-driven tasks |
| Claude Desktop | Local MCP / desktop extension (`.mcpb`) | Yes | Desktop app must have the local dependencies |
| Codex CLI / IDE | MCP stdio, CLI, AGENTS.md | Yes, when running locally | Can also reference project instructions |
| ChatGPT Desktop | Local MCP plugin, where supported | Yes, on supported desktop surfaces | Local tools are not automatically available in web/mobile |
| ChatGPT web/mobile | Custom remote MCP plugin or secure tunnel | No direct local stdio | Remote server needs authentication and HTTPS |
| Claude web/mobile | Custom remote MCP connector | No direct local stdio | Connector requests come from Anthropic's cloud |
| OpenAI/Anthropic API agents | Function calling; MCP connector | In your own executor; or via remote MCP | You own the tool execution and validation |
| Custom GPT Actions | REST/OpenAPI with auth | Only through hosted API | Legacy alternative; prefer plugins for new ChatGPT integrations |
| VS Code / Cursor | MCP stdio | Yes | IDE MCP config refers to installed `aiops` |
| n8n/GitHub Actions/cron | CLI, Python functions, webhooks | Wherever runner executes | Deterministic tasks need no LLM at all |
| File handoff | Markdown/JSON reports | Via attachment/sync | Easiest low-trust fallback |

## Claude Code

```bash
claude mcp add --transport stdio aiops -- /absolute/path/to/Local-AI-Ops/.venv/bin/aiops mcp
claude mcp list
```

Then prompt Claude: “Use the `job_check` tool to evaluate this job. Use `local_llm` only for extraction. Send the final short reasoning to the cloud model.”

## Claude Desktop

Configure its local MCP server (or make an `.mcpb` extension):

```json
{
  "mcpServers": {
    "aiops": {
      "command": "/absolute/path/to/Local-AI-Ops/.venv/bin/aiops",
      "args": ["mcp"]
    }
  }
}
```

Replace the absolute path, save, restart Claude Desktop, and inspect connected tools. On Windows, use `.venv\\Scripts\\aiops.exe`.

## Codex CLI / IDE

In `~/.codex/config.toml`:

```toml
[mcp_servers.aiops]
command = "/absolute/path/to/Local-AI-Ops/.venv/bin/aiops"
args = ["mcp"]
```

Check with `codex mcp list`. Codex can also call the CLI directly in an approved shell and follow `AGENTS.md` for tool-routing behavior.

## VS Code MCP (supported IDE clients)

Put `.vscode/mcp.json` in the workspace:

```json
{
  "servers": {
    "aiops": {
      "type": "stdio",
      "command": "/absolute/path/to/Local-AI-Ops/.venv/bin/aiops",
      "args": ["mcp"]
    }
  }
}
```

## ChatGPT web, mobile and remote Claude

A stdio server on your PC is **not a remote URL**. For browser/mobile access, deploy a separate Streamable HTTP MCP endpoint (`https://host.example/mcp`) with **TLS, authentication, per-tool authorization, request limits, and audit logs**, or use a supported secure MCP tunnel. ChatGPT currently allows adding custom MCP servers as plugins where account/workspace permissions allow; Claude supports custom remote MCP connectors in Customize → Connectors.

**Security blocker:** the current `file_to_text(path)` MCP tool reads client-specified local paths. Do not expose this server directly to the public Internet or tunnel it without implementing an explicit allowed-path policy, authentication and tool-scoped permissions. Running `aiops mcp` locally as stdio is the recommended initial mode.

## Tool calling without MCP

OpenAI and Anthropic API agents can invoke the core Python functions through their native tool/function-call loops. Keep a small allowlist of functions and validate the tool arguments before executing them. Example:

```python
from aiops.text.ops import compact, estimate_tokens

ALLOWED = {
    "compact_text": lambda a: compact(a["text"], min(max(a.get("max_tokens", 1000), 1), 4000)),
    "count_tokens": lambda a: estimate_tokens(a["text"]),
}

def dispatch(tool_name: str, arguments: dict):
    if tool_name not in ALLOWED:
        raise ValueError("Unknown tool")
    return ALLOWED[tool_name](arguments)
```

Native function calling still consumes API tokens for the model's decisions and summaries, but not for the mechanical work executed by Python. Cache deterministic outputs and send back a short result, not a full raw dataset.

## Other useful integrations

- **Python-first batch pipelines:** import `aiops.text.ops` and `aiops.jobs.pipeline` to run filtering, dedupe and scoring before involving an LLM.
- **Shell/CLI tool use:** Claude Code, Codex and local developer agents can call `aiops docs totext`, `aiops jobs run` and `aiops yt chapters` with no MCP dependency.
- **Automation and CI:** use cron, Task Scheduler, GitHub Actions or n8n to generate compact report files on a schedule; AI reads only the final shortlist.
- **Skills and instructions:** put predictable workflows in `AGENTS.md` and `CLAUDE.md`. These are guidance, not executable tools or a replacement for MCP.
- **REST/OpenAPI:** only needed for legacy GPT Actions, generic HTTP clients and webhooks. Prefer a thin authenticated adapter over the same Python core, not another copy of the business logic.
- **OAuth-secured remote MCP:** suitable when you want one service for ChatGPT and Claude across devices. Run expensive tasks as jobs and return compact job IDs/results.

## Token-saving operating rules

1. Check whether a task is deterministic (parse/filter/convert/diff/score), then use Python.
2. For ambiguous language extraction, call Ollama with structured output; cache by input hash and model settings.
3. Escalate novel reasoning, architecture and complex debugging to ChatGPT/Claude.
4. Bound tool-result size; return IDs, ranks, evidence and short text, not bulk raw inputs.
5. Keep source text and model results untrusted; never treat GitHub issues, PDFs or job posts as tool-use instructions.

Reference documentation:
- https://developers.openai.com/api/docs/guides/custom-mcp-server
- https://developers.openai.com/learn/docs-mcp
- https://support.claude.com/en/articles/11176164-use-connectors-to-extend-claude-s-capabilities
- https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop
- https://py.sdk.modelcontextprotocol.io/
