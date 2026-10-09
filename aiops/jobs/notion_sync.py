"""Push shortlisted jobs to a Notion database (upsert by URL).

Needs NOTION_TOKEN in the environment and the database shared with your
integration: https://developers.notion.com/docs/create-a-notion-integration
"""
from __future__ import annotations

import json
import os
import urllib.request

from .models import Job

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"


def _call(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("Set NOTION_TOKEN to your Notion integration secret.")
    req = urllib.request.Request(
        f"{API}{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": VERSION,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def _properties(job: Job, p: dict) -> dict:
    props: dict = {
        p["title"]: {"title": [{"text": {"content": job.title or job.url}}]},
        p["url"]: {"url": job.url},
    }
    if job.company:
        props[p["company"]] = {"rich_text": [{"text": {"content": job.company}}]}
    if job.location:
        props[p["location"]] = {"rich_text": [{"text": {"content": job.location}}]}
    if job.score is not None:
        props[p["score"]] = {"number": job.score}
    if job.cv_version:
        props[p["cv"]] = {"select": {"name": job.cv_version}}
    props[p["status"]] = {"select": {"name": job.status}}
    return props


def upsert(job: Job, cfg: dict) -> str:
    n = cfg["notion"]
    p = n["properties"]
    found = _call("POST", f"/databases/{n['database_id']}/query",
                  {"filter": {"property": p["url"], "url": {"equals": job.url}}})
    props = _properties(job, p)
    if found.get("results"):
        page_id = found["results"][0]["id"]
        _call("PATCH", f"/pages/{page_id}", {"properties": props})
        return page_id
    page = _call("POST", "/pages", {
        "parent": {"database_id": n["database_id"]},
        "properties": props,
    })
    return page["id"]
