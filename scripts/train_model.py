import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
import os
os.makedirs("models", exist_ok=True)  # Ensures the models folder exists

# Load preprocessed data
df = pd.read_csv("data/processed_upi_transactions.csv")

# Check if 'is_fraud' column exists
if 'is_fraud' not in df.columns:
    print("⚠️ 'is_fraud' column not found. Generating synthetic fraud labels.")
    df['is_fraud'] = np.random.choice([0, 1], size=len(df), p=[0.95, 0.05])  # 5% fraud transactions

# Define features and target
X = df[['normalized_amount', 'transaction_count', 'merchant_id', 'user_id']]
y = df['is_fraud']

# Split dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize and train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Make predictions and evaluate
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"✅ Model trained successfully! Accuracy: {accuracy:.2f}")

# Save trained model
joblib.dump(model, "models/upi_fraud_model.pkl")
print("✅ Model saved as 'models/upi_fraud_model.pkl'")

fraud_model_path = "D:/python/UPI_Fraud_Detection_Project/models/upi_fraud_model.pkl"
anomaly_model_path = "D:/python/UPI_Fraud_Detection_Project/models/anomaly_detection_model.pkl"

if os.path.exists(fraud_model_path):
    fraud_model = joblib.load(fraud_model_path)
else:
    print("⚠️ Fraud detection model file not found!")

if os.path.exists(anomaly_model_path):
    anomaly_model = joblib.load(anomaly_model_path)
else:
    print("⚠️ Anomaly detection model file not found!")