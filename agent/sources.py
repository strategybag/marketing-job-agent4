import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re

HEADERS = {
    "User-Agent": "MarketingJobCopilot/1.0"
}

def fetch_text_from_url(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()

def parse_greenhouse_board(board_token: str) -> List[Dict]:
    """
    Public Greenhouse job-board helper.
    Example board token: companyname from https://boards.greenhouse.io/companyname
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    jobs = []
    for j in data.get("jobs", []):
        jobs.append({
            "company": board_token,
            "title": j.get("title", ""),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "description": BeautifulSoup(j.get("content", ""), "html.parser").get_text(" ")
        })
    return jobs

def parse_ashby_board(org_slug: str) -> List[Dict]:
    """
    Public Ashby job-board helper.
    Example org slug from https://jobs.ashbyhq.com/orgslug
    """
    url = f"https://api.ashbyhq.com/posting-api/job-board/{org_slug}"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    jobs = []
    for j in data.get("jobs", []):
        jobs.append({
            "company": org_slug,
            "title": j.get("title", ""),
            "location": j.get("location", ""),
            "url": j.get("jobUrl", ""),
            "description": j.get("descriptionHtml", "")
        })
    return jobs


def parse_company_careers(url: str) -> List[Dict]:
    """
    Generic career page scraper.
    Best-effort parser for standard career pages. For JavaScript-heavy sites,
    use the direct Greenhouse, Ashby, Lever, or SmartRecruiters board URL when available.
    """
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []
    seen = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = re.sub(r"\s+", " ", link.get_text(" ", strip=True))

        href_l = href.lower()
        text_l = text.lower()

        looks_like_job = (
            any(k in href_l for k in ["job", "career", "position", "opening", "lever.co", "greenhouse.io", "ashbyhq.com", "smartrecruiters"])
            or any(k in text_l for k in ["director", "vice president", "vp", "head of", "chief marketing", "marketing", "brand", "growth"])
        )

        if not looks_like_job:
            continue

        if href.startswith("http"):
            full_url = href
        else:
            full_url = url.rstrip("/") + "/" + href.lstrip("/")

        if full_url in seen:
            continue
        seen.add(full_url)

        try:
            job_desc = fetch_text_from_url(full_url)
        except Exception:
            job_desc = text

        title = text if text else "Unknown Role"

        jobs.append({
            "company": url,
            "title": title[:180],
            "location": "",
            "url": full_url,
            "description": job_desc
        })

    return jobs


def parse_lever_board(company_slug: str) -> List[Dict]:
    """
    Public Lever postings helper.
    Example slug from https://jobs.lever.co/companyslug
    """
    url = f"https://api.lever.co/v0/postings/{company_slug}?mode=json"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    jobs = []
    for j in data:
        categories = j.get("categories") or {}
        jobs.append({
            "company": company_slug,
            "title": j.get("text", ""),
            "location": categories.get("location", ""),
            "url": j.get("hostedUrl", ""),
            "description": BeautifulSoup((j.get("description") or "") + " " + (j.get("descriptionPlain") or ""), "html.parser").get_text(" ")
        })
    return jobs


def parse_smartrecruiters_board(company_slug: str) -> List[Dict]:
    """
    Public SmartRecruiters postings helper.
    Example slug from https://jobs.smartrecruiters.com/companyslug
    """
    url = f"https://api.smartrecruiters.com/v1/companies/{company_slug}/postings"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    jobs = []
    for j in data.get("content", []):
        job_url = j.get("ref") or j.get("applyUrl") or ""
        desc = ""
        if j.get("ref"):
            try:
                detail = requests.get(j["ref"], headers=HEADERS, timeout=20).json()
                desc = detail.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", "")
            except Exception:
                desc = ""
        jobs.append({
            "company": company_slug,
            "title": j.get("name", ""),
            "location": (j.get("location") or {}).get("city", ""),
            "url": job_url,
            "description": BeautifulSoup(desc, "html.parser").get_text(" ")
        })
    return jobs
