import re
from typing import Dict, Any, List
from agent.profile import TARGET_PROFILE

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()

def contains_any(text: str, terms: List[str]) -> int:
    text_n = normalize(text)
    return sum(1 for term in terms if normalize(term) in text_n)

def score_job(title: str, company: str, location: str, description: str) -> Dict[str, Any]:
    full_text = " ".join([title or "", company or "", location or "", description or ""])
    text_n = normalize(full_text)

    score = 0
    reasons = []

    title_hits = contains_any(title, TARGET_PROFILE["target_titles"])
    if title_hits:
        score += 30
        reasons.append("Strong senior marketing leadership title match.")
    elif any(term in normalize(title) for term in ["marketing", "brand", "growth", "field"]):
        score += 18
        reasons.append("Relevant marketing title, but may not be fully senior.")

    keyword_hits = contains_any(full_text, TARGET_PROFILE["core_keywords"])
    keyword_score = min(keyword_hits * 4, 28)
    score += keyword_score
    if keyword_hits:
        reasons.append(f"Matched {keyword_hits} core marketing keywords.")

    industry_hits = contains_any(full_text, TARGET_PROFILE["preferred_industries"])
    industry_score = min(industry_hits * 5, 20)
    score += industry_score
    if industry_hits:
        reasons.append(f"Industry fit: matched {industry_hits} preferred industry signals.")

    location_hits = contains_any(location + " " + description, TARGET_PROFILE["preferred_locations"])
    if location_hits:
        score += 12
        reasons.append("Location or work model appears aligned.")

    if any(x in text_n for x in ["lead team", "manage team", "leadership team", "direct reports", "agency"]):
        score += 10
        reasons.append("Role appears to include leadership or agency management.")

    if any(x in text_n for x in ["salary", "compensation", "$", "bonus", "equity"]):
        score += 3
        reasons.append("Compensation details may be available.")

    score = min(score, 100)
    recommendation = "Apply" if score >= TARGET_PROFILE["minimum_score_to_queue"] else "Review" if score >= 60 else "Pass"

    return {
        "score": score,
        "recommendation": recommendation,
        "reasons": reasons
    }
