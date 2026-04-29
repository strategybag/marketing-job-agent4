
import sqlite3
from pathlib import Path
from typing import Dict, Any
import pandas as pd

DB_PATH = Path("data/jobs.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        company TEXT,
        title TEXT,
        location TEXT,
        url TEXT UNIQUE,
        description TEXT,
        score INTEGER,
        recommendation TEXT,
        reasons TEXT,
        status TEXT DEFAULT 'New',
        tailored_resume TEXT,
        cover_letter TEXT,
        recruiter_note TEXT,
        notes TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS scan_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source_count INTEGER,
        raw_jobs_found INTEGER,
        new_jobs_saved INTEGER,
        high_fit_jobs INTEGER,
        errors TEXT
    )
    """)
    conn.commit()
    conn.close()

def job_exists(url: str) -> bool:
    init_db()
    if not url:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id FROM jobs WHERE url = ?", (url,))
    row = cur.fetchone()
    conn.close()
    return row is not None

def add_job(job: Dict[str, Any]) -> int | None:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("""
        INSERT INTO jobs (
            company, title, location, url, description, score, recommendation, reasons,
            tailored_resume, cover_letter, recruiter_note, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("company"),
            job.get("title"),
            job.get("location"),
            job.get("url"),
            job.get("description"),
            job.get("score"),
            job.get("recommendation"),
            "\n".join(job.get("reasons", [])) if isinstance(job.get("reasons"), list) else job.get("reasons"),
            job.get("tailored_resume"),
            job.get("cover_letter"),
            job.get("recruiter_note"),
            job.get("notes")
        ))
        conn.commit()
        job_id = cur.lastrowid
    except sqlite3.IntegrityError:
        job_id = None
    finally:
        conn.close()
    return job_id

def list_jobs() -> pd.DataFrame:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM jobs ORDER BY created_at DESC", conn)
    conn.close()
    return df

def update_status(job_id: int, status: str, notes: str = ""):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE jobs SET status = ?, notes = ? WHERE id = ?", (status, notes, job_id))
    conn.commit()
    conn.close()

def log_scan(source_count: int, raw_jobs_found: int, new_jobs_saved: int, high_fit_jobs: int, errors: list[str]):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO scan_runs (source_count, raw_jobs_found, new_jobs_saved, high_fit_jobs, errors)
    VALUES (?, ?, ?, ?, ?)
    """, (source_count, raw_jobs_found, new_jobs_saved, high_fit_jobs, "\n".join(errors)))
    conn.commit()
    conn.close()

def list_scan_runs() -> pd.DataFrame:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM scan_runs ORDER BY started_at DESC LIMIT 50", conn)
    conn.close()
    return df
