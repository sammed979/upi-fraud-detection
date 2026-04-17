"""
model.py
--------
Generates a synthetic fraud dataset and trains a RandomForestClassifier.
Run this once before starting the Flask app:
    python model.py
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle

np.random.seed(42)
N = 5000

# ── Purpose encoding ──────────────────────────────────────────────────────────
# 0=education, 1=shopping, 2=friend/family, 3=unknown
purpose = np.random.choice([0, 1, 2, 3], N, p=[0.2, 0.3, 0.3, 0.2])

amount       = np.random.exponential(scale=3000, size=N).clip(10, 100000)
new_receiver = np.random.choice([0, 1], N, p=[0.6, 0.4])
reported     = np.random.choice([0, 1], N, p=[0.95, 0.05])

# ── Rule-based fraud label (ground truth for training) ────────────────────────
score = np.zeros(N)
score += new_receiver * 30
score += (amount > 10000) * 20
score += (purpose == 3) * 25          # unknown purpose
score += reported * 50
score -= (purpose == 0) * 20          # education reduces risk
score -= (new_receiver == 0) * 15     # repeat receiver reduces risk
score += np.random.normal(0, 5, N)    # add noise
score = score.clip(0, 100)

fraud_label = (score >= 50).astype(int)

df = pd.DataFrame({
    "amount":       amount.round(2),
    "new_receiver": new_receiver,
    "purpose":      purpose,
    "reported":     reported,
    "fraud_label":  fraud_label,
})

# ── Train model ───────────────────────────────────────────────────────────────
FEATURES = ["amount", "new_receiver", "purpose", "reported"]
X = df[FEATURES]
y = df["fraud_label"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(n_estimators=200, max_depth=8,
                                random_state=42, class_weight="balanced")
model.fit(X_train, y_train)

print(classification_report(y_test, model.predict(X_test),
                             target_names=["Legit", "Fraud"]))

# ── Save model ────────────────────────────────────────────────────────────────
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("[OK] model.pkl saved")
