"""Collect jobs from job boards (via JobSpy) or from a file of links."""
from __future__ import annotations

import csv
from pathlib import Path

from .models import Job


def from_jobspy(cfg: dict) -> list[Job]:
    """Search job boards with JobSpy (https://github.com/speedyapply/JobSpy).

    Keep volumes low: LinkedIn's terms forbid scraping and it rate-limits hard.
    """
    from jobspy import scrape_jobs  # optional dependency

    s = cfg["search"]
    jobs: list[Job] = []
    for term in s["terms"]:
        for loc in s["locations"]:
            df = scrape_jobs(
                site_name=s["sites"],
                search_term=term,
                location=loc,
                results_wanted=s["results_per_search"],
                hours_old=s["hours_old"],
                country_indeed=loc,
                linkedin_fetch_description=True,
            )
            for row in df.fillna("").to_dict("records"):
                url = row.get("job_url_direct") or row.get("job_url")
                if not url:
                    continue
                jobs.append(Job(
                    url=url,
                    title=str(row.get("title", "")),
                    company=str(row.get("company", "")),
                    location=str(row.get("location", "")),
                    country=loc,
                    description=str(row.get("description", "")),
                    source=str(row.get("site", "jobspy")),
                ))
    return jobs


def from_file(path: str | Path) -> list[Job]:
    """Load jobs from a .txt (one URL per line) or .csv file.

    CSV columns (all optional except url): url,title,company,location,country,description
    """
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with open(path, encoding="utf-8-sig") as f:
            return [
                Job(**{k: (row.get(k) or "") for k in
                       ("url", "title", "company", "location", "country", "description")},
                    source="file")
                for row in csv.DictReader(f) if row.get("url")
            ]
    lines = path.read_text(encoding="utf-8").splitlines()
    return [Job(url=l.strip(), source="file") for l in lines
            if l.strip() and not l.lstrip().startswith("#")]
