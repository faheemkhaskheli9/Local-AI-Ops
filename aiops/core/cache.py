"""Disk cache in SQLite. Same input -> stored output, no recompute, no tokens.

    from aiops.core import cached

    @cached("summaries")
    def summarize(text: str) -> str: ...
"""
from __future__ import annotations

import functools
import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

DEFAULT_PATH = Path(os.environ.get("AIOPS_CACHE", Path.home() / ".cache" / "aiops" / "cache.db"))


def stable_hash(obj: Any) -> str:
    """Hash any JSON-able object the same way on every machine and run."""
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class Cache:
    def __init__(self, path: str | Path = DEFAULT_PATH):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (ns TEXT, key TEXT, value TEXT, "
            "created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (ns, key))"
        )
        self.conn.commit()

    def get(self, ns: str, key: str) -> Any | None:
        row = self.conn.execute(
            "SELECT value FROM cache WHERE ns = ? AND key = ?", (ns, key)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def set(self, ns: str, key: str, value: Any) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO cache (ns, key, value) VALUES (?, ?, ?)",
                (ns, key, json.dumps(value, ensure_ascii=False)),
            )
            self.conn.commit()

    def clear(self, ns: str | None = None) -> int:
        with self._lock:
            cur = (self.conn.execute("DELETE FROM cache WHERE ns = ?", (ns,)) if ns
                   else self.conn.execute("DELETE FROM cache"))
            self.conn.commit()
            return cur.rowcount


_default: Cache | None = None


def default_cache() -> Cache:
    global _default
    if _default is None:
        _default = Cache()
    return _default


def cached(ns: str, cache: Cache | None = None) -> Callable:
    """Decorator: cache a function's JSON-able result by its arguments."""
    def deco(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            c = cache or default_cache()
            key = stable_hash([fn.__module__, fn.__qualname__, args, kwargs])
            hit = c.get(ns, key)
            if hit is not None:
                return hit
            value = fn(*args, **kwargs)
            c.set(ns, key, value)
            return value
        return wrapper
    return deco
