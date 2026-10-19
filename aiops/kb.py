"""Offline knowledge-base routing and evidence validation.

This module does not fetch GitHub data: platform connectors or the user's
authorized GitHub CLI perform retrieval. Returned plans are not evidence.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
import re
from pathlib import Path


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    instructions: tuple[str, ...]
    index: str
    terms: tuple[str, ...]
    stale_after_days: int
    private: bool = False

    @property
    def repository(self) -> str:
        return f"faheemkhaskheli9/{self.name}"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repository}"


SOURCES = (
    Source("ai", "AI-Knowledge-Base", ("AGENTS.md",), "INDEX.md", (
        "ai", "ml", "machine learning", "deep learning", "llm", "llms",
        "rag", "agent", "agents", "mcp", "embedding", "vector",
        "pytorch", "transformer", "computer vision", "fine tuning",
        "finetuning", "model inference", "speech recognition",
        "model evaluation", "ai model"), 90),
    Source("engineering", "Software-Engineering-KnowledgeBase",
           ("AGENTS.md",), "INDEX.md", (
        "software", "python", "fastapi", "api", "database", "system design",
        "architecture", "distributed", "scaling", "caching", "deployment",
        "devops", "ci/cd", "docker", "kubernetes", "testing",
        "observability", "microservice", "backend", "reliability"), 180),
    Source("security", "Cyber-Security-Knowledge-Base",
           ("README.md", "CLAUDE.md"), "README.md", (
        "security", "cyber", "owasp", "vulnerability", "cve",
        "secure", "threat", "injection", "malware", "incident response",
        "authentication", "authorization", "secrets", "hardening",
        "pentest", "privacy", "sast", "soc"), 90),
    Source("medical", "Medical-Knowledge-Base",
           ("AGENTS.md",), "KB-INDEX.md", (
        "medical", "clinical", "medicine", "patient", "hospital",
        "healthcare", "drug", "medication", "diagnosis", "treatment",
        "symptoms", "triage", "oncology", "clinical trial"), 30),
    Source("personal", "Personal-Knowledge-Base",
           ("AGENTS.md", "CONTEXT.md"), "INDEX.md", (
        "my cv", "my resume", "my career", "my work history",
        "my projects", "my portfolio", "my preferences",
        "my job applications", "my profile"), 180, True),
)
_BY_REPOSITORY = {source.repository: source for source in SOURCES}


def _match(task: str, term: str) -> bool:
    # Boundaries stop "ai" matching "email" or "agent" matching "agency".
    return re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)",
                     task.lower()) is not None


def route(task: str, include_private: bool = False) -> dict:
    """Return deterministic GitHub retrieval instructions; never fetch files."""
    if not isinstance(task, str) or not task.strip():
        raise ValueError("Task must be nonempty text")
    routes = []
    withheld_private = False
    for source in SOURCES:
        matched = [term for term in source.terms if _match(task, term)]
        if not matched:
            continue
        if source.private and not include_private:
            withheld_private = True
            continue
        routes.append({
            "id": source.id, "repository": source.repository,
            "url": source.url, "private": source.private,
            "instructions": list(source.instructions), "index": source.index,
            "matched_terms": matched, "stale_after_days": source.stale_after_days,
        })
    return {
        "routes": routes,
        "private_access_required": withheld_private,
        "retrieval_performed": False,
        "next_step": "Fetch the selected indexes and matched full topics using "
                     "the existing authorized GitHub connector or CLI; cite files "
                     "actually read and verify time-sensitive claims independently.",
    }


def validate(task: str, evidence: list[dict], *, include_private: bool = False,
             as_of: str | None = None) -> dict:
    """Check self-reported retrieval metadata. Cannot independently prove access.

    Evidence items: {repository, path, retrieved: true, last_verified?: YYYY-MM-DD}.
    Index/AGENTS-only evidence is insufficient; include one relevant full topic
    per selected repository. Date-free references produce a freshness warning.
    """
    if not isinstance(evidence, list):
        raise TypeError("Evidence must be a list of objects")
    today = date.fromisoformat(as_of) if as_of else date.today()
    planned = route(task, include_private=include_private)
    expected = {entry["repository"]: entry for entry in planned["routes"]}
    found: set[str] = set()
    issues: list[str] = []
    warnings: list[str] = []
    accepted: list[str] = []

    for i, ref in enumerate(evidence):
        if not isinstance(ref, dict):
            issues.append(f"evidence[{i}] must be an object")
            continue
        repository, path = ref.get("repository"), ref.get("path")
        if not isinstance(repository, str) or repository not in expected:
            issues.append(f"evidence[{i}] is not an authorized selected repository")
            continue
        if not isinstance(path, str) or not path.endswith(".md") or (
            path.startswith("/") or "\\" in path or
            any(part in ("", ".", "..") for part in path.split("/"))
        ):
            issues.append(f"evidence[{i}] has an unsafe or invalid Markdown path")
            continue
        if ref.get("retrieved") is not True:
            issues.append(f"evidence[{i}] is not marked retrieved in this session")
            continue
        source = _BY_REPOSITORY[repository]
        accepted.append(f"{source.url}/blob/HEAD/{path}")
        if path not in (*source.instructions, source.index):
            found.add(repository)
        checked = ref.get("last_verified")
        if checked is None:
            warnings.append(f"{repository}/{path}: source freshness not supplied")
        else:
            try:
                verified = date.fromisoformat(checked)
                if verified > today:
                    issues.append(f"{repository}/{path}: future verification date")
                elif (today - verified).days > source.stale_after_days:
                    warnings.append(f"{repository}/{path}: verify outdated facts")
            except (TypeError, ValueError):
                issues.append(f"{repository}/{path}: invalid last_verified date")

    missing = sorted(set(expected) - found)
    for repository in missing:
        issues.append(f"{repository}: no full topic file retrieved")
    if planned["private_access_required"]:
        warnings.append("Personal KB not selected without explicit private opt-in")
    return {
        "ok": not issues and bool(expected),
        "selected": list(expected),
        "missing": missing,
        "issues": issues,
        "warnings": warnings,
        "candidate_citations": accepted,
        "verified_retrieval": False,
        "note": "Local validation checks supplied metadata, not GitHub access, "
                "document accuracy, or the validity of user-provided claims.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline KB router and evidence audit")
    subs = parser.add_subparsers(dest="action", required=True)
    plan = subs.add_parser("plan")
    plan.add_argument("task")
    plan.add_argument("--private", action="store_true",
                      help="Opt in to selecting private Personal KB")
    check = subs.add_parser("validate")
    check.add_argument("task")
    check.add_argument("evidence_file", help="JSON list of retrieved file metadata")
    check.add_argument("--private", action="store_true")
    check.add_argument("--as-of", help="Date YYYY-MM-DD for reproducible checks")
    args = parser.parse_args(argv)
    if args.action == "plan":
        result = route(args.task, include_private=args.private)
    else:
        evidence = json.loads(Path(args.evidence_file).read_text(encoding="utf-8"))
        result = validate(args.task, evidence, include_private=args.private,
                          as_of=args.as_of)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if args.action == "plan" or result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
