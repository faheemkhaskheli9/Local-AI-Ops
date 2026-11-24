"""One contract per tool across dispatch, the CLI and MCP (offline)."""
import asyncio
import dataclasses
import functools
import json
import subprocess
import sys

import pytest

from aiops.cli import main
from aiops.export import export
from aiops.registry import dispatch, list_tools

SRT = """1
00:00:00,000 --> 00:00:04,000
Welcome to the lesson.

2
00:01:10,000 --> 00:01:14,000
First we install the tools.
"""
JOB = "We need a Python LLM engineer with RAG, LangChain and Docker experience."


@pytest.fixture
def files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # no config.yaml here: built-in job defaults
    monkeypatch.delenv("AIOPS_JOBS_CONFIG", raising=False)
    data = {"a.txt": "alpha\nbeta\n", "b.txt": "alpha\ngamma\n", "talk.srt": SRT,
            "page.html": "<h1>Title</h1><p>Body text here.</p>", "job.txt": JOB,
            "evidence.json": json.dumps([{"repository": "faheemkhaskheli9/AI-Knowledge-Base",
                                          "path": "concepts/transformers.md",
                                          "retrieved": True}])}
    for name, text in data.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    return data


def _cli(capsys, argv):
    capsys.readouterr()
    main(argv)
    return capsys.readouterr().out.rstrip("\n")


# tool -> (dispatch arguments, equivalent CLI argv, how the CLI prints the result)
def cases(data):
    return {
        "file_to_text": ({"path": "page.html", "max_tokens": 50},
                         ["docs", "totext", "page.html", "--max-tokens", "50"], str),
        "compact_text": ({"text": data["a.txt"], "max_tokens": 50},
                         ["text", "compact", "a.txt", "--max-tokens", "50"], str),
        "count_tokens": ({"text": data["a.txt"]}, ["text", "tokens", "a.txt"], str),
        "text_diff": ({"before": data["a.txt"], "after": data["b.txt"]},
                      ["text", "diff", "a.txt", "b.txt"], str),
        "srt_to_chapters": ({"srt_text": SRT, "markers": ["install"]},
                            ["yt", "chapters", "talk.srt", "--markers", "install"], str),
        "local_llm": ({"prompt": "hi"}, ["llm", "local", "hi"], str),
        "kb_plan": ({"task": "Clinical RAG"}, ["kb", "plan", "Clinical RAG"],
                    lambda r: json.dumps(r, indent=2, ensure_ascii=False)),
        "kb_validate": ({"task": "LLM", "evidence": json.loads(data["evidence.json"]),
                         "as_of": "2026-10-19"},
                        ["kb", "validate", "LLM", "evidence.json", "--as-of", "2026-10-19"],
                        lambda r: json.dumps(r, indent=2, ensure_ascii=False)),
        "job_check": ({"title": "LLM Engineer", "company": "Acme", "location": "Amsterdam",
                       "description": JOB},
                      ["jobs", "check", "job.txt", "--title", "LLM Engineer",
                       "--company", "Acme", "--location", "Amsterdam"],
                      lambda r: json.dumps(r, indent=2, ensure_ascii=False)),
    }


@pytest.fixture
def fake_llm(monkeypatch):
    from aiops.core import llm
    monkeypatch.setattr(llm, "local", lambda prompt, schema=None, model=None: f"echo:{prompt}")


def test_every_tool_has_a_matching_cli_command(files, fake_llm, capsys):
    table = cases(files)
    assert set(table) == {spec.name for spec in list_tools()}
    for name, (arguments, argv, render) in table.items():
        assert _cli(capsys, argv) == render(dispatch(name, arguments)), name


def test_job_check_skips_llm_and_uses_skip_list(tmp_path, monkeypatch):
    (tmp_path / "companies.csv").write_text("company,status\nAcme,Skip\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text(
        f"ollama:\n  enabled: true\nfilters:\n  target_companies_csv: {tmp_path / 'companies.csv'}\n",
        encoding="utf-8")
    from aiops.jobs import extract
    monkeypatch.setattr(extract, "extract", lambda *a, **k: pytest.fail("LLM called"))
    args = {"title": "LLM Engineer", "company": "Acme", "location": "Amsterdam",
            "description": JOB, "config_path": str(tmp_path / "config.yaml")}
    assert dispatch("job_check", args)["status"] == "filtered_out"
    monkeypatch.setenv("AIOPS_JOBS_CONFIG", str(tmp_path / "config.yaml"))
    del args["config_path"]
    assert dispatch("job_check", args)["status"] == "filtered_out"
    with pytest.raises(FileNotFoundError):
        dispatch("job_check", {**args, "config_path": str(tmp_path / "missing.yaml")})


def test_kb_validate_reports_the_date_it_used():
    assert dispatch("kb_validate", {"task": "LLM", "evidence": [],
                                    "as_of": "2026-10-19"})["as_of"] == "2026-10-19"


# --- MCP (skipped when the optional `mcp` extra is not installed) ---

def _mcp():
    pytest.importorskip("mcp")
    from aiops.mcp_server import build
    return build()


def test_mcp_lists_registry_tools_with_exported_schemas():
    server = _mcp()
    tools = asyncio.run(server.list_tools())
    exported = {t["name"]: t["input_schema"] for t in export("anthropic")}
    assert {t.name: getattr(t, "input_schema", None) or t.inputSchema
            for t in tools} == exported


@pytest.mark.parametrize("name, arguments, message", [
    ("count_tokens", {"text": 3}, "argument 'text' must be string, got integer"),
    ("compact_text", {"text": "x", "max_tokens": "5"}, "'max_tokens' must be integer"),
    ("count_tokens", {"text": "x", "extra": 1}, "unexpected keyword argument 'extra'"),
    ("count_tokens", {}, "missing a required argument: 'text'"),
    ("no_such_tool", {}, "Unknown tool: no_such_tool"),
])
def test_mcp_rejects_what_dispatch_rejects(name, arguments, message, monkeypatch):
    server = _mcp()
    from aiops import registry
    calls = []

    def spy(fn):
        @functools.wraps(fn)
        def run(*args, **kwargs):
            calls.append(fn.__name__)
            return fn(*args, **kwargs)
        return run

    monkeypatch.setattr(registry, "_TOOLS", {
        key: dataclasses.replace(spec, function=spy(spec.function))
        for key, spec in registry._TOOLS.items()})
    with pytest.raises((TypeError, ValueError)):
        dispatch(name, arguments)
    with pytest.raises(Exception, match=message):
        asyncio.run(server.call_tool(name, arguments))
    assert not calls  # validation failed before any tool ran


def test_mcp_calls_go_through_dispatch(monkeypatch):
    server = _mcp()
    from aiops import mcp_server
    seen = []
    real = mcp_server.dispatch
    monkeypatch.setattr(mcp_server, "dispatch", lambda n, a: seen.append(n) or real(n, a))
    asyncio.run(server.call_tool("count_tokens", {"text": "abcdabcd"}))
    # Lists sent as JSON strings are still accepted, as the SDK allows.
    asyncio.run(server.call_tool("srt_to_chapters",
                                 {"srt_text": SRT, "markers": '["install"]'}))
    assert seen == ["count_tokens", "srt_to_chapters"]


def test_mcp_stdio_server_starts_and_lists_tools():
    pytest.importorskip("mcp")
    proc = subprocess.Popen([sys.executable, "-m", "aiops.cli", "mcp"], stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    try:
        def send(msg):
            proc.stdin.write(json.dumps({"jsonrpc": "2.0", **msg}) + "\n")
            proc.stdin.flush()

        send({"id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"}}})
        assert json.loads(proc.stdout.readline())["result"]["serverInfo"]["name"] == "aiops"
        send({"method": "notifications/initialized"})
        send({"id": 2, "method": "tools/list"})
        names = {t["name"] for t in json.loads(proc.stdout.readline())["result"]["tools"]}
        assert names == {spec.name for spec in list_tools()}
        send({"id": 3, "method": "tools/call",
              "params": {"name": "count_tokens", "arguments": {"text": 3}}})
        result = json.loads(proc.stdout.readline())["result"]
        assert result["isError"] and "must be string" in result["content"][0]["text"]
    finally:
        proc.stdin.close()
        proc.wait(timeout=30)
