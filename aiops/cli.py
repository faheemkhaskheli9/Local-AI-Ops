"""aiops: one command for every tool.

    aiops text compact FILE [--max-tokens N]   clean + dedupe + trim
    aiops text tokens FILE                     rough token count
    aiops text diff A B                        unified diff
    aiops docs totext FILE [--compact]         PDF/DOCX/HTML/CSV -> text
    aiops yt transcribe AUDIO [--lang ur]      local Whisper -> .srt
    aiops yt chapters SRT [--markers a,b]      YouTube chapter list
    aiops yt thumb IMAGE OUT                   1280x720 JPEG under 2 MB
    aiops llm local "prompt" [--schema f.json] cached local model call
    aiops jobs ...                             job pipeline (see aiops jobs -h)
    aiops cache clear [NS]                     clear cached results
    aiops mcp                                  run MCP server for Claude
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _read(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["jobs"]:
        from aiops.jobs.cli import main as jobs_main
        return jobs_main(argv[1:])

    ap = argparse.ArgumentParser(prog="aiops", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    groups = ap.add_subparsers(dest="group", required=True)

    t = groups.add_parser("text").add_subparsers(dest="cmd", required=True)
    c = t.add_parser("compact"); c.add_argument("file"); c.add_argument("--max-tokens", type=int)
    t.add_parser("tokens").add_argument("file")
    d = t.add_parser("diff"); d.add_argument("a"); d.add_argument("b")

    dc = groups.add_parser("docs").add_subparsers(dest="cmd", required=True)
    tt = dc.add_parser("totext"); tt.add_argument("file")
    tt.add_argument("--compact", action="store_true"); tt.add_argument("--max-tokens", type=int)

    y = groups.add_parser("yt").add_subparsers(dest="cmd", required=True)
    tr = y.add_parser("transcribe"); tr.add_argument("audio")
    tr.add_argument("--lang"); tr.add_argument("--model", default="small")
    ch = y.add_parser("chapters"); ch.add_argument("srt")
    ch.add_argument("--markers", help="comma-separated phrases; default: split on pauses")
    th = y.add_parser("thumb"); th.add_argument("image"); th.add_argument("out")

    lm = groups.add_parser("llm").add_subparsers(dest="cmd", required=True)
    lo = lm.add_parser("local"); lo.add_argument("prompt")
    lo.add_argument("--schema"); lo.add_argument("--model")

    groups.add_parser("jobs", help="job pipeline (aiops jobs -h)")
    ca = groups.add_parser("cache").add_subparsers(dest="cmd", required=True)
    ca.add_parser("clear").add_argument("ns", nargs="?")
    groups.add_parser("mcp", help="run the MCP server (stdio)")

    a = ap.parse_args(argv)

    if a.group == "text":
        from aiops.text import ops
        if a.cmd == "compact":
            print(ops.compact(_read(a.file), a.max_tokens))
        elif a.cmd == "tokens":
            print(ops.estimate_tokens(_read(a.file)))
        else:
            print(ops.diff(_read(a.a), _read(a.b)))

    elif a.group == "docs":
        from aiops.docs.extract import to_text
        from aiops.text.ops import compact
        out = to_text(a.file)
        print(compact(out, a.max_tokens) if a.compact or a.max_tokens else out)

    elif a.group == "yt":
        from aiops.youtube import tools as yt
        if a.cmd == "transcribe":
            srt = yt.to_srt(yt.transcribe(a.audio, a.model, a.lang))
            out = Path(a.audio).with_suffix(".srt")
            out.write_text(srt, encoding="utf-8")
            print(out)
        elif a.cmd == "chapters":
            segs = yt.parse_srt(_read(a.srt))
            chs = (yt.chapters_from_markers(segs, [m.strip() for m in a.markers.split(",")])
                   if a.markers else yt.chapters_by_gap(segs))
            print(yt.chapters_text(chs))
        else:
            print(yt.thumbnail(a.image, a.out))

    elif a.group == "llm":
        from aiops.core import llm
        schema = json.loads(Path(a.schema).read_text()) if a.schema else None
        out = llm.local(a.prompt, schema=schema, model=a.model)
        print(json.dumps(out, indent=2, ensure_ascii=False) if schema else out)

    elif a.group == "cache":
        from aiops.core.cache import default_cache
        print(f"removed {default_cache().clear(a.ns)} entries")

    elif a.group == "mcp":
        from aiops.mcp_server import run
        run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
