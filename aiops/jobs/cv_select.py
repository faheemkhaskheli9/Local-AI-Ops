"""Pick a CV version by counting keyword hits. Deterministic tie-breaking."""
from __future__ import annotations

import re


def count_hits(text: str, keywords: list[str]) -> int:
    t = text.lower()
    return sum(len(re.findall(rf"\b{re.escape(k.lower())}\b", t)) for k in keywords)


def pick_cv(text: str, cv_cfg: dict) -> tuple[str, dict[str, int]]:
    """Return (version, hit_counts).

    Every key in cv_cfg except 'default' and 'min_hits' is a version name
    mapped to its keyword list. Highest count wins; ties resolve to the
    default version so the result never depends on dict order.
    """
    versions = {k: v for k, v in cv_cfg.items() if k not in ("default", "min_hits")}
    hits = {name: count_hits(text, kws) for name, kws in versions.items()}
    best = max(hits.values(), default=0)
    winners = sorted(n for n, h in hits.items() if h == best)
    if best < cv_cfg.get("min_hits", 1) or len(winners) != 1:
        return cv_cfg.get("default", "general"), hits
    return winners[0], hits
