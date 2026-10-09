from __future__ import annotations

import copy
from pathlib import Path

import yaml

DEFAULTS: dict = {
    "db_path": "jobs.db",
    "search": {
        "terms": ["machine learning engineer", "LLM engineer", "AI engineer"],
        "locations": ["Netherlands", "Germany", "Belgium"],
        "sites": ["indeed", "linkedin"],
        "results_per_search": 20,
        "hours_old": 72,
    },
    "filters": {
        "require_any": [],  # e.g. ["python"]; empty = no requirement
        "reject_title": ["intern", "internship", "werkstudent", "phd", "student"],
        "reject_languages": ["german", "dutch", "french"],
        "allow_language_if_optional": True,
        "target_companies_csv": None,  # CSV with columns: company,status
        "ind_sponsors_csv": None,  # CSV of IND recognised sponsors (column: name)
    },
    "cv_versions": {
        "llm": ["llm", "rag", "langchain", "llamaindex", "agent", "agents",
                "prompt", "retrieval", "genai", "generative", "openai",
                "fine-tuning", "vector", "embedding", "mcp"],
        "ml": ["computer vision", "pytorch", "tensorflow", "segmentation",
               "detection", "yolo", "opencv", "time series", "forecasting",
               "mlops", "deep learning", "classification"],
        "default": "general",
        "min_hits": 2,
    },
    "skills": ["python", "pytorch", "tensorflow", "llm", "rag", "langchain",
               "llamaindex", "fastapi", "docker", "aws", "azure", "gcp",
               "computer vision", "opencv", "yolo", "transformers",
               "hugging face", "mlflow", "airflow", "sql", "nlp", "agents"],
    "scoring": {
        "threshold": 0.45,
        "keyword_weight": 0.6,
        "embedding_weight": 0.4,
        "embedding_model": None,  # e.g. "BAAI/bge-small-en-v1.5"
        "cv_text_files": {},  # {"llm": "cvs/llm.txt", ...} used for embeddings
    },
    "ollama": {
        "enabled": False,
        "host": "http://localhost:11434",
        "model": "qwen2.5:7b",
        "seed": 42,
    },
    "notion": {
        "enabled": False,
        "database_id": None,  # token is read from NOTION_TOKEN env var
        "properties": {
            "title": "Role",
            "company": "Company",
            "url": "URL",
            "status": "Status",
            "score": "Fit Score",
            "cv": "CV Version",
            "location": "Location",
        },
    },
}


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: str | Path | None = "config.yaml") -> dict:
    if path and Path(path).exists():
        with open(path, encoding="utf-8") as f:
            return _merge(DEFAULTS, yaml.safe_load(f) or {})
    return copy.deepcopy(DEFAULTS)
