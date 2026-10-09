from aiops.jobs.brief import build_brief, trim_description
from aiops.jobs.config import load_config
from aiops.jobs.cv_select import pick_cv
from aiops.jobs.filters import apply_filters, language_requirement, norm_company
from aiops.jobs.models import Job, normalize_url
from aiops.jobs.pipeline import process
from aiops.jobs.score import keyword_score
from aiops.jobs.store import Store

CFG = load_config(None)

LLM_JOB = Job(
    url="https://www.linkedin.com/jobs/view/123/?trackingId=abc&refId=x",
    title="Senior LLM Engineer",
    company="Acme AI B.V.",
    location="Amsterdam, Netherlands",
    description=(
        "About the role\nBuild RAG systems and LLM agents with LangChain.\n\n"
        "Requirements\nPython, PyTorch, Docker, AWS, retrieval and embedding "
        "pipelines, FastAPI. German is a plus.\n\n"
        "What we offer\nVisa sponsorship and relocation support. Free lunch."
    ),
)


def test_normalize_url_strips_tracking():
    assert normalize_url("HTTPS://LinkedIn.com/jobs/view/1/?a=b#x") == \
        "https://linkedin.com/jobs/view/1"
    assert LLM_JOB.url == "https://www.linkedin.com/jobs/view/123"


def test_language_requirement():
    assert language_requirement("Fluent German (C1) is required.", "german")
    assert not language_requirement("German is a plus.", "german")
    assert not language_requirement("Work with our Germany team.", "german")
    assert language_requirement("Dutch: native or business-level.", "dutch")


def test_filters_visa_and_rejections():
    job = apply_filters(Job(**LLM_JOB.to_dict()), CFG)
    assert job.status == "filtered_in"
    assert job.flags["visa_mentioned"]

    bad = Job(url="https://x.com/2", title="ML Intern",
              description="We do not offer visa sponsorship. Fluent German required.")
    apply_filters(bad, CFG)
    assert bad.status == "filtered_out"
    assert len(bad.reasons) == 3


def test_skip_companies_and_ind_list():
    skip = {norm_company("Acme AI BV")}
    job = apply_filters(Job(**LLM_JOB.to_dict()), CFG, skip_companies=skip)
    assert "company marked Skip/Applied in target list" in job.reasons

    job = apply_filters(Job(**LLM_JOB.to_dict()), CFG, ind_sponsors={"othercorp"})
    assert job.flags["ind_sponsor"] is False
    assert any("IND" in r for r in job.reasons)


def test_pick_cv_deterministic():
    v, hits = pick_cv(LLM_JOB.text, CFG["cv_versions"])
    assert v == "llm" and hits["llm"] > hits["ml"]
    v, _ = pick_cv("Computer vision with PyTorch, YOLO and OpenCV detection.",
                   CFG["cv_versions"])
    assert v == "ml"
    v, _ = pick_cv("Backend engineer, Java.", CFG["cv_versions"])
    assert v == "general"


def test_keyword_score_stable():
    a = keyword_score(LLM_JOB.text, CFG["skills"])
    b = keyword_score(LLM_JOB.text, CFG["skills"])
    assert a == b and a[0] > 0.5
    assert "rag" in a[1] and "langchain" in a[1]


def test_store_dedupes(tmp_path):
    s = Store(tmp_path / "t.db")
    assert s.add(Job(url="https://a.com/job/1?utm=x"))
    assert not s.add(Job(url="https://a.com/job/1/"))
    assert len(s.by_status("new")) == 1


def test_process_and_brief(tmp_path):
    job = process(Job(**LLM_JOB.to_dict()), CFG)
    assert job.status == "shortlist" and job.cv_version == "llm"
    brief = build_brief(job)
    assert "Free lunch" not in brief  # benefits section trimmed
    assert "LangChain" in brief
    assert len(brief) < len(LLM_JOB.description) + 400


def test_trim_keeps_text_without_headings():
    assert trim_description("Just one paragraph.") == "Just one paragraph."
