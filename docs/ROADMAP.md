# Roadmap: improvement plan and future direction

**Updated:** 2026-11-23 · **Branch policy:** commit directly to `main` unless a branch/PR is explicitly requested.  
**Canonical task tracker:** [GitHub issues](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues). This file is the plan and index; issue state (including each issue's *Depends on* line) is the source of truth.

## 1. Vision

**Today:** nine tools behind one registry (text, docs, YouTube chapters, jobs, KB routing, cached local LLM), reachable from the CLI, local MCP stdio and exported OpenAI/Anthropic function-call schemas.

**Target:** a **local-first context gateway**. Agents call it *before* spending paid tokens:

```text
raw input ──> extract ──> compact / page ──> route (rules → local model → paid model, explicit)
                                │                    │
                                └── cache ───────────┴──> measured usage report
```

| Pillar | Means in practice |
|---|---|
| **One tool, every door** | A function declared once in the registry drives CLI, MCP (stdio, later HTTP) and function-call JSON. REST only if [#12](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/12) shows a real gap. |
| **Trustworthy** | Rule-based tools are byte-deterministic. LLM tools are *cache replays*; temperature 0 does not make a model deterministic. |
| **Safe** | Every call, from every adapter, goes through `dispatch` (validation, limits, policy). File access only inside allowed folders. |
| **Measured** | `aiops stats` reports calls, hit rate and *estimated* savings. No dollar claims without measured usage. |

**Non-goals** (scope control, unchanged): no plugin platform, IDE, orchestrator, custom MCP protocol, OAuth implementation, GitHub/Notion/Google client, hosted GPU stack. Anything with recurring hosting cost or that exposes the home machine needs separate approval.

## 2. Audit of the current code (2026-11-23)

Strengths: ~1.8k lines in `aiops/`, 40 offline tests passing, registry with strict type-checked `dispatch`, remote-deny check inside `dispatch`, clear reuse policy.

### Security and correctness

| # | Gap | Evidence | Issue |
|---|---|---|---|
| G1 | **MCP bypasses `dispatch`**: raw functions are registered, so strict type checks, remote deny and future limits never apply to MCP calls | `aiops/mcp_server.py:15` | #2, #3 |
| G2 | **Arbitrary local file reads** for any MCP client: `file_to_text(path)`, and `job_check(config_path)` → CV/CSV paths in that config | `aiops/tool_catalog.py:7,36`; `aiops/jobs/score.py:46` | #7 |
| G3 | `max_tokens` unchecked: `0` disables the budget, negative values slice from the end | `aiops/text/ops.py:39,65` | #3 |
| G4 | `dispatch` has no output cap or timeout and raises raw Python errors; Ollama down → raw `URLError`, bad schema JSON → raw `JSONDecodeError` | `aiops/registry.py:128`; `aiops/core/llm.py:47-48` | #3 |
| G5 | `job_check` is tier `read` but can call an LLM when the config enables Ollama, and skips the skip-company/IND lists, so MCP verdicts differ from `aiops jobs run` | `aiops/tool_catalog.py:36-48`; `aiops/jobs/pipeline.py:28-30,50-55` | #2, #8 |
| G6 | `html_to_text` drops everything inside `<form>`/`<header>`; pages wrapped in a `<form>` return empty text | `aiops/docs/extract.py:15,26-28` | [#23](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/23) |

### Caching and determinism

| # | Gap | Evidence | Issue |
|---|---|---|---|
| G7 | No registry tool is cached; only `llm.local`/`llm.claude` are. `@cached` is defined but unused | `aiops/core/cache.py:72` | #5 |
| G8 | LLM cache key has model *name*, not digest, and omits `OLLAMA_HOST`; `use_cache=False` still writes | `aiops/core/llm.py:44-49` | #5 |
| G9 | `stable_hash(default=str)` makes sets hash-seed dependent; `f(1)` and `f(x=1)` get different keys; `@cached` never stores `None` and ignores tool version | `aiops/core/cache.py:24,78-84` | #5 (before `@cached` is used) |
| G10 | Non-deterministic inputs: `kb_validate` uses today's date when `as_of` is missing; `job_check` reads `config.yaml` from the working directory | `aiops/kb.py:113`; `aiops/tool_catalog.py:37` | #2 |
| G11 | Dead duplicate cache: `Store.cached`, `llm_cache` table, unused `store` argument; config `ollama.host` ignored | `aiops/jobs/store.py:18,65-75`; `aiops/jobs/extract.py:33-35` | [#24](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/24) |

### Process, tests and docs

| # | Gap | Evidence | Issue |
|---|---|---|---|
| G12 | CI runs only on KB/registry-catalog paths, Python 3.11 only; changes to `registry.py`, `core/`, `text/`, `docs/`, `jobs/`, `youtube/`, `pyproject.toml` never trigger it | `.github/workflows/kb-validation.yml` | #4 |
| G13 | No tests for `mcp_server.build()`, `llm` (mocked), CLI `llm`/`yt` paths | `tests/` | #2, #4 |
| G14 | CLI is hand-written; `aiops docs totext` does not compact by default while MCP `file_to_text` compacts to 4,000 tokens | `aiops/cli.py:81-82` | #2 |
| G15 | Docs drift: "seven tools" (actual nine) in `REUSE_POLICY.md:28`, `RESEARCH_EXTENSIONS.md:14`; `CLAUDE.md` step 6 and `README.md` say to add MCP tools by hand in `mcp_server.py`; README sections after *License* | see files | [#25](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/25) |
| G16 | 17 roadmap issues open, none closed; plans grow faster than code | issues #2–#18 | rule 1 below |
| G17 | Version `0.2.0`, no CHANGELOG; `mypy --strict` on `aiops/core` + `registry.py` reports 11 errors; no `ruff`/`pytest-cov` in `dev` extra | `pyproject.toml` | #4 |

## 3. Working rules

1. **Ship before planning.** No new research or plan documents until v0.3 is tagged. New ideas become GitHub issues (label `enhancement`), not docs.
2. **WIP limit of two** roadmap issues in progress.
3. **Done** = code + test + CLI/MCP exposure through the registry + README row + issue closed with acceptance evidence.
4. **Reuse-first:** check installed connectors, `gh`, official SDKs and existing modules before writing code ([REUSE_POLICY.md](REUSE_POLICY.md)); record the gap in the issue.
5. **Security:** remote tiers deny by default; no unrestricted file reads, write/admin access, silent API billing, raw sensitive logs or credentials in the repo.
6. **Determinism:** rule-based transforms need golden tests; LLM results are cached replays keyed by model identity.
7. **Observability:** report output size, *estimated* tokens saved, latency and error rate; never promise dollar savings without measured prices and usage.
8. **Release checkpoints:** offline tests and static checks on CI; written manual smoke-test results for clients not covered by CI.

## 4. Release plan

Order follows each issue's *Depends on* line.

### v0.3: trustworthy, safe core (next)

| Order | Issue | Pri | Scope | Done when |
|---|---|---|---|---|
| 1 | [#2](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/2) Registry contracts | P0 | MCP registers wrappers that call `dispatch` (G1); existing CLI commands generated from or checked against the registry (G14), not a parallel `aiops tool` CLI; `job_check` tier/lists fixed (G5); explicit `as_of`/`config_path` handling (G10); MCP startup smoke test | Nine-tool parity across CLI, MCP and exports; MCP rejects wrong types the same way `dispatch` does |
| 2 | [#3](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/3) Bounded dispatch | P0 | `max_tokens >= 1` (G3); input/output size caps; structured `{"error": {code, message, hint}}` incl. `OLLAMA_DOWN`, `INVALID_JSON` (G4). Timeouts only for network calls in v0.3; killable timeouts for PDF/Whisper need a subprocess and move to a follow-up | No tool executes after failed validation, via CLI, MCP or `dispatch` |
| 3 | [#4](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/4) CI + golden tests | P0 | Run on every push/PR; Python 3.10–3.13 matrix; package build + install smoke test; `tests/golden/`; record coverage baseline (no target yet); add `ruff`, `pytest-cov` to `dev` | Clean checkout green; golden change without version bump fails |
| 4 | [#7](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/7) File sandbox (local part) | P0 | Pulled forward from v0.4: `AIOPS_ALLOWED_DIRS` for `file_to_text` and `job_check` paths (G2); `..`/symlink escape tests | Paths outside allowed folders denied for every local client |
| 5 | [#5](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/5) Cache correctness | P1 | Canonical arg hashing (G9); LLM key = model digest + host (G8); honour `use_cache=False`; tool version + content hash for any tool that becomes cached (G7); `aiops cache stats` | Edited file or changed model never replays a stale result |
| 6 | [#6](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/6) Telemetry | P1 | SQLite call log (tool, ms, hit, chars in/out; never content); `aiops stats` | Baseline numbers available for section 6 |

Release gate: tag `v0.3.0` with a CHANGELOG; CLI/MCP behaviour compatible except documented safety fixes; no sensitive input logged.

### v0.4: safe remote access

| Order | Issue | Pri | Done when |
|---|---|---|---|
| 7 | [#8](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/8) Auth, scopes, limits | P0 | Unauthorized clients denied; per-token rate limit; read/llm tiers only remotely |
| 8 | [#9](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/9) Streamable HTTP MCP | P0 | Official SDK; remote client lists and calls only allowed tools |
| 9 | [#10](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/10) Deployment checklist | P1 | TLS, secret handling, rollback, verified client steps |

Release gate: never expose unauthenticated local-file tools; remote tools deny by default; no tunnel URLs or real tokens in Git.

### v0.5: portability

| Order | Issue | Pri | Done when |
|---|---|---|---|
| 10 | [#11](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/11) Function-call executor | P1 | Bounded offline tool-loop tests for both API formats via `dispatch` |
| 11 | [#13](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/13) Skills + `aiops doctor` | P1 | Validates dependencies, local server startup, optional Ollama health and client config templates |
| 12 | [#12](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/12) REST/OpenAPI | P2 | Only if a confirmed client cannot use MCP; otherwise closed as not planned |

### v0.6: measurable savings on real work

| Order | Issue | Pri | Done when |
|---|---|---|---|
| 13 | [#17](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/17) Context packs | P1 | Bounded, reproducible pack via existing indexers (can start after v0.3) |
| 14 | [#18](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/18) Agent handoff | P1 | Create/resume across two agents with commit verification (can start after v0.3) |
| 15 | [#14](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/14) Rules-first routing | P1 | Local eval fixtures decide escalation; no hidden paid calls |
| 16 | [#15](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/15) Batch issue triage | P1 | Incremental compact reports via existing GitHub tooling |
| 17 | [#16](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/16) PC-off fallback | P2 | Only with demonstrated need and approved cost |

Release gate: reproducible size reduction on privacy-safe fixtures **reported together with accuracy trade-offs** and model-use assumptions.

### v1.0 candidates (each needs an issue before work starts)

- Stable tool schema + error contract under semver.
- Paged results (`next_cursor`) for text tools.
- Published savings benchmark (size *and* quality) on fixtures.
- Docs tables generated from the registry (fixes G15 permanently).
- PyPI release under a free distribution name such as `local-ai-ops` (`aiops` is taken on PyPI); import name stays `aiops`.

**Not planned:** third-party tool-pack plugin system (conflicts with scope control).

## 5. Dependencies (from issue bodies)

```text
#2 ──> #3 ──> #4 ──> #7 ──> #8 ──> #9 ──> #10
        │      │      ▲                 │
        │      └──────┘ (#7 needs #2,#3,#4)
        └──> #5 ──> #6
#2,#3,#4 ──> #11          #2,#4,#9 ──> #13
#8,#9,#11 ──> #12         #6,#11,#13 ──> #14 ──> #15 (also #5,#6)
#9,#10,#14 ──> #16        #2,#3,#4 ──> #17      #2,#4 ──> #18 (integrates #13)
```

Critical path to remote access: #2 → #3 → #4 → #7 → #8 → #9 → #10. #5/#6 run in parallel after #3. #17/#18 can start once v0.3 is out.

**Candidate screening** (no duplicate issues): agent hooks and config inventory → #13; affected-test selection → #4; model evals → #14; token accounting → #6; secret scanning → #7/#8. Background: [RESEARCH_EXTENSIONS.md](RESEARCH_EXTENSIONS.md).

## 6. Success metrics (baseline first)

Targets are set **after** v0.3 produces baselines, never before.

| Metric | v0.3 | Later |
|---|---|---|
| Roadmap issues closed with acceptance evidence | #2, #3, #4, #5, #6 and local #7 | count conditional #12/#16 only if implemented |
| Coverage of `aiops/core`, `registry` | baseline recorded | target set from baseline |
| Rule-based tool latency (p95, from `aiops stats`) | baseline recorded | < 200 ms for text tools; PDF/Whisper reported separately |
| Cache hit rate (LLM paths) | baseline recorded | target set from a month of use |
| Size reduction on fixtures | — | reported with an accuracy check, never alone |

## 7. Immediate next actions

1. #2: route MCP through `dispatch` (G1) and add an MCP smoke test.
2. #3: validate `max_tokens` and return structured errors (G3, G4).
3. Fix [#23](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/23) (HTML `<form>` bug) and [#24](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/24) (dead cache cleanup).
4. Widen CI triggers to all paths (cheap first step of #4).

System design: [ARCHITECTURE.md](ARCHITECTURE.md).
