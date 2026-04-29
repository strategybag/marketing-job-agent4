
# Marketing Leadership Job Application Copilot — Automated Version

A compliant AI-powered job search copilot for marketing leadership roles.

It automates:
- company watchlist scanning,
- Greenhouse, Ashby, Lever, SmartRecruiters, and company career page imports,
- fit scoring,
- saving high-fit roles,
- tailored resume direction,
- cover-letter drafts,
- recruiter outreach drafts,
- dashboard metrics,
- daily scheduled scanning,
- alert file generation.

It does **not** auto-submit applications to LinkedIn, Indeed, or other job boards. Final application submission remains manual.

## Setup

```bash
cd marketing_job_agent
python -m venv .venv
```

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

If script execution is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Mac or Linux

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Optional OpenAI setup

Edit `.env`:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o
```

Without an OpenAI key, the app still runs using fallback templates.

## Running one automated scan

```bash
python run_daily_scan.py
```

## Installing daily automation

### Windows

Run from PowerShell inside the project folder:

```powershell
.\install_windows_daily_task.ps1
```

This creates a Windows Scheduled Task called:

```text
MarketingJobAgentDailyScan
```

It runs daily at 8:00 AM.

### Mac or Linux

```bash
chmod +x install_mac_linux_cron.sh
./install_mac_linux_cron.sh
```

This adds a daily 8:00 AM cron job.

## Editing your company watchlist

Open:

```text
data/watchlist.json
```

Example:

```json
{
  "minimum_score_to_save": 70,
  "minimum_score_for_alert": 80,
  "generate_materials_for_saved_jobs": true,
  "sources": [
    {"type": "greenhouse", "token": "stripe", "label": "Stripe"},
    {"type": "ashby", "token": "air", "label": "Air"},
    {"type": "lever", "token": "zipline", "label": "Zipline"},
    {"type": "smartrecruiters", "token": "companyslug", "label": "Company Name"},
    {"type": "company", "url": "https://company.com/careers", "label": "Company Name"}
  ]
}
```

## Dashboard tabs

- Dashboard: executive pipeline overview
- Add Job: manually add one role
- Import Boards: import from selected sources
- Application Tracker: manage applications
- Automation: run scans, edit watchlist, view scan history
- Settings: edit profile files

## Alert files

High-fit alerts are saved here:

```text
data/alerts/
```

Each scan creates a markdown alert file.

## Recommended next upgrade

Connect Gmail so the system creates a draft email with high-fit roles every morning.
