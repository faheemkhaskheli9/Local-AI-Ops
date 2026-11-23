# Roadmap: improvement plan and future direction

**Updated:** 2026-11-23 · **Branch policy:** commit directly to `main` unless a branch/PR is explicitly requested.  
**Canonical task tracker:** [GitHub issues](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues). This file is the plan and index; issue state is the source of truth for progress.

## 1. Vision: what this repo becomes

**Today:** a personal toolbox of nine deterministic Python tools (text, docs, YouTube, jobs, KB routing, cached local LLM) reachable from the CLI, local MCP and exported function-call schemas.

**Target (v1.0):** a **local-first context gateway for AI agents**. Every agent (chat apps, coding agents, API scripts) calls it *before* spending paid tokens:

```text
raw input ──> extract ──> compact / page ──> route (rules → local model → paid model)
                │               │                    │
                └──── content-hash cache ────────────┴──> measured savings report
```

| Pillar | Means in practice |
|---|---|
| **One tool, every door** | A function declared once in the registry appears in CLI, MCP stdio/HTTP and function-call JSON. No hand-written adapters. |
| **Trustworthy** | Golden tests, versioned outputs, content-hash cache keys, structured errors, sandboxed file access. |
| **Measured** | `aiops stats` proves calls avoided, cache hit rate and bytes/tokens saved, instead of claiming them. |
| **Safe remote** | Authenticated, read-only-by-default HTTP MCP so web/mobile clients can use home-PC tools. |
| **Extensible** | Third-party "tool packs" install via Python entry points (`aiops-pack-*`) without editing this repo. |
| **Distributable** | Published on PyPI, `pipx install aiops`, `aiops doctor` verifies a client setup in one command. |

**Non-goals:** a second MCP protocol, provider clients (GitHub, Notion, Google), an agent runtime, multi-tenant SaaS, or hosted GPUs.

## 2. Current state (audit, 2026-11-23)

Strengths: small clean core (~2.2k LOC), 40 offline tests passing, shared registry with type-checked dispatch, remote deny-by-default, clear reuse policy.

Gaps found in the code:

| # | Gap | Where | Fix in |
|---|---|---|---|
| G1 | **Planning outpaces shipping:** ~37 KB of plans vs ~2.2k LOC; 17 roadmap issues open, none closed | `docs/` | Section 3 rules |
| G2 | CLI is still hand-written, so registry tools and CLI commands can drift | `aiops/cli.py` | #2 |
| G3 | `dispatch` has no output cap, no timeout, raises raw Python errors | `aiops/registry.py` | #3 |
| G4 | CI only triggers on KB file paths; no lint, type check or Python-version matrix | `.github/workflows/` | #4 |
| G5 | `@cached` key ignores tool version; `None` results are never cached; `file_to_text` is keyed by path, not content | `aiops/core/cache.py`, `tool_catalog.py` | #5 |
| G6 | Local LLM cache key has model *name*, not model *digest*; Ollama down gives a raw `URLError` | `aiops/core/llm.py` | #5, #3 |
| G7 | No `aiops cache stats` / `aiops stats`; savings are unmeasured | `aiops/cli.py` | #6 |
| G8 | `file_to_text` reads any local path | `tool_catalog.py` | #7 |
| G9 | No tests for `mcp_server.build()`, `llm` (mocked), cache TTL, CLI `llm`/`yt` paths | `tests/` | #2, #4 |
| G10 | Docs drift: "seven" tools in several docs (actual: nine); README sections after *License* | `docs/`, `README.md` | #21 |
| G11 | Still `0.2.0`, no CHANGELOG, not on PyPI | `pyproject.toml` | v1.0 |

## 3. Working rules (to fix G1)

1. **Ship before planning.** No new research/plan documents until v0.3 is released. New ideas go into a GitHub issue labelled `idea`, not a doc.
2. **WIP limit of two:** at most two roadmap issues in progress at once.
3. **Definition of done** = code + test + CLI/MCP exposure + README row + issue closed.
4. **Release every milestone** with a version bump and CHANGELOG entry.
5. Reuse-first and security rules from [REUSE_POLICY.md](REUSE_POLICY.md) still apply.

## 4. Release plan

### v0.3: trustworthy core (next; target ~2–3 weeks)

| Order | Issue | Scope | Done when |
|---|---|---|---|
| 1 | [#4](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/4) CI + golden tests | Run on every push/PR; Python 3.10–3.13 matrix; `ruff` + `mypy --strict` on `aiops/core`, `registry`; `tests/golden/` fixtures | Clean checkout green; golden output change without version bump fails |
| 2 | [#2](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/2) Registry contracts | Generate CLI subcommands for registry tools (`aiops tool <name> --arg`); MCP startup smoke test; schema snapshot test | One declaration drives CLI, MCP and exports |
| 3 | [#3](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/3) Bounded dispatch | Input/output size caps, per-tier timeout, `{"error": {code, message, hint}}`, `OLLAMA_DOWN` code | Invalid, oversized or failing calls return structured errors |
| 4 | [#5](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/5) Cache correctness | Key = tool + version + args + file sha256 + model digest; cache `None` via sentinel; optional TTL column; `aiops cache stats` | Edited file or new model never returns stale output |
| 5 | [#6](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/6) Telemetry | SQLite call log (tool, ms, hit, chars in/out; no content); `aiops stats` | Hit rate and estimated savings visible after one day of use |

Release gate: tag `v0.3.0`, CHANGELOG, docs say "nine tools" (or generate the count).

### v0.4: safe remote access

| Order | Issue | Done when |
|---|---|---|
| 6 | [#7](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/7) File sandbox + allowlist | `AIOPS_ALLOWED_DIRS`; `..`/symlink escapes blocked by tests |
| 7 | [#8](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/8) Auth, scopes, limits | Bearer token, per-token rate limit, read/llm tiers only remotely |
| 8 | [#9](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/9) Streamable HTTP MCP | `aiops serve --http` via official SDK; remote client can list and call allowed tools |
| 9 | [#10](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/10) Deployment checklist | `deploy/` with tunnel + service files; smoke-test log for each web client |

### v0.5: portability and packaging

| Order | Issue | Done when |
|---|---|---|
| 10 | [#13](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/13) Skills + `aiops doctor` | One command validates Python, extras, Ollama, MCP config for each client |
| 11 | [#11](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/11) Function-call executor | Bounded offline tool-loop tests for both API formats via shared `dispatch` |
| 12 | New: tool-pack plugins | `aiops.packs` entry-point group; registry loads external packs; one example pack |
| 13 | New: PyPI release | `pipx install aiops` works; trusted-publishing workflow |
| 14 | [#12](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/12) REST/OpenAPI | Only if a confirmed client cannot use MCP |

### v0.6: measurable token savings on real work

| Order | Issue | Done when |
|---|---|---|
| 15 | [#17](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/17) Task-aware context packs | Bounded, reproducible pack for a repo + issue, reusing existing indexers |
| 16 | [#14](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/14) Rules-first routing | Local eval fixtures decide when the local model is good enough; no hidden paid calls |
| 17 | [#18](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/18) Agent handoff | Create/resume handoff across two agents with commit verification |
| 18 | [#15](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/15) Batch issue triage | Incremental compact reports via existing GitHub tooling |
| 19 | [#16](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/16) PC-off fallback | Only with demonstrated need and approved cost |

### v1.0: stable platform

- Stable tool schema and error contract (semver: breaking schema change = major bump).
- Paged results (`next_cursor`) for every text tool.
- Published benchmark: tokens/bytes saved on privacy-safe fixtures vs. raw input.
- Docs generated from the registry (tool table in README, MCP tool list).
- At least one external tool pack.

## 5. Dependencies

```text
#4 CI ──> #2 Registry ──> #3 Dispatch ──> #5 Cache ──> #6 Stats ─────────────┐
                              │                                                │
                              └──> #7 Sandbox ──> #8 Auth ──> #9 HTTP ──> #10  │
#2 + #3 ──> #11 Executor ──> #13 Doctor ──> packs ──> PyPI                     │
#2 + #4 ──> #17 Context packs                       #6 + #11 ──> #14 Router ──┴──> #15, #16
#2 + #13 ──> #18 Handoff
```

CI (#4) moves first: every later change then lands with a safety net.

## 6. Success metrics

| Metric | v0.3 | v1.0 |
|---|---|---|
| Roadmap issues closed | 5 | 19+ |
| Test coverage (`aiops/core`, `registry`) | ≥ 85 % | ≥ 90 % |
| Rule-based tool latency (p95) | < 200 ms | < 200 ms |
| Cache hit rate on repeated work | measured | ≥ 50 % |
| Estimated input reduction on fixtures | measured | ≥ 70 % |
| Clients verified by `aiops doctor` | 0 | 4+ |

## 7. Immediate next actions

1. Fix CI triggers and add the version matrix + lint (#4).
2. Fix the `@cached` `None`/version bugs and add content-hash keys (#5); small, high value.
3. Generate CLI commands from the registry (#2).
4. Close #19/#20 as `idea` or merge into existing issues to keep the backlog lean.

Research background: [RESEARCH_EXTENSIONS.md](RESEARCH_EXTENSIONS.md). System design: [ARCHITECTURE.md](ARCHITECTURE.md).
