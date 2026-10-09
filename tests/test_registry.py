"""Pure offline validation for shared adapter contracts."""
import json

import pytest

from aiops.export import export
from aiops.registry import dispatch, get_tool, list_tools, tool


EXPECTED = {"file_to_text", "compact_text", "count_tokens", "text_diff",
            "job_check", "srt_to_chapters", "local_llm"}


def test_catalog_reuses_exact_existing_mcp_tools():
    assert {spec.name for spec in list_tools()} == EXPECTED
    assert get_tool("local_llm").tier == "llm"
    assert all(not spec.remote for spec in list_tools())


def test_export_openai_and_anthropic_share_schemas():
    oa = export("openai")
    cc = export("openai-chat")
    an = export("anthropic")
    assert [x["name"] for x in oa] == [x["name"] for x in an]
    assert oa[0]["parameters"] == an[0]["input_schema"]
    assert cc[0]["function"]["name"] == oa[0]["name"]
    assert len(oa) == 7
    assert json.loads(json.dumps(oa)) == oa


def test_signature_metadata_defaults_and_unions():
    x = get_tool("srt_to_chapters").parameters()
    assert x["required"] == ["srt_text"]
    assert x["additionalProperties"] is False
    assert x["properties"]["markers"] == {
        "anyOf": [{"type": "array", "items": {"type": "string"}},
                  {"type": "null"}], "default": None,
    }


def test_dispatch_existing_python_function():
    assert dispatch("count_tokens", {"text": "abcd" * 7}) == 7
    assert dispatch("text_diff", {"before": "a", "after": "b"})


def test_dispatch_rejects_unknown_missing_and_wrong_types():
    with pytest.raises(ValueError):
        dispatch("github_delete_repository", {})
    with pytest.raises(TypeError):
        dispatch("count_tokens", {})
    with pytest.raises(TypeError):
        dispatch("count_tokens", {"text": 3})
    with pytest.raises(TypeError):
        dispatch("count_tokens", {"text": "x", "other": 2})
    with pytest.raises(TypeError):
        dispatch("srt_to_chapters", {"srt_text": "a", "markers": [2]})
    with pytest.raises(TypeError):
        dispatch("count_tokens", [])


def test_remote_deny_by_default():
    with pytest.raises(PermissionError):
        dispatch("file_to_text", {"path": "/etc/passwd"}, remote=True)
    with pytest.raises(PermissionError):
        dispatch("local_llm", {"prompt": "hello"}, remote=True)
    assert list_tools(remote=True) == []


def test_registry_rejects_duplicate_and_bad_tier():
    with pytest.raises(ValueError):
        tool(name="foo", tier="internet")
    with pytest.raises(ValueError):
        tool(name="count_tokens")(lambda text: None)
