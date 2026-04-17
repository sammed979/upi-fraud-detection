import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH  = BASE_DIR / "data" / "fraud_detection.db"
DB_PATH.parent.mkdir(exist_ok=True)

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id             INTEGER,
            merchant_id         INTEGER,
            transaction_amount  REAL,
            hour_of_day         INTEGER,
            normalized_amount   REAL,
            transaction_count   INTEGER,
            fraud_prediction    INTEGER,
            anomaly_prediction  INTEGER,
            fraud_score         REAL,
            risk_level          TEXT,
            source              TEXT DEFAULT 'manual',
            razorpay_payment_id TEXT,
            timestamp           DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_transaction(data: dict):
    conn = get_connection()
    conn.execute("""
        INSERT INTO transactions
            (user_id, merchant_id, transaction_amount, hour_of_day,
             normalized_amount, transaction_count, fraud_prediction,
             anomaly_prediction, fraud_score, risk_level, source, razorpay_payment_id)
        VALUES
            (:user_id, :merchant_id, :transaction_amount, :hour_of_day,
             :normalized_amount, :transaction_count, :fraud_prediction,
             :anomaly_prediction, :fraud_score, :risk_level, :source, :razorpay_payment_id)
    """, data)
    conn.commit()
    conn.close()

def get_all_transactions(limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return rows

def get_stats():
    conn = get_connection()
    total  = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    fraud  = conn.execute("SELECT COUNT(*) FROM transactions WHERE fraud_prediction=1").fetchone()[0]
    today  = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE DATE(timestamp)=DATE('now')"
    ).fetchone()[0]
    conn.close()
    return {"total": total, "fraud": fraud, "today": today}

if __name__ == "__main__":
    init_db()
