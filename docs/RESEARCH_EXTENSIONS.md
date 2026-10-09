# Research: high-value extensions without duplicating tools

**Reviewed:** 2026-10-09. **Purpose:** find low-maintenance, local-first additions that reduce cloud agent input size and repetitive interaction for multi-repository software, ML, research, and content workflows.

**Status:** evaluated candidates, **not implemented**. Existing [ROADMAP.md](ROADMAP.md) and [GitHub Issues](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues) remain the canonical implementation tracker. This research does not replace that backlog. User preference: commit on `main`, no branches/PRs without explicit request.

## What the repo already does

- `aiops.text`: deterministic cleaning, shortening, token estimates, diffs.
- `aiops.docs`: PDF/DOCX/HTML/CSV/JSON extraction.
- `aiops.jobs`: job discovery/filters/dedupe, score and CV routing.
- `aiops.youtube`: transcription and subtitle-to-chapter operations.
- `aiops.core`: SQLite cached Ollama / Anthropic calls.
- `aiops.registry`, `aiops.tool_catalog`, `aiops.mcp_server`, `aiops.export`: seven existing tool wrappers, local stdio MCP, native provider schemas.
- Existing issues #2–#16 cover contract reliability, bounded dispatch, CI, cache, stats, secure HTTP MCP, native tool calls, packaging, routing, batch triage, optional cloud fallback.

All proposals below must first confirm they cannot be achieved entirely in an installed plugin, SDK, or existing module. Favor thin adapters and pure local composition; don't rebuild provider platforms, repo search engines, or full agent runtimes.

## Ranked candidate matrix

Effort = rough integration-only engineering work for one contributor, **not a validated estimate**. Evidence links identify existing reusable software.

| Rank | Proposed capability and output | Why it matters | Existing solution to reuse | Integration work | Tracker |
| --- | --- | --- | --- | --- | --- |
| **1** | **Task-aware context pack**: constrained `context.md/json` containing relevant symbols, current GitHub issue, changed files, test locations and source links | Large repos repeatedly cost context tokens | [Repomix](https://github.com/yamadashy/repomix), [Aider repository maps](https://aider.chat/docs/repomap.html), [code-symbol-index](https://github.com/hit9/code-symbol-index), git CLI | S–M; no new indexer | **#17 (new)** |
| **2** | **Cross-agent handoff**: portable, sanitized `handoff.json/md` with goal, last verified commit, changed files, tests, blockers, next task | Prevents ChatGPT→Claude→Codex restarts | [Agent Handoff](https://github.com/AniruddhaHumane/handoff), git CLI, existing `AGENTS.md` | S; assess reuse before implementing | **#18 (new)** |
| **3** | **Agent lifecycle hooks**: context at start; run lint/checks after edits; safety gates before risky commands | Removes repeated instructions, keeps behavior deterministic | [Claude Code hooks](https://claude.com/resources/articles/how-to-configure-hooks), native agent/IDE hooks | S–M; thin templates, no hook engine | [#13](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/13) |
| 4 | **Changed-code test selection**: quick affected tests + full CI fallback | Less wasted agent runtime and tool output | [pytest-testmon](https://www.testmon.org/), pytest; relevant ecosystem test selection | S; optional command wrapper | [#4](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/4) |
| 5 | **Local-model eval gate**: use fixed JSON fixtures to compare actual extraction/triage accuracy vs cloud baseline | Avoid cheap-but-wrong decisions | [promptfoo](https://github.com/promptfoo/promptfoo), pytest, Ollama JSON schema support | M; fixtures + thin runner only | [#14](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/14) |
| 6 | **Connected-tool inventory and conflict check**: inspect MCP client configurations; flag equivalent capabilities and excessive schemas | Avoids duplicate plugins/tools and tool-description bloat | [MCP Inspector](https://github.com/modelcontextprotocol/inspector), [official MCP Registry API](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/official-registry-api.md) | M; compare metadata, no new directory | [#13](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/13) |
| 7 | **Structured result slimming**: filter JSON/CLI output by required fields, hard bounds, pagination/cursors, source references | Big tool outputs waste model context or hide evidence | Python stdlib, existing `aiops.text`; use schema-specific safe projections | S–M; improve existing dispatch | [#3](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/3) |
| 8 | **Token/cost accounting and cache-aware prompt assembly**: actual provider usage + estimates + stable prefixes | Makes token savings measurable, not hypothetical | [OpenAI caching guide](https://developers.openai.com/api/docs/guides/prompt-caching), [OpenTelemetry GenAI](https://opentelemetry.io/docs/specs/semconv/), existing SQLite | M; emit metadata but never private prompts by default | [#6](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/6), [#14](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/14) |
| 9 | **Local secret + tool-security preflight**: scan before commits or remote enablement | Prompts/tool results can leak keys or cause unsafe tool use | [TruffleHog](https://github.com/trufflesecurity/trufflehog), [OWASP MCP cheat sheet](https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html) | S–M; opt-in scanner CLI, no scanner rewrite | [#7](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/7), [#8](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/8) |
| 10 | **Research evidence pack**: DOI, title, verified date, claim→source pointers, uncertainties | Academic papers and technical articles need checkable claims | [OpenAlex](https://help.openalex.org/how-to/api-recipes/), [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/), available scholarly plugins | M; only evidence formatting/dedupe; don't build search engine | Candidate after #14 |
| 11 | **ML experiment handoff report**: summarize baseline vs current run, dataset/model identities, result deltas | Reduces repeated reading of metric files | [MLflow Tracking](https://www.mlflow.org/docs/latest/tracking/), [DVC](https://doc.dvc.org/user-guide) | M; adapter to existing run metadata, no MLflow clone | Candidate only when used regularly |
| 12 | **Multi-repository quality digest**: compact, cached tests/deploy failures plus open blocking issues, linked to existing GitHub tasks | Many projects need frequent check-ins | GitHub plugin/`gh` + git; existing issue triage logic | M; summary composition only | [#15](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/15) |

## First two candidate specifications

### A. Task-aware context pack (#17)

Input: a local Git working tree, a local task identifier/issue URL, an explicit character/token budget, optional focus paths. Don't fetch from private external systems without an approved connector.

Output (prefer JSON plus short Markdown):
- `source_repo`, `base_commit`, `task_url`, `changed_paths`, `context_budget`, `approx_tokens`
- `selected_files` with relative path, relevance reason, content hash and line spans
- `issue_summary` from an authorized GitHub source, targeted symbol map and candidate tests
- `excluded_paths` with reason, and a manifest of tool/version/input hashes
- Explicit `truncated` and retrieval pointer fields; keep raw source local.

Workflow: reuse git diff + Repomix `--mcp --sandbox` / CLI, or invoke existing code-symbol-index; **do not implement custom Tree-sitter indexing or repackage an entire repository blindly**. Use a deterministic ranking baseline: task path overlap, changed files, import/symbol match, test-name match; honor `.gitignore`, binary sizes, secrets and token budget. Only add embedding reranking if measured better than rules.

Acceptance: fixtures with a 5–20 file dummy repo show stable selection ordering, bounded output, retained evidence and changed-file invalidation. Compare output size to full repo pack without claiming actual provider token savings until measured.

### B. Portable agent handoff (#18)

Input: current task/issue, clean or dirty git status, last commit, changed paths, test command/outcome, explicit decisions and blockers. Optional agent-provided notes with a field-specific size cap.

Output:
```json
{
  "schema_version": 1,
  "repo": "owner/name",
  "base_commit": "<git-sha>",
  "task_url": "<issue-url-or-null>",
  "changed_files": ["relative/path.py"],
  "last_verification": {"command": "pytest", "status": "passed|failed|not-run"},
  "decisions": [],
  "blockers": [],
  "next_action": "short text",
  "sensitive_content_included": false
}
```
Evaluate Agent Handoff first; only add a thin `aiops handoff` command if it supplies a distinct machine-verifiable feature. Do not automatically ingest or publish Claude/ChatGPT private conversation transcripts. Preserve explicit provenance and verify commit SHA on resume; if source repo has diverged, warn instead of silently reusing obsolete instructions.

Acceptance: create → resume across two client configurations in an offline fixture; no secrets or uncontrolled paths, no inflated summary, and a clear stale-state error. Human judgment remains responsible for whether a handoff's instructions are trustworthy.

## Implementation sequencing

1. **Do the existing safety/reliability work first:** [#2](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/2)–[#4](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/4). These make every later adapter safer.
2. **Small independent local wins:** #17 and #18 can be prototyped after the basic test harness, without a remote MCP gateway.
3. **Integrate, do not multiply tasks:** make native hooks/config inventory part of #13; affected test runner part of #4; model evals part of #14; token accounting part of #6; safety scanners part of #7/#8.
4. **Remote gateway (#7–#10) remains a security-dependent milestone,** not a shortcut for accessing local files.
5. **Later research/ML adapters should be demand gated** and should call existing OpenAlex/Crossref/MLflow/DVC tools when available instead of reinventing them.

## Decision criteria before implementation

For each candidate, record:
- An explicit repeated real workflow and its baseline (LLM turns, context size, latency, manual effort).
- Existing plugin/CLI/SDK tested and why it is not already sufficient.
- Minimal reusable adapter/function boundary and permission model.
- At least one deterministic fixture, a failure case, privacy handling and estimated maintenance risk.
- Actual measurements after shipping: bytes/tokens returned, correctness, extra CPU/disk/time. Avoid equating estimated chars/4 directly with actual billed tokens.
- An exit criterion: if an existing tool completely solves the task, close the candidate as **not planned**.

## Primary sources used

- Repomix MCP + sandbox: https://github.com/yamadashy/repomix
- Aider repo map: https://aider.chat/docs/repomap.html
- Code symbol index: https://github.com/hit9/code-symbol-index
- Agent Handoff: https://github.com/AniruddhaHumane/handoff
- Claude hooks: https://claude.com/resources/articles/how-to-configure-hooks
- pytest-testmon: https://www.testmon.org/
- MCP Inspector: https://github.com/modelcontextprotocol/inspector
- MCP Registry: https://github.com/modelcontextprotocol/registry
- OWASP MCP security: https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html
- Prompt caching: https://developers.openai.com/api/docs/guides/prompt-caching
- OpenTelemetry GenAI: https://opentelemetry.io/docs/specs/semconv/
- TruffleHog: https://github.com/trufflesecurity/trufflehog
- OpenAlex: https://help.openalex.org/how-to/api-recipes/
- Crossref: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- MLflow: https://www.mlflow.org/docs/latest/tracking/
- DVC: https://doc.dvc.org/user-guide

*No prototype or performance benchmark was run as part of this research.*
