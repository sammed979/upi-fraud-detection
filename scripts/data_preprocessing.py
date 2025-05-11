import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# Load dataset
df = pd.read_csv("UPI_Fraud_Detection_Project/data/processed_upi_transactions.csv")  # Full path

# Handle missing values
df.fillna(method='ffill', inplace=True)

# Remove duplicate entries
df.drop_duplicates(inplace=True)

# Normalize transaction amount
scaler = MinMaxScaler()
df['normalized_amount'] = scaler.fit_transform(df[['transaction_amount']])

# Feature Engineering: Transaction frequency
df['transaction_count'] = df.groupby('user_id')['user_id'].transform('count')

# Convert categorical data to numeric format
df['merchant_id'] = df['merchant_id'].astype('category').cat.codes
df['user_id'] = df['user_id'].astype('category').cat.codes

# Save processed data
df.to_csv("data/processed_upi_transactions.csv", index=False)

print("✅ Data preprocessing complete. Processed file saved as 'data/processed_upi_transactions.csv'.")