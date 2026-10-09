"""Text helpers that people often ask an LLM to do. All deterministic."""
from __future__ import annotations

import difflib
import re
import unicodedata

BOILERPLATE = re.compile(
    r"(cookie|privacy policy|terms of (use|service)|all rights reserved|subscribe to|"
    r"sign up for our newsletter|equal opportunity employer|follow us on|share this)",
    re.I,
)


def clean(text: str) -> str:
    """Normalize unicode, fix smart quotes, collapse spaces and blank lines."""
    t = unicodedata.normalize("NFKC", text)
    t = (t.replace("‘", "'").replace("’", "'")
          .replace("“", '"').replace("”", '"')
          .replace(" ", " ").replace("​", ""))
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" *\n *", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def strip_boilerplate(text: str) -> str:
    """Drop short lines that are cookie banners, legal footers, share buttons."""
    keep = [l for l in text.splitlines()
            if not (len(l) < 200 and BOILERPLATE.search(l))]
    return "\n".join(keep)


def estimate_tokens(text: str) -> int:
    """Rough token count (about 4 characters per token for English)."""
    return max(1, round(len(text) / 4)) if text else 0


def trim_to_tokens(text: str, max_tokens: int) -> str:
    """Cut text to a token budget at a paragraph or sentence boundary."""
    limit = max_tokens * 4
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("\n\n", "\n", ". "):
        i = cut.rfind(sep)
        if i > limit * 0.6:
            return cut[: i + (1 if sep == ". " else 0)].rstrip()
    return cut.rstrip()


def compact(text: str, max_tokens: int | None = None) -> str:
    """clean + strip_boilerplate + dedupe repeated lines (+ optional budget).

    Use before pasting anything into an LLM.
    """
    seen, out = set(), []
    for line in strip_boilerplate(clean(text)).splitlines():
        k = line.strip().lower()
        if k and k in seen:
            continue
        seen.add(k)
        out.append(line)
    t = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()
    return trim_to_tokens(t, max_tokens) if max_tokens else t


def slugify(text: str, max_len: int = 60) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t[:max_len].rstrip("-")


def diff(a: str, b: str, context: int = 2) -> str:
    """Unified diff of two texts. Show what changed instead of resending both."""
    return "\n".join(difflib.unified_diff(
        a.splitlines(), b.splitlines(), "before", "after", lineterm="", n=context))


def keywords(text: str, vocab: list[str]) -> dict[str, int]:
    """Count whole-word hits of each vocab term (case-insensitive)."""
    t = text.lower()
    return {w: n for w in vocab
            if (n := len(re.findall(rf"(?<![a-z0-9]){re.escape(w.lower())}(?![a-z0-9])", t)))}
