"""Deterministic LLM calls with caching.

- `local(...)`  : Ollama, temperature 0, fixed seed, optional JSON schema. Free.
- `claude(...)` : Anthropic API, temperature 0, cached. Repeat calls cost nothing.

Both return the same answer for the same input, because the answer is
stored the first time and read back afterwards.
"""
from __future__ import annotations

import json
import os
import urllib.request

from .cache import Cache, default_cache, stable_hash

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("AIOPS_LOCAL_MODEL", "qwen2.5:7b")
CLAUDE_MODEL = os.environ.get("AIOPS_CLAUDE_MODEL", "claude-haiku-5-5")


def _post(url: str, body: dict, headers: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def local(prompt: str, *, schema: dict | None = None, system: str | None = None,
          model: str | None = None, seed: int = 42, cache: Cache | None = None,
          use_cache: bool = True):
    """Call a local Ollama model. Returns a dict when `schema` is given, else str."""
    body = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "top_k": 1, "seed": seed},
    }
    if system:
        body["system"] = system
    if schema:
        body["format"] = schema
    c = cache or default_cache()
    key = stable_hash(body)
    if use_cache and (hit := c.get("llm.local", key)) is not None:
        return hit
    raw = _post(f"{OLLAMA_HOST.rstrip('/')}/api/generate", body, {})["response"]
    out = json.loads(raw) if schema else raw.strip()
    c.set("llm.local", key, out)
    return out


def claude(prompt: str, *, system: str | None = None, model: str | None = None,
           max_tokens: int = 1024, cache: Cache | None = None, use_cache: bool = True) -> str:
    """Call Claude via the API (needs ANTHROPIC_API_KEY). Cached by full request."""
    body = {
        "model": model or CLAUDE_MODEL,
        "max_tokens": max_tokens,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        body["system"] = system
    c = cache or default_cache()
    key = stable_hash(body)
    if use_cache and (hit := c.get("llm.claude", key)) is not None:
        return hit
    key_env = os.environ.get("ANTHROPIC_API_KEY")
    if not key_env:
        raise RuntimeError("Set ANTHROPIC_API_KEY to use aiops.core.llm.claude")
    data = _post("https://api.anthropic.com/v1/messages", body,
                 {"x-api-key": key_env, "anthropic-version": "2023-06-01"})
    out = "".join(b.get("text", "") for b in data.get("content", []))
    c.set("llm.claude", key, out)
    return out
