import os

# Ensure 'models' and 'results' folders exist
os.makedirs("models", exist_ok=True)
os.makedirs("results", exist_ok=True)
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

# Ensure the 'models' folder exists
import os
os.makedirs("models", exist_ok=True)

# Load preprocessed data
df = pd.read_csv("UPI_Fraud_Detection_Project/data/processed_upi_transactions.csv")  # Full path

# Define features (excluding 'is_fraud' since this is anomaly detection)
X = df[['normalized_amount', 'transaction_count', 'merchant_id', 'user_id']]

# Initialize Isolation Forest for anomaly detection
model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
df['anomaly_score'] = model.fit_predict(X)  # -1: Anomaly, 1: Normal

# Save trained model
joblib.dump(model, "models/anomaly_detection_model.pkl")
print("✅ Anomaly detection model saved as 'models/anomaly_detection_model.pkl'")

# Show flagged anomalies
anomalies = df[df['anomaly_score'] == -1]
print(f"🔍 Detected {len(anomalies)} potential fraud transactions:")
print(anomalies.head())

# Save flagged anomalies for further analysis
anomalies.to_csv("results/fraudulent_transactions.csv", index=False)
print("✅ Fraudulent transactions saved to 'results/fraudulent_transactions.csv'")