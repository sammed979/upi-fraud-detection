import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR  = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_DIR / "upi_transactions.csv")

df.ffill(inplace=True)
df.drop_duplicates(inplace=True)

# Normalize transaction amount — save scaler for inference
scaler = MinMaxScaler()
df["normalized_amount"] = scaler.fit_transform(df[["transaction_amount"]])
joblib.dump(scaler, MODEL_DIR / "amount_scaler.pkl")

# Transaction velocity per user
df["transaction_count"] = df.groupby("user_id")["user_id"].transform("count")

# Encode IDs
df["merchant_id"] = df["merchant_id"].astype("category").cat.codes
df["user_id"]     = df["user_id"].astype("category").cat.codes

out = DATA_DIR / "processed_upi_transactions.csv"
df.to_csv(out, index=False)
print(f"[OK] Preprocessing complete -> {out}")
print(f"   Shape: {df.shape} | Fraud rate: {df['is_fraud'].mean()*100:.1f}%")
