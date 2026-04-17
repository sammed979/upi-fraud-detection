"""
database.py
-----------
Handles all SQLite database operations.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "database.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS reported_upi_ids (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            upi_id      TEXT NOT NULL UNIQUE,
            reason      TEXT,
            reported_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS transaction_logs (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            upi_id       TEXT,
            amount       REAL,
            purpose      TEXT,
            new_receiver INTEGER,
            rule_score   REAL,
            ml_score     REAL,
            final_score  REAL,
            risk_level   TEXT,
            explanation  TEXT,
            checked_at   DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

def is_reported(upi_id: str) -> bool:
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM reported_upi_ids WHERE upi_id=?", (upi_id.lower(),)
    ).fetchone()
    conn.close()
    return row is not None

def report_upi(upi_id: str, reason: str):
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO reported_upi_ids (upi_id, reason) VALUES (?,?)",
            (upi_id.lower(), reason)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # already reported
    conn.close()

def log_transaction(data: dict):
    conn = get_conn()
    conn.execute("""
        INSERT INTO transaction_logs
            (upi_id, amount, purpose, new_receiver,
             rule_score, ml_score, final_score, risk_level, explanation)
        VALUES
            (:upi_id, :amount, :purpose, :new_receiver,
             :rule_score, :ml_score, :final_score, :risk_level, :explanation)
    """, data)
    conn.commit()
    conn.close()

def get_recent_logs(limit=20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM transaction_logs ORDER BY checked_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    init_db()
    print("[OK] Database initialized")
