import pandas as pd
import numpy as np

# Generate synthetic transaction data
df = pd.DataFrame({
    'user_id': np.random.randint(1000, 2000, 100),
    'merchant_id': np.random.randint(200, 300, 100),
    'transaction_amount': np.random.uniform(50, 5000, 100),
    'transaction_time': pd.date_range(start='2024-01-01', periods=100, freq='H')
})

# Save to CSV
df.to_csv("data/upi_transactions.csv", index=False)

print("Sample dataset created: data/upi_transactions.csv")