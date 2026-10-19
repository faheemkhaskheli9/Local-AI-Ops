"""Deterministic KB routing, permission and evidence-boundary checks."""
import json

import pytest

from aiops.kb import main, route, validate


def ref(repo, path, verified="2026-10-15"):
    return {"repository": f"faheemkhaskheli9/{repo}", "path": path,
            "retrieved": True, "last_verified": verified}


def test_routes_single_ai_domain_and_requires_real_retrieval():
    result = route("Compare LLM models for RAG")
    assert [r["id"] for r in result["routes"]] == ["ai"]
    assert result["retrieval_performed"] is False
    assert result["routes"][0]["index"] == "INDEX.md"


def test_multiple_domains_for_secure_medical_ai():
    result = route("Build secure clinical RAG API with authentication")
    assert {r["id"] for r in result["routes"]} == {
        "ai", "engineering", "security", "medical"
    }


def test_word_boundaries_and_unknown_topic():
    assert route("Send me an email")["routes"] == []
    assert route("Find the agency")["routes"] == []
    with pytest.raises(ValueError):
        route("   ")


def test_private_knowledge_requires_opt_in():
    task = "Update my resume and my projects"
    a = route(task)
    assert all(not x["private"] for x in a["routes"])
    assert a["private_access_required"]
    b = route(task, include_private=True)
    assert [x["id"] for x in b["routes"]] == ["personal"]
    assert b["routes"][0]["private"]


def test_evidence_requires_full_topic_for_each_selected_repo():
    task = "Clinical RAG"
    evidence = [
        ref("AI-Knowledge-Base", "llm-apps/rag-basics.md"),
        ref("Medical-Knowledge-Base", "docs/medicines/monographs/metformin.md"),
    ]
    result = validate(task, evidence, as_of="2026-10-19")
    assert result["ok"]
    assert len(result["candidate_citations"]) == 2
    assert result["verified_retrieval"] is False
    evidence.pop()
    assert not validate(task, evidence, as_of="2026-10-19")["ok"]


def test_indexes_alone_cannot_satisfy_evidence():
    a = validate("LLM", [ref("AI-Knowledge-Base", "INDEX.md")],
                 as_of="2026-10-19")
    assert not a["ok"]
    assert a["missing"] == ["faheemkhaskheli9/AI-Knowledge-Base"]


@pytest.mark.parametrize("path", ["../secret.md", "/etc/passwd.md",
                                  "docs\\evil.md", "foo/./bar.md", "readme.txt"])
def test_rejects_invalid_paths(path):
    x = validate("LLM", [ref("AI-Knowledge-Base", path)],
                 as_of="2026-10-19")
    assert not x["ok"]
    assert not x["candidate_citations"]


def test_rejects_injected_or_unauthorized_evidence():
    x = validate("LLM", [
        ref("Personal-Knowledge-Base", "profile/about-me.md"),
        {"repository": "faheemkhaskheli9/AI-Knowledge-Base",
         "path": "models/providers.md", "retrieved": "true"},
    ], as_of="2026-10-19")
    assert not x["ok"]


def test_freshness_warnings_and_invalid_dates():
    item = ref("AI-Knowledge-Base", "models/a.md", "2026-01-01")
    x = validate("LLM", [item], as_of="2026-10-19")
    assert x["ok"] and x["warnings"]
    item["last_verified"] = "3000-01-01"
    assert not validate("LLM", [item], as_of="2026-10-19")["ok"]
    item["last_verified"] = "not-a-date"
    assert not validate("LLM", [item], as_of="2026-10-19")["ok"]


def test_cli_planning_json(capsys):
    assert main(["plan", "clinical RAG"]) == 0
    d = json.loads(capsys.readouterr().out)
    assert len(d["routes"]) == 2


def test_cli_validation_exit_code(tmp_path, capsys):
    p = tmp_path / "evidence.json"
    p.write_text(json.dumps([ref("AI-Knowledge-Base", "models/gpt.md")]))
    assert main(["validate", "LLM", str(p), "--as-of", "2026-10-19"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"]
    p.write_text("[]")
    assert main(["validate", "LLM", str(p), "--as-of", "2026-10-19"]) == 1
