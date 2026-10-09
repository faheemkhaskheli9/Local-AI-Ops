import json

from aiops.cli import main
from aiops.core.cache import Cache, cached, stable_hash
from aiops.docs.extract import csv_to_text, html_to_text, to_text
from aiops.text import ops
from aiops.youtube import tools as yt


def test_stable_hash_order_independent():
    assert stable_hash({"a": 1, "b": 2}) == stable_hash({"b": 2, "a": 1})


def test_cached_decorator(tmp_path):
    calls = []
    c = Cache(tmp_path / "c.db")

    @cached("t", cache=c)
    def double(x):
        calls.append(x)
        return x * 2

    assert double(3) == 6 and double(3) == 6
    assert calls == [3]
    assert c.clear("t") == 1


def test_compact_and_trim():
    raw = "Hello  world\n\n\n\nAccept cookie settings\nHello world\nKeep this."
    out = ops.compact(raw)
    assert "cookie" not in out
    assert out.count("Hello world") == 1
    long = ("Sentence one is here. " * 200).strip()
    cut = ops.trim_to_tokens(long, 50)
    assert len(cut) <= 200 and cut.endswith(".")


def test_text_helpers():
    assert ops.slugify("Hello, Wörld! RAG 101") == "hello-world-rag-101"
    assert ops.keywords("RAG and rag, not drag", ["rag"]) == {"rag": 2}
    assert "+b" in ops.diff("a\nc", "a\nb\nc")
    assert ops.estimate_tokens("abcd" * 10) == 10


def test_html_and_csv():
    html = ("<html><script>x()</script><nav>menu</nav><h1>Title</h1>"
            "<p>Para one</p><ul><li>a</li><li>b</li></ul></html>")
    t = html_to_text(html)
    assert "x()" not in t and "menu" not in t
    assert "# Title" in t and "- a" in t
    assert csv_to_text("a,b\n1,2\n3,4", max_rows=1).endswith("1 more rows")


def test_to_text_files(tmp_path):
    p = tmp_path / "d.json"
    p.write_text(json.dumps({"k": [1, 2]}))
    assert '"k"' in to_text(p)


SRT = """1
00:00:00,000 --> 00:00:04,000
Welcome to the channel.

2
00:01:10,500 --> 00:01:15,000
First let's install Python.

3
00:03:00,000 --> 00:03:05,000
Now we train the model.
"""


def test_srt_roundtrip_and_chapters():
    segs = yt.parse_srt(SRT)
    assert len(segs) == 3 and segs[1].start == 70.5
    assert yt.parse_srt(yt.to_srt(segs))[2].text == "Now we train the model."
    chs = yt.chapters_from_markers(segs, {"install": "Setup", "we train": "Training"})
    assert yt.chapters_text(chs) == "0:00 Intro\n1:10 Setup\n3:00 Training"
    gap = yt.chapters_by_gap(segs, pause=2, min_len=60)
    assert [t for t, _ in gap] == [0.0, 70.5, 180.0]
    assert yt.fmt_ts(3723) == "1:02:03"


def test_cli_text(tmp_path, capsys):
    f = tmp_path / "a.txt"
    f.write_text("x" * 40)
    assert main(["text", "tokens", str(f)]) == 0
    assert capsys.readouterr().out.strip() == "10"
