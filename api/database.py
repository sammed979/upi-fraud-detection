import sqlite3
import os

# Ensure 'data' folder exists
os.makedirs("data", exist_ok=True)

# Create database connection
conn = sqlite3.connect("data/fraud_detection.db")
cursor = conn.cursor()

# Create transactions table
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    merchant_id INTEGER,
    transaction_amount REAL,
    fraud_prediction TEXT,
    anomaly_detection TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()
print("✅ Database initialized successfully!")