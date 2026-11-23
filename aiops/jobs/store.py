"""SQLite cache keyed by normalized job URL, so no job is processed twice."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from .models import Job

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    url TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class Store:
    def __init__(self, path: str | Path = "jobs.db"):
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)

    def add(self, job: Job) -> bool:
        """Insert a new job. Returns False if the URL is already known."""
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO jobs (url, status, data) VALUES (?, ?, ?)",
            (job.url, job.status, json.dumps(job.to_dict())),
        )
        self.conn.commit()
        return cur.rowcount == 1

    def save(self, job: Job) -> None:
        self.conn.execute(
            "INSERT INTO jobs (url, status, data) VALUES (?, ?, ?) "
            "ON CONFLICT(url) DO UPDATE SET status=excluded.status, "
            "data=excluded.data, updated_at=CURRENT_TIMESTAMP",
            (job.url, job.status, json.dumps(job.to_dict())),
        )
        self.conn.commit()

    def get(self, url: str) -> Job | None:
        from .models import normalize_url

        row = self.conn.execute(
            "SELECT data FROM jobs WHERE url = ?", (normalize_url(url),)
        ).fetchone()
        return Job.from_dict(json.loads(row[0])) if row else None

    def by_status(self, *statuses: str) -> list[Job]:
        q = "SELECT data FROM jobs"
        args: tuple = ()
        if statuses:
            q += f" WHERE status IN ({','.join('?' * len(statuses))})"
            args = statuses
        q += " ORDER BY created_at, url"
        return [Job.from_dict(json.loads(r[0])) for r in self.conn.execute(q, args)]
