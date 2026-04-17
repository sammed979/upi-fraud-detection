import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)
N = 5000

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

user_ids     = np.random.randint(1000, 2000, N)
merchant_ids = np.random.randint(200,  400,  N)
amounts      = np.random.exponential(scale=1500, size=N).clip(10, 50000)
raw_p = np.array([0.01,0.01,0.01,0.01,0.01,0.02,
                   0.04,0.06,0.07,0.07,0.06,0.06,
                   0.07,0.07,0.06,0.06,0.05,0.05,
                   0.05,0.04,0.04,0.03,0.02,0.02])
hour_p = raw_p / raw_p.sum()
hours  = np.random.choice(range(24), N, p=hour_p)
days  = np.random.randint(0, 365, N)
start = pd.Timestamp("2024-01-01")
times = [start + pd.Timedelta(days=int(d), hours=int(h)) for d, h in zip(days, hours)]

# Rule-based fraud labels (realistic patterns)
is_fraud = np.zeros(N, dtype=int)

# Pattern 1: very high amount at odd hours (midnight-4am)
is_fraud[(amounts > 15000) & (hours < 4)] = 1

# Pattern 2: rapid repeat — same user appears many times
user_series   = pd.Series(user_ids)
user_counts   = user_series.map(user_series.value_counts())
is_fraud[user_counts > 12] = 1

# Pattern 3: round large amounts (money mule pattern)
is_fraud[(amounts % 1000 < 5) & (amounts > 9000)] = 1

# Pattern 4: very small test transactions followed by large (card testing)
is_fraud[amounts < 15] = 1

# Add ~3% random noise fraud
noise_idx = np.random.choice(N, size=int(N * 0.03), replace=False)
is_fraud[noise_idx] = 1

df = pd.DataFrame({
    "user_id":            user_ids,
    "merchant_id":        merchant_ids,
    "transaction_amount": amounts.round(2),
    "transaction_time":   times,
    "hour_of_day":        hours,
    "is_fraud":           is_fraud
})

out = DATA_DIR / "upi_transactions.csv"
df.to_csv(out, index=False)
print(f"[OK] Dataset created: {out}")
print(f"   Total: {N} | Fraud: {is_fraud.sum()} ({is_fraud.mean()*100:.1f}%)")
