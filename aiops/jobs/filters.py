"""Rule-based filters. Same input -> same output, no LLM needed."""
from __future__ import annotations

import csv
import re
from pathlib import Path

from .models import Job

VISA_PATTERNS = [
    r"visa sponsor\w*", r"sponsor\w* (?:a |your )?(?:work )?visa",
    r"work permit", r"blue card", r"highly skilled migrant", r"kennismigrant",
    r"relocation (?:support|package|assistance|budget|bonus)",
    r"(?:we|will) (?:help|support) (?:you )?(?:with )?relocat\w*",
    r"relocat\w* (?:is )?(?:provided|offered|available)",
]
NO_VISA_PATTERNS = [
    r"(?:no|not|unable to|cannot|can't|do not|don't) (?:offer |provide )?"
    r"(?:visa )?sponsor\w*",
    r"must (?:already )?(?:have|hold) (?:the )?(?:right|permit|authori[sz]ation) to work",
    r"eu (?:citizenship|passport) (?:is )?required",
    r"(?:only|must be) (?:eu|eea) (?:citizens?|residents?)",
]
LEVELS = r"(?:a1|a2|b1|b2|c1|c2)"
OPTIONAL_WORDS = r"(?:plus|bonus|nice to have|advantage|preferred|beneficial|asset|optional)"


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def language_requirement(text: str, language: str, optional_ok: bool = True) -> bool:
    """True if the post *requires* the given language.

    A mention like "German is a plus" counts as optional when optional_ok.
    """
    t = text.lower()
    lang = language.lower()
    if not re.search(rf"\b{lang}\b", t):
        return False
    # Look at each sentence that mentions the language.
    for sentence in re.split(r"[.\n;•]", t):
        if not re.search(rf"\b{lang}\b", sentence):
            continue
        if optional_ok and re.search(OPTIONAL_WORDS, sentence):
            continue
        if re.search(
            rf"(fluent|fluency|native|proficien\w*|business[- ]level|required|"
            rf"must|mandatory|essential|{LEVELS})",
            sentence,
        ):
            return True
    return False


def load_names(csv_path: str | None, column: str) -> set[str]:
    if not csv_path or not Path(csv_path).exists():
        return set()
    with open(csv_path, encoding="utf-8-sig") as f:
        return {
            norm_company(row[column])
            for row in csv.DictReader(f)
            if row.get(column)
        }


def norm_company(name: str) -> str:
    name = name.lower()
    name = re.sub(r"\b(b\.?v\.?|n\.?v\.?|gmbh|ag|sa|sas|ltd|inc|bv|se|srl)\b", "", name)
    return re.sub(r"[^a-z0-9]", "", name)


def apply_filters(job: Job, cfg: dict, *, skip_companies: set[str] | None = None,
                  ind_sponsors: set[str] | None = None) -> Job:
    """Set job.flags / job.reasons and mark status 'filtered_out' if rejected."""
    f = cfg["filters"]
    text = job.text.lower()
    title = job.title.lower()
    reasons: list[str] = []

    job.flags["visa_mentioned"] = _any(VISA_PATTERNS, text)
    job.flags["no_visa"] = _any(NO_VISA_PATTERNS, text)

    for word in f["reject_title"]:
        if re.search(rf"\b{re.escape(word.lower())}\b", title):
            reasons.append(f"title contains '{word}'")

    for lang in f["reject_languages"]:
        if language_requirement(text, lang, f["allow_language_if_optional"]):
            reasons.append(f"requires {lang}")

    if job.flags["no_visa"]:
        reasons.append("says no visa sponsorship")

    if f["require_any"] and not any(w.lower() in text for w in f["require_any"]):
        reasons.append("none of require_any keywords found")

    company_key = norm_company(job.company) if job.company else ""
    if skip_companies and company_key in skip_companies:
        reasons.append("company marked Skip/Applied in target list")

    if ind_sponsors is not None and (job.country.lower() in {"netherlands", "nl"}
                                     or "netherlands" in job.location.lower()):
        job.flags["ind_sponsor"] = company_key in ind_sponsors
        if ind_sponsors and not job.flags["ind_sponsor"]:
            reasons.append("NL company not on IND recognised-sponsor list")

    job.reasons = reasons
    job.status = "filtered_out" if reasons else "filtered_in"
    return job
