import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib
from pathlib import Path

BASE_DIR    = Path(__file__).resolve().parent.parent
DATA_DIR    = BASE_DIR / "data"
MODEL_DIR   = BASE_DIR / "models"
RESULTS_DIR = BASE_DIR / "results"
MODEL_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_DIR / "processed_upi_transactions.csv")

FEATURES = ["normalized_amount", "transaction_count", "merchant_id", "user_id", "hour_of_day"]
X = df[FEATURES]

model = IsolationForest(n_estimators=200, contamination=0.07, random_state=42)
df["anomaly_score"] = model.fit_predict(X)  # -1 = anomaly, 1 = normal

joblib.dump(model, MODEL_DIR / "anomaly_detection_model.pkl")
print(f"[OK] Anomaly model saved -> {MODEL_DIR / 'anomaly_detection_model.pkl'}")

anomalies = df[df["anomaly_score"] == -1]
out = RESULTS_DIR / "fraudulent_transactions.csv"
anomalies.to_csv(out, index=False)
print(f"[INFO] {len(anomalies)} anomalies detected -> {out}")
