"""Fit scoring: keyword overlap (always) + optional embedding similarity.

Both parts are deterministic: the same job and CV always get the same score.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path


def keyword_score(text: str, skills: list[str]) -> tuple[float, list[str]]:
    """Share of the job's mentioned skills that you have.

    We look at which of *your* skills the post mentions. A post that
    mentions many of them scores high. Returns (score 0-1, matched skills).
    """
    t = text.lower()
    matched = sorted(
        s for s in skills if re.search(rf"(?<![a-z]){re.escape(s.lower())}(?![a-z])", t)
    )
    # Saturate at 8 matches: a post listing 8+ of your skills is a strong fit.
    return min(len(matched) / 8.0, 1.0), matched


@lru_cache(maxsize=2)
def _model(name: str):
    from sentence_transformers import SentenceTransformer  # optional dependency

    return SentenceTransformer(name)


def embedding_score(text: str, cv_text: str, model_name: str) -> float:
    model = _model(model_name)
    a, b = model.encode([text, cv_text], normalize_embeddings=True)
    sim = float((a * b).sum())
    # Map typical cosine range [0.3, 0.9] to [0, 1].
    return max(0.0, min(1.0, (sim - 0.3) / 0.6))


def fit_score(text: str, cfg: dict, cv_version: str | None = None) -> dict:
    s = cfg["scoring"]
    kw, matched = keyword_score(text, cfg["skills"])
    result = {"keyword": round(kw, 3), "matched": matched, "embedding": None}

    cv_path = s.get("cv_text_files", {}).get(cv_version or "")
    if s.get("embedding_model") and cv_path and Path(cv_path).exists():
        cv_text = Path(cv_path).read_text(encoding="utf-8")
        emb = embedding_score(text, cv_text, s["embedding_model"])
        result["embedding"] = round(emb, 3)
        total = s["keyword_weight"] * kw + s["embedding_weight"] * emb
    else:
        total = kw
    result["total"] = round(total, 3)
    return result
