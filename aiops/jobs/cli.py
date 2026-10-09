"""aiops jobs: collect | add | run | list | brief | sync"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import collect
from .brief import build_brief
from .config import load_config
from .pipeline import run
from .store import Store


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="aiops jobs", description=__doc__)
    ap.add_argument("-c", "--config", default="config.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("collect", help="search job boards with JobSpy and store new jobs")
    a = sub.add_parser("add", help="add jobs from a .txt (URLs) or .csv file")
    a.add_argument("file")
    sub.add_parser("run", help="filter, pick CV and score all new jobs")
    ls = sub.add_parser("list", help="show jobs by status")
    ls.add_argument("--status", default="shortlist")
    b = sub.add_parser("brief", help="write short LLM briefs for shortlisted jobs")
    b.add_argument("--out", default="briefs")
    b.add_argument("--task", default="cover letter")
    sub.add_parser("sync", help="push shortlisted jobs to Notion")

    args = ap.parse_args(argv)
    cfg = load_config(args.config)
    store = Store(cfg["db_path"])

    if args.cmd in ("collect", "add"):
        jobs = collect.from_jobspy(cfg) if args.cmd == "collect" else collect.from_file(args.file)
        new = sum(store.add(j) for j in jobs)
        print(f"found {len(jobs)}, new {new}, duplicates {len(jobs) - new}")

    elif args.cmd == "run":
        counts = run(store, cfg)
        print(", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) or "nothing new")

    elif args.cmd == "list":
        for j in sorted(store.by_status(args.status), key=lambda j: -(j.score or 0)):
            why = "; ".join(j.reasons)
            print(f"{(j.score or 0):.2f}  {j.cv_version or '-':8} {j.company[:20]:20} "
                  f"{j.title[:40]:40} {j.url}" + (f"  [{why}]" if why else ""))

    elif args.cmd == "brief":
        out = Path(args.out)
        out.mkdir(exist_ok=True)
        jobs = store.by_status("shortlist")
        for j in jobs:
            (out / f"{j.key}.md").write_text(build_brief(j, args.task), encoding="utf-8")
        print(f"wrote {len(jobs)} briefs to {out}/")

    elif args.cmd == "sync":
        from .notion_sync import upsert

        if not cfg["notion"]["enabled"] or not cfg["notion"]["database_id"]:
            print("Enable notion and set database_id in config.yaml first.")
            return 1
        jobs = store.by_status("shortlist")
        for j in jobs:
            upsert(j, cfg)
        print(f"synced {len(jobs)} jobs to Notion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
