"""Structured field extraction from a job post with a local model (Ollama).

Uses aiops.core.llm.local: temperature 0, fixed seed, JSON schema, cached.
"""
from __future__ import annotations

from aiops.core import llm

SCHEMA = {
    "type": "object",
    "properties": {
        "seniority": {"type": "string", "enum": ["junior", "mid", "senior", "lead", "unknown"]},
        "salary_min_eur": {"type": ["integer", "null"]},
        "salary_max_eur": {"type": ["integer", "null"]},
        "remote": {"type": "string", "enum": ["onsite", "hybrid", "remote", "unknown"]},
        "visa_sponsorship": {"type": "string", "enum": ["yes", "no", "unknown"]},
        "required_languages": {"type": "array", "items": {"type": "string"}},
        "years_experience": {"type": ["integer", "null"]},
        "main_stack": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["seniority", "salary_min_eur", "salary_max_eur", "remote",
                 "visa_sponsorship", "required_languages", "years_experience",
                 "main_stack"],
}

PROMPT = """Extract facts from this job post. Use only what the text says.
Use "unknown" or null when the post does not say. Salary in EUR per year.

JOB POST:
{text}"""


def extract(text: str, cfg: dict, store=None, max_chars: int = 6000) -> dict:
    o = cfg["ollama"]
    return llm.local(PROMPT.format(text=text[:max_chars]), schema=SCHEMA,
                     model=o["model"], seed=o["seed"])
