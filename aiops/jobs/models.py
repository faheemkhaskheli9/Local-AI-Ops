from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from urllib.parse import urlsplit, urlunsplit


def normalize_url(url: str) -> str:
    """Strip query string, fragment and trailing slash so the same job
    always maps to the same key (LinkedIn adds tracking params)."""
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


@dataclass
class Job:
    url: str
    title: str = ""
    company: str = ""
    location: str = ""
    country: str = ""
    description: str = ""
    source: str = "manual"

    # Filled in by the pipeline
    status: str = "new"  # new | filtered_out | scored | drafted | applied | skip
    reasons: list[str] = field(default_factory=list)
    flags: dict[str, bool] = field(default_factory=dict)
    score: float | None = None
    cv_version: str | None = None
    extracted: dict | None = None

    def __post_init__(self) -> None:
        self.url = normalize_url(self.url)

    @property
    def key(self) -> str:
        return hashlib.sha256(self.url.encode()).hexdigest()[:16]

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.company}\n{self.location}\n{self.description}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Job":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
