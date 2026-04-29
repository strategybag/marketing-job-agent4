import streamlit as st
import pandas as pd
from agent.scoring import score_job
from agent.generator import ai_outputs
from agent.db import init_db, add_job, list_jobs, update_status
from agent.sources import fetch_text_from_url, parse_greenhouse_board, parse_ashby_board, parse_company_careers, parse_lever_board, parse_smartrecruiters_board
from agent.automation import run_scan
from agent.db import list_scan_runs

st.set_page_config(page_title="Marketing Leadership Job Copilot", layout="wide")

init_db()

st.title("Marketing Leadership Job Application Copilot")
st.caption("AI-assisted discovery, fit scoring, tailored materials, and human-approved application tracking.")

tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["Dashboard", "Add Job", "Import Boards", "Application Tracker", "Automation", "Settings"])


with tab0:
    st.subheader("Executive Dashboard")
    df = list_jobs()

    if df.empty:
        st.info("No jobs have been added yet. Add or import jobs to populate the dashboard.")
    else:
        total_jobs = len(df)
        applied_jobs = int((df["status"] == "Applied").sum()) if "status" in df else 0
        interview_jobs = int((df["status"] == "Interview").sum()) if "status" in df else 0
        avg_score = round(float(df["score"].fillna(0).mean()), 1)
        apply_ready = int((df["recommendation"] == "Apply").sum()) if "recommendation" in df else 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total roles", total_jobs)
        c2.metric("Apply-ready roles", apply_ready)
        c3.metric("Average fit score", avg_score)
        c4.metric("Applied", applied_jobs)
        c5.metric("Interviews", interview_jobs)

        st.markdown("### Pipeline by status")
        status_counts = (
            df["status"]
            .fillna("New")
            .value_counts()
            .rename_axis("Status")
            .reset_index(name="Count")
        )
        st.bar_chart(status_counts.set_index("Status"))

        st.markdown("### Fit score distribution")
        score_df = df[["id", "company", "title", "score"]].copy()
        score_df["score"] = score_df["score"].fillna(0)
        st.bar_chart(score_df.set_index("id")["score"])

        st.markdown("### Recommendations")
        rec_counts = (
            df["recommendation"]
            .fillna("Unscored")
            .value_counts()
            .rename_axis("Recommendation")
            .reset_index(name="Count")
        )
        st.dataframe(rec_counts, use_container_width=True)

        st.markdown("### Highest-fit opportunities")
        top_roles = df.sort_values("score", ascending=False).head(10)
        st.dataframe(
            top_roles[["id", "company", "title", "location", "score", "recommendation", "status", "url"]],
            use_container_width=True
        )

        st.markdown("### Companies with most tracked roles")
        company_counts = (
            df["company"]
            .fillna("Unknown")
            .value_counts()
            .head(10)
            .rename_axis("Company")
            .reset_index(name="Tracked Roles")
        )
        st.dataframe(company_counts, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download full dashboard data",
            data=csv,
            file_name="marketing_job_dashboard_data.csv",
            mime="text/csv"
        )

with tab1:
    st.subheader("Add a job posting")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("Company")
        title = st.text_input("Job title")
        location = st.text_input("Location / work model")
        url = st.text_input("Job URL")
    with col2:
        auto_fetch = st.checkbox("Fetch description from URL", value=False)
        description = st.text_area("Job description", height=260)

    if auto_fetch and url and st.button("Fetch URL text"):
        try:
            description = fetch_text_from_url(url)
            st.success("Fetched page text. Review before scoring.")
            st.text_area("Fetched description", value=description, height=260)
        except Exception as e:
            st.error(f"Could not fetch URL: {e}")

    if st.button("Score and generate materials", type="primary"):
        if not title or not company or not description:
            st.error("Company, title, and job description are required.")
        else:
            scored = score_job(title, company, location, description)
            outputs = ai_outputs(
                title=title,
                company=company,
                location=location,
                description=description,
                score=scored["score"],
                score_reasons=scored["reasons"]
            )
            job = {
                "company": company,
                "title": title,
                "location": location,
                "url": url,
                "description": description,
                "score": scored["score"],
                "recommendation": scored["recommendation"],
                "reasons": scored["reasons"],
                "tailored_resume": outputs.get("tailored_resume"),
                "cover_letter": outputs.get("cover_letter"),
                "recruiter_note": outputs.get("recruiter_note"),
            }
            job_id = add_job(job)
            st.success(f"Saved job #{job_id}. Recommendation: {scored['recommendation']} | Score: {scored['score']}")

            st.markdown("### Fit reasons")
            for r in scored["reasons"]:
                st.write(f"- {r}")

            st.markdown("### Tailored resume direction")
            st.text_area("Tailored resume", outputs.get("tailored_resume", ""), height=250)

            st.markdown("### Cover letter")
            st.text_area("Cover letter", outputs.get("cover_letter", ""), height=250)

            st.markdown("### Recruiter note")
            st.text_area("Recruiter note", outputs.get("recruiter_note", ""), height=180)

with tab2:
    st.subheader("Import from public job boards")
    st.write("Use public board tokens only. This imports job descriptions for scoring and review; it does not auto-apply.")

    source = st.selectbox("Source", ["Greenhouse", "Ashby", "Lever", "SmartRecruiters", "Company Websites"])
    token = st.text_input("Board token / organization slug")
    urls_input = ""
    if source == "Company Websites":
        urls_input = st.text_area("Enter company career page URLs, one per line", placeholder="https://company.com/careers\nhttps://another.com/jobs")
    min_score = st.slider("Minimum score to save", min_value=0, max_value=100, value=70)

    if st.button("Import and score"):
        if not token:
            st.error("Enter a board token or organization slug.")
        else:
            try:
                if source == "Greenhouse":
                    jobs = parse_greenhouse_board(token)
                elif source == "Ashby":
                    jobs = parse_ashby_board(token)
                elif source == "Lever":
                    jobs = parse_lever_board(token)
                elif source == "SmartRecruiters":
                    jobs = parse_smartrecruiters_board(token)
                elif source == "Company Websites":
                    jobs = []
                    urls = [u.strip() for u in urls_input.split("\n") if u.strip()]
                    for u in urls:
                        jobs.extend(parse_company_careers(u))
                else:
                    jobs = []
                saved = 0
                results = []
                for j in jobs:
                    scored = score_job(j["title"], j["company"], j["location"], j["description"])
                    results.append({
                        "title": j["title"],
                        "location": j["location"],
                        "score": scored["score"],
                        "recommendation": scored["recommendation"],
                        "url": j["url"]
                    })
                    if scored["score"] >= min_score:
                        outputs = ai_outputs(
                            title=j["title"],
                            company=j["company"],
                            location=j["location"],
                            description=j["description"],
                            score=scored["score"],
                            score_reasons=scored["reasons"]
                        )
                        add_job({
                            **j,
                            "score": scored["score"],
                            "recommendation": scored["recommendation"],
                            "reasons": scored["reasons"],
                            "tailored_resume": outputs.get("tailored_resume"),
                            "cover_letter": outputs.get("cover_letter"),
                            "recruiter_note": outputs.get("recruiter_note"),
                        })
                        saved += 1

                st.success(f"Imported {len(jobs)} jobs and saved {saved}.")
                st.dataframe(pd.DataFrame(results), use_container_width=True)
            except Exception as e:
                st.error(f"Import failed: {e}")

with tab3:
    st.subheader("Application tracker")
    df = list_jobs()

    if df.empty:
        st.info("No jobs saved yet.")
    else:
        st.dataframe(
            df[["id", "created_at", "company", "title", "location", "score", "recommendation", "status", "url"]],
            use_container_width=True
        )

        selected_id = st.number_input("Job ID to update/view", min_value=1, step=1)
        status = st.selectbox("Status", ["New", "Review", "Approved to Apply", "Applied", "Followed Up", "Interview", "Rejected", "Closed"])
        notes = st.text_area("Notes")
        if st.button("Update status"):
            update_status(int(selected_id), status, notes)
            st.success("Status updated.")

        selected = df[df["id"] == int(selected_id)]
        if not selected.empty:
            row = selected.iloc[0]
            st.markdown(f"### {row['title']} — {row['company']}")
            st.write(f"Score: {row['score']} | Recommendation: {row['recommendation']} | Status: {row['status']}")
            if row["url"]:
                st.link_button("Open job posting", row["url"])
            st.markdown("#### Reasons")
            st.text(row["reasons"] or "")
            st.markdown("#### Tailored resume")
            st.text_area("Resume direction", row["tailored_resume"] or "", height=250)
            st.markdown("#### Cover letter")
            st.text_area("Cover letter draft", row["cover_letter"] or "", height=250)
            st.markdown("#### Recruiter note")
            st.text_area("Recruiter note draft", row["recruiter_note"] or "", height=180)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download tracker CSV", data=csv, file_name="application_tracker.csv", mime="text/csv")


with tab4:
    st.subheader("Automation")
    st.write("Run scans manually here, or install the included daily scheduler script.")

    if st.button("Run automated scan now", type="primary"):
        try:
            result = run_scan()
            st.success(
                f"Scan complete: {result['new_jobs_saved']} new saved roles, "
                f"{result['high_fit_jobs']} high-fit alerts."
            )
            st.json({
                "sources_checked": result["source_count"],
                "raw_jobs_found": result["raw_jobs_found"],
                "new_jobs_saved": result["new_jobs_saved"],
                "high_fit_jobs": result["high_fit_jobs"],
                "alert_file": result["alert_file"],
                "errors": result["errors"]
            })
        except Exception as e:
            st.error(f"Automation failed: {e}")

    st.markdown("### Watchlist")
    try:
        watchlist_text = open("data/watchlist.json", "r", encoding="utf-8").read()
        updated_watchlist = st.text_area("Edit watchlist JSON", value=watchlist_text, height=320)
        if st.button("Save watchlist"):
            import json
            parsed = json.loads(updated_watchlist)
            open("data/watchlist.json", "w", encoding="utf-8").write(json.dumps(parsed, indent=2))
            st.success("Watchlist saved.")
    except Exception as e:
        st.error(f"Could not load watchlist: {e}")

    st.markdown("### Recent scan runs")
    try:
        scans = list_scan_runs()
        if scans.empty:
            st.info("No scan history yet.")
        else:
            st.dataframe(scans, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load scan runs: {e}")

    st.markdown("### Daily scheduler install commands")

    st.write("Windows PowerShell:")
    st.code(r".\install_windows_daily_task.ps1", language="powershell")

    st.write("Mac or Linux:")
    st.code("chmod +x install_mac_linux_cron.sh\n./install_mac_linux_cron.sh", language="bash")


with tab5:
    st.subheader("Settings and profile")
    st.write("Edit these files to customize the system:")
    st.code("""
data/master_resume.txt
data/achievement_library.txt
agent/profile.py
.env
""")
    st.warning("Keep final submission manual for LinkedIn, Indeed, and leadership applications. This protects quality and reduces platform compliance risk.")
