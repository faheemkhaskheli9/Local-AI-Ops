# Delivery roadmap (v0.3–v0.6)

**Updated:** 2026-10-09 · **Branch policy:** commit directly to `main`; do not create branches/PRs unless explicitly requested.  
**Canonical task tracker:** [GitHub issues](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues). This document is the **release plan and index**, not a second backlog. Issue state is the source of truth for actual progress.

## Current baseline (already exists; do not rebuild)

- Deterministic text/document helpers, job screening, YouTube chapter utilities and cached Ollama integration.
- Seven MCP stdio tools exposed from existing Python implementations.
- Shared `aiops.registry` / `aiops.tool_catalog`, argument dispatch, and `aiops.export` OpenAI/Anthropic function-call schema exports.
- `docs/ARCHITECTURE.md`, `docs/INTEGRATIONS.md`, `docs/REUSE_POLICY.md`, `AGENTS.md`.
- Tests exist, but clean-install CI, end-to-end MCP compatibility, hardened remote security and measured token savings are **not yet verified**.

**Do not build a second GitHub, Notion, Google, jobs, Ollama, or MCP provider implementation.** Use installed platform plugins/official APIs/CLI and existing Python modules. Every new feature should identify an actual gap, alternatives considered, and acceptance tests.

## Release plan and prioritized issues

### v0.3 — Reliability and measurement (first)

| Order | Issue | Priority | Definition of done |
| --- | --- | --- | --- |
| 1 | [#2 Registry contracts + MCP SDK compatibility](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/2) | P0 | Seven-tool parity and MCP startup smoke tests |
| 2 | [#3 Bounded dispatch + structured errors](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/3) | P0 | Invalid/oversized calls rejected before execution |
| 3 | [#4 Golden tests + GitHub Actions CI](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/4) | P0 | Clean checkout validates tests and package |
| 4 | [#5 File/model-aware cache invalidation](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/5) | P1 | Edited files and model changes never serve stale results |
| 5 | [#6 Usage telemetry and token baseline](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/6) | P1 | Privacy-safe hit rate, latency and *estimated* savings |

Release gate: `pytest` and package smoke tests pass on CI; existing CLI/MCP behavior remains compatible; schemas are stable; no sensitive input is logged. **Already implemented registry/export code is hardening work, not a new rewrite.**

### v0.4 — Secure remote MCP (after safety gates)

| Order | Issue | Priority | Definition of done |
| --- | --- | --- | --- |
| 6 | [#7 Filesystem sandbox + remote allowlist](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/7) | P0 | Traversal/symlink escapes blocked; explicit tool opt-in |
| 7 | [#8 Authentication, scopes, limits](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/8) | P0 | Unauthorized clients denied; auth method matches client |
| 8 | [#9 Official Streamable HTTP MCP adapter](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/9) | P0 | Remote discovery/call works with official MCP SDK |
| 9 | [#10 Secure deployment + client smoke checklist](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/10) | P1 | TLS, secret handling, rollback and verified client steps |

Release gate: never expose unauthenticated local-file tools; all remote tools deny by default; a remotely connected test client can call only authorized read-only capabilities. No publishing tunnel URLs or real tokens in Git.

### v0.5 — Client portability without adapter duplication

| Order | Issue | Priority | Definition of done |
| --- | --- | --- | --- |
| 10 | [#11 Native OpenAI/Anthropic function-call executor](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/11) | P1 | Shared registry dispatch; bounded offline loop tests |
| 11 | [#13 Portable skills + setup/doctor checks](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/13) | P1 | Client config templates validated, no copied business logic |
| 12 | [#12 Conditional REST/OpenAPI evaluation](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/12) | P2 | Implement only if a confirmed client gap requires it |

Release gate: one Python implementation serves supported agent surfaces, without duplicate provider clients. REST/OpenAPI remains optional; prefer MCP when supported.

### v0.6 — Real workload optimization

| Order | Issue | Priority | Definition of done |
| --- | --- | --- | --- |
| 13 | [#14 Rules-first routing and explicit escalation](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/14) | P1 | Local/deterministic first, no hidden paid calls |
| 14 | [#15 GitHub issue batch triage + dedupe](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/15) | P1 | Incremental compact reports via existing GitHub tools |
| 15 | [#16 Conditional PC-off fallback evaluation](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/16) | P2 | Activate only with demonstrated need and approved costs |

Release gate: demonstrate reproducible size/cost reduction on real-like, privacy-safe fixtures; report accuracy tradeoffs and model-use assumptions. Customer/customer-account connectors stay owned by provider apps.

## Dependencies and parallelization

```text
#2 Registry compatibility ──> #3 Safe dispatch ────────> #7 File sandbox
           │                   │                       │
           └──────> #4 CI      ├──────> #5 Cache        └──> #8 Auth ──> #9 HTTP MCP ──> #10 Deployment
                               └──────> #6 Telemetry
           #3 + #4 ──> #11 Native function calling ──> #13 Skills/doctor
           #9 + #11 ──> #12 Optional REST/OpenAPI decision
           #6 + #11 + #13 ──> #14 Router ──> #15 Batch triage
           #9 + #10 + #14 ──> #16 Optional PC-off fallback
```

The critical path to **ChatGPT/Claude remote access** is #2 → #3 → #4 and #7 → #8 → #9 → #10. Cache/stats work (#5/#6) can progress in parallel after safety contracts stabilize.

## Quality and review rules

1. **Reuse-first:** check installed plugins, GitHub/Notion/Google/Indeed service tools, `gh`, official SDKs, existing Python modules and open-source libraries before adding code. Record the gap in the issue/commit.
2. **One logical change per commit directly to `main`.** Keep issues up to date and close only after acceptance criteria pass.
3. **Security:** remote tiers deny by default; no unrestricted file reads, write/admin access, silent API billing, raw sensitive logs, or credentials in the repo.
4. **Determinism:** rule-based transforms need stable tests; temperature-zero LLM output itself is *not* guaranteed deterministic. Distinguish cache replay and model identity.
5. **Observability:** output size, estimated tokens saved, actual API usage when available, latency and error rates. Do not promise dollar savings without measured prices/usage.
6. **Release checkpoints:** run offline tests, static checks, and integration tests relevant to the affected adapter. Write explicit manual smoke-test results for clients not covered in CI.

## Scope control

Do **not** add an entire alternative plugin platform, IDE, orchestrator, database, hosted GPU stack, OAuth implementation, GitHub/Notion client or custom MCP protocol. Start with official integrations. Features requiring recurring hosting expense, additional cloud billing or exposing the home machine need separate review before activation.

**Next actionable task:** [#2 — Harden registry contracts and MCP compatibility](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/2), then [#3](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/3) and [#4](https://github.com/faheemkhaskheli9/Local-AI-Ops/issues/4).
