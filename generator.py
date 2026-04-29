import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""

def fallback_outputs(title: str, company: str, description: str, score_reasons: list[str]) -> dict:
    master_resume = read_text("data/master_resume.txt")
    achievements = read_text("data/achievement_library.txt")

    fit_points = "\n".join([f"- {r}" for r in score_reasons]) or "- Strong marketing leadership fit."

    cover_letter = f"""
Dear Hiring Team,

I am interested in the {title} role at {company}. My background includes more than 20 years of marketing leadership across brand strategy, field marketing, customer acquisition, loyalty, retail, digital marketing, and portfolio growth.

This opportunity appears aligned for the following reasons:
{fit_points}

At Par Pacific, I led brand marketing and loyalty initiatives that increased retail brand awareness, grew sales to approximately $57 million, launched mobile app and loyalty campaigns, and created measurable savings by modernizing the loyalty experience. I have also led large-scale brand strategy and acquisition work at ExxonMobil and Direct Energy, including omnichannel marketing, agency leadership, sponsorships, and performance-driven growth.

I would welcome the opportunity to discuss how my experience building brands, leading teams, and translating marketing strategy into measurable growth could support {company}.

Best regards,
Brian Gray
""".strip()

    recruiter_note = f"""
Hi,

I saw the {title} opportunity at {company} and wanted to reach out directly. My background includes senior marketing leadership across brand strategy, field marketing, loyalty, mobile app growth, customer acquisition, and multi-location retail growth.

At Par Pacific, I led brand and loyalty initiatives that increased awareness, supported sales growth to approximately $57 million, and generated more than 150,000 mobile app downloads. I would welcome the opportunity to connect if this role is still active.

Best,
Brian Gray
""".strip()

    tailored_resume = f"""
TAILORED RESUME DIRECTION FOR: {title} — {company}

Recommended positioning:
Senior marketing executive with deep experience in brand strategy, field marketing, loyalty, customer acquisition, mobile app growth, retail marketing, and cross-functional leadership.

Top proof points to emphasize:
- Increased retail brand awareness by approximately 20%.
- Grew sales by approximately 15% to $57 million.
- Launched loyalty and mobile app campaigns generating more than 150,000 downloads.
- Created approximately $300,000 annual savings by modernizing loyalty infrastructure.
- Managed marketing teams, agency partners, and cross-functional stakeholders.
- Improved customer acquisition by approximately 12% and reduced marketing costs by approximately 15% at Direct Energy.

Master resume source:
{master_resume[:3000]}

Achievement source:
{achievements[:2000]}
""".strip()

    return {
        "tailored_resume": tailored_resume,
        "cover_letter": cover_letter,
        "recruiter_note": recruiter_note
    }

def ai_outputs(title: str, company: str, location: str, description: str, score: int, score_reasons: list[str]) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    if not api_key:
        return fallback_outputs(title, company, description, score_reasons)

    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    master_resume = read_text("data/master_resume.txt")
    achievements = read_text("data/achievement_library.txt")

    prompt = f"""
You are an executive resume and job-search assistant.

Candidate: Brian Gray, senior marketing leader.
Target role: {title}
Company: {company}
Location: {location}
Fit score: {score}
Fit reasons: {score_reasons}

Job description:
{description}

Master resume:
{master_resume}

Achievement library:
{achievements}

Create three outputs:
1. Tailored resume direction with revised executive summary and prioritized bullet points.
2. Concise cover letter.
3. Short recruiter outreach note.

Constraints:
- Do not invent employers, degrees, certifications, or metrics.
- Preserve only supported metrics.
- Emphasize brand strategy, field marketing, loyalty, customer acquisition, mobile app growth, retail, revenue growth, and leadership when relevant.
- Use plain labels: TAILORED RESUME, COVER LETTER, RECRUITER NOTE.
"""

    response = client.responses.create(
        model=model,
        input=prompt
    )
    text = response.output_text

    return {
        "tailored_resume": extract_section(text, "TAILORED RESUME", "COVER LETTER"),
        "cover_letter": extract_section(text, "COVER LETTER", "RECRUITER NOTE"),
        "recruiter_note": extract_section(text, "RECRUITER NOTE", None),
        "raw": text
    }

def extract_section(text: str, start: str, end: str | None) -> str:
    upper = text.upper()
    s = upper.find(start)
    if s == -1:
        return text.strip()
    e = upper.find(end, s + len(start)) if end else -1
    section = text[s:e if e != -1 else len(text)]
    return section.replace(start, "", 1).strip(" :-\n")
