
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from agent.scoring import score_job
from agent.generator import ai_outputs
from agent.db import add_job, job_exists, log_scan
from agent.sources import (
    parse_greenhouse_board,
    parse_ashby_board,
    parse_company_careers,
    parse_lever_board,
    parse_smartrecruiters_board,
)

WATCHLIST_PATH = Path("data/watchlist.json")
ALERTS_DIR = Path("data/alerts")

def load_watchlist() -> Dict[str, Any]:
    if not WATCHLIST_PATH.exists():
        raise FileNotFoundError("Missing data/watchlist.json")
    return json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))

def fetch_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    source_type = source.get("type", "").lower()
    if source_type == "greenhouse":
        return parse_greenhouse_board(source["token"])
    if source_type == "ashby":
        return parse_ashby_board(source["token"])
    if source_type == "lever":
        return parse_lever_board(source["token"])
    if source_type == "smartrecruiters":
        return parse_smartrecruiters_board(source["token"])
    if source_type == "company":
        return parse_company_careers(source["url"])
    raise ValueError(f"Unsupported source type: {source_type}")

def run_scan() -> Dict[str, Any]:
    config = load_watchlist()
    min_save = int(config.get("minimum_score_to_save", 70))
    min_alert = int(config.get("minimum_score_for_alert", 80))
    generate_materials = bool(config.get("generate_materials_for_saved_jobs", True))
    sources = config.get("sources", [])

    raw_jobs_found = 0
    new_jobs_saved = 0
    high_fit_jobs = 0
    errors = []
    saved_jobs = []
    alert_jobs = []

    for source in sources:
        try:
            jobs = fetch_source(source)
            raw_jobs_found += len(jobs)

            for j in jobs:
                if not j.get("url") or job_exists(j.get("url")):
                    continue

                scored = score_job(
                    j.get("title", ""),
                    source.get("label") or j.get("company", ""),
                    j.get("location", ""),
                    j.get("description", "")
                )

                if scored["score"] < min_save:
                    continue

                outputs = {"tailored_resume": "", "cover_letter": "", "recruiter_note": ""}
                if generate_materials:
                    outputs = ai_outputs(
                        title=j.get("title", ""),
                        company=source.get("label") or j.get("company", ""),
                        location=j.get("location", ""),
                        description=j.get("description", ""),
                        score=scored["score"],
                        score_reasons=scored["reasons"]
                    )

                job_record = {
                    **j,
                    "company": source.get("label") or j.get("company", ""),
                    "score": scored["score"],
                    "recommendation": scored["recommendation"],
                    "reasons": scored["reasons"],
                    "tailored_resume": outputs.get("tailored_resume", ""),
                    "cover_letter": outputs.get("cover_letter", ""),
                    "recruiter_note": outputs.get("recruiter_note", ""),
                    "notes": f"Automated scan source: {source.get('label') or source.get('token') or source.get('url')}"
                }

                job_id = add_job(job_record)
                if job_id:
                    job_record["id"] = job_id
                    saved_jobs.append(job_record)
                    new_jobs_saved += 1

                    if scored["score"] >= min_alert:
                        high_fit_jobs += 1
                        alert_jobs.append(job_record)

        except Exception as e:
            errors.append(f"{source.get('label') or source}: {e}")

    log_scan(len(sources), raw_jobs_found, new_jobs_saved, high_fit_jobs, errors)
    alert_file = write_alert(alert_jobs, errors)

    return {
        "source_count": len(sources),
        "raw_jobs_found": raw_jobs_found,
        "new_jobs_saved": new_jobs_saved,
        "high_fit_jobs": high_fit_jobs,
        "errors": errors,
        "saved_jobs": saved_jobs,
        "alert_jobs": alert_jobs,
        "alert_file": str(alert_file) if alert_file else None
    }

def write_alert(alert_jobs: List[Dict[str, Any]], errors: List[str]) -> Path | None:
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = ALERTS_DIR / f"job_alert_{timestamp}.md"

    lines = [
        "# Marketing Leadership Job Alert",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"High-fit roles found: {len(alert_jobs)}",
        ""
    ]

    if alert_jobs:
        for job in sorted(alert_jobs, key=lambda x: x.get("score", 0), reverse=True):
            lines.extend([
                f"## {job.get('title')} — {job.get('company')}",
                "",
                f"- Score: {job.get('score')}",
                f"- Recommendation: {job.get('recommendation')}",
                f"- Location: {job.get('location')}",
                f"- URL: {job.get('url')}",
                "- Reasons:",
            ])
            for r in job.get("reasons", []):
                lines.append(f"  - {r}")
            lines.append("")

    if errors:
        lines.extend(["## Scan errors", ""])
        for e in errors:
            lines.append(f"- {e}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path

if __name__ == "__main__":
    result = run_scan()
    print(json.dumps(result, indent=2, default=str))
