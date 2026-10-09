"""Build a short brief for the LLM step (cover letter / recruiter note).

Instead of pasting a whole job page into Claude or ChatGPT, send only the
facts the writer needs. This usually cuts the prompt by 70-90%.
"""
from __future__ import annotations

import re

from .models import Job

KEEP_HEADINGS = re.compile(
    r"(responsibilit|what you.?ll do|requirement|qualification|what we.?re looking|"
    r"you have|you bring|must|skills|about the role|the role)", re.I)
DROP_HEADINGS = re.compile(
    r"(benefit|perks|what we offer|equal opportunit|diversity|about us|our story|"
    r"privacy|gdpr|how to apply)", re.I)


def trim_description(text: str, max_chars: int = 2500) -> str:
    """Keep role/requirements sections, drop benefits and boilerplate."""
    blocks = re.split(r"\n\s*\n", text.strip())
    kept, keep_mode = [], True
    for b in blocks:
        first = b.strip().splitlines()[0] if b.strip() else ""
        if len(first) < 80 and DROP_HEADINGS.search(first):
            keep_mode = False
        elif len(first) < 80 and KEEP_HEADINGS.search(first):
            keep_mode = True
        if keep_mode:
            kept.append(re.sub(r"[ \t]+", " ", b.strip()))
    out = "\n\n".join(kept) or text
    return out[:max_chars]


def build_brief(job: Job, task: str = "cover letter") -> str:
    ex = job.extracted or {}
    facts = [
        f"Role: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location}",
        f"CV version to use: {job.cv_version}",
        f"Fit score: {job.score}",
    ]
    if ex:
        facts.append(f"Seniority: {ex.get('seniority')}; stack: "
                     f"{', '.join(ex.get('main_stack') or [])}")
    matched = (job.flags or {}).get("matched_skills")
    return (
        f"Write a {task} for this job. Keep it under 250 words, formal and specific.\n\n"
        + "\n".join(facts)
        + (f"\nMy matching skills: {matched}" if matched else "")
        + f"\n\nKey parts of the post:\n{trim_description(job.description)}\n"
    )
