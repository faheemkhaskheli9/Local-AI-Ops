# Agent instructions for Local-AI-Ops

Prefer deterministic Python tools over LLM inference whenever practical. This project exposes the same core via `aiops` CLI and `aiops mcp`.

- Use `aiops text compact` or MCP `compact_text` before sending large passages to a model.
- Use `aiops docs totext FILE --max-tokens 1500` / MCP `file_to_text` for PDF, DOCX and HTML extraction.
- Use job-pipeline filters, scoring and CV selection before requesting an LLM to assess the shortlist.
- Use `aiops yt chapters` or MCP `srt_to_chapters` for transcript chapter generation; avoid asking a cloud model to process the entire SRT.
- Route low-risk extraction/classification to cached local Ollama through `aiops llm local` / MCP `local_llm`. Validate schema and review factual claims.
- Reserve cloud models for decisions involving novelty, architectural complexity, serious ambiguity or high stakes.
- Do not read sensitive local files, contact external sites, or run model-generated shell commands without explicit user authorization.
- Do not expose the local stdio MCP server to the public Internet. Its file tool accepts local paths; remote deployment needs authentication and an allowed-path policy.
- Return concise evidence, status, and links; never dump entire raw files or credentials into LLM context.
- Keep changes small and focused; extend existing pure functions instead of duplicating business logic in MCP and CLI.
- Add tests for code changes and run `pytest`. Avoid network, GPU, heavy optional dependencies in core tests.

Integration setup, supported surfaces and security caveats: [docs/INTEGRATIONS.md](docs/INTEGRATIONS.md). For project structure see [CLAUDE.md](CLAUDE.md).

## Reuse first

Before adding a tool or plugin, check [docs/REUSE_POLICY.md](docs/REUSE_POLICY.md). Use installed GitHub, Notion, Gmail, Calendar, Drive and job-search connectors for their existing capabilities. Prefer wrapping an existing Python operation through `aiops.registry` over writing a second implementation. Do not build another MCP protocol implementation or provider client when the official SDK/connector already exists.


## Relevant knowledge bases

For questions involving AI, engineering, security or clinical domains, use the
[portable KB routing skill](skills/knowledge-base-routing/SKILL.md) and
`aiops kb plan "TASK"` to select references. Fetch actual topic files via
the connected GitHub tool: routing output alone is not evidence. Require
explicit authorization for the private Personal KB. Do not claim repo access
without fetching it; validate dynamic medical/security/AI facts with primary
sources. Neither `kb_plan` nor `kb_validate` communicates with GitHub.
