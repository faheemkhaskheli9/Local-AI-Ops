# Reuse existing capabilities before creating another tool

**Rule:** Local-AI-Ops is an adapter and automation layer, not a clone of existing plugins.

## Capability decision

1. **Look for an existing first-party or connected provider tool.** Examples: GitHub repository/issue/PR actions, Gmail email, Google Calendar events, Google Drive/Docs/Sheets, Notion databases, Indeed job searches. Prefer the provider's supported APIs, app/connector tools and permissions.
2. **Use an existing Python implementation** in this project when it provides a local, offline or deterministic capability. The shared registry wraps that function; it does not duplicate it.
3. **Use an existing open-source library** for established parsing and inference tasks (pypdf, python-docx, Whisper/faster-whisper, Ollama, MCP SDK). Do not recreate protocol clients or parsers.
4. **Write a new function only for a genuine gap**: specialized data transformations, local-only processing, offline caching, custom scoring, validation or cross-service orchestration. Document why the existing capability is insufficient.
5. **Never automatically replicate a user's connected account.** Keep OAuth/token handling in the appropriate provider tool or connector when possible.

## Separation of responsibilities

| Work | Existing owner | Local-AI-Ops adds |
| --- | --- | --- |
| GitHub commits, issues, PRs, source | GitHub plugin / GitHub API / `gh` CLI | Offline reports, scoring, dedupe, compact issue summaries |
| Gmail and calendar | Gmail and Google Calendar plugins | Optional local formatting and task summaries |
| Notion pages and databases | Notion plugin / Notion API | Existing job shortlist adapter only when needed |
| Job discovery | Existing job search plugins / authorized sources | Local visa/language matching and CV selection |
| PDF/DOCX extraction | pypdf, python-docx | Text trimming, dedupe, bounded result sizes |
| Video transcription | faster-whisper | Subtitle and chapter workflows |
| LLM inference | Ollama / OpenAI / Anthropic | Routing and cache; do not reimplement models |
| MCP communications | Official MCP Python SDK | Thin registration, not a custom protocol stack |

## Registry scope

- `aiops.tool_catalog` wraps the seven **pre-existing MCP operations**; `aiops.registry` validates arguments and provides OpenAI/Anthropic schemas.
- Local tools are `remote=False` by default. No remote server or public file access is enabled.
- `aiops.export` emits tool definitions for an agent's own function-calling executor; it does **not** connect or install a provider plugin.
- A tool proposal must state its existing alternative, the missing capability and why a wrapper cannot solve it.
- Prefer using platform connector discovery at runtime; installed plugins vary by user/workspace and are not hard-coded by this project.

## Before adding a feature

Check: does the provider connector already do this, can a script invoke the existing module, is there a stable library/API, and does it genuinely reduce cloud-model work? If all answers are yes, reuse instead of building.
