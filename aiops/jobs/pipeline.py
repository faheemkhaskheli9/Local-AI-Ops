"""Run every deterministic step over new jobs in the store."""
from __future__ import annotations

from .cv_select import pick_cv
from .filters import apply_filters, load_names
from .models import Job
from .score import fit_score
from .store import Store


def load_skip_companies(cfg: dict) -> set[str]:
    """Companies marked Skip or Applied in your target-companies CSV."""
    import csv
    from pathlib import Path

    from .filters import norm_company

    path = cfg["filters"].get("target_companies_csv")
    if not path or not Path(path).exists():
        return set()
    with open(path, encoding="utf-8-sig") as f:
        return {
            norm_company(r["company"]) for r in csv.DictReader(f)
            if r.get("company") and (r.get("status") or "").lower() in {"skip", "applied"}
        }


def process(job: Job, cfg: dict, store: Store | None = None,
            skip: set[str] | None = None, sponsors: set[str] | None = None) -> Job:
    apply_filters(job, cfg, skip_companies=skip, ind_sponsors=sponsors)
    if job.status == "filtered_out":
        return job

    job.cv_version, hits = pick_cv(job.text, cfg["cv_versions"])
    job.flags["cv_hits"] = hits  # type: ignore[assignment]

    s = fit_score(job.text, cfg, job.cv_version)
    job.score = s["total"]
    job.flags["matched_skills"] = s["matched"]  # type: ignore[assignment]

    if cfg["ollama"]["enabled"] and job.description:
        from .extract import extract

        job.extracted = extract(job.description, cfg, store)

    job.status = "shortlist" if job.score >= cfg["scoring"]["threshold"] else "low_fit"
    return job


def run(store: Store, cfg: dict) -> dict[str, int]:
    skip = load_skip_companies(cfg)
    sponsors = load_names(cfg["filters"].get("ind_sponsors_csv"), "name") or None
    counts: dict[str, int] = {}
    for job in store.by_status("new"):
        process(job, cfg, store, skip, sponsors)
        store.save(job)
        counts[job.status] = counts.get(job.status, 0) + 1
    return counts
