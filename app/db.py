import sqlite3
from app.config import settings

DB_PATH = settings.data_dir / "stream_shorts.sqlite3"

def connect():
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source_url TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'queued',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          error TEXT
        );
        CREATE TABLE IF NOT EXISTS clips (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          job_id INTEGER NOT NULL,
          title TEXT,
          start_seconds REAL NOT NULL,
          end_seconds REAL NOT NULL,
          file_path TEXT NOT NULL,
          transcript TEXT,
          status TEXT NOT NULL DEFAULT 'review',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(job_id) REFERENCES jobs(id)
        );
        """)
