import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
print(os.getcwd())  # Prints the current working directory
# Load dataset (assuming a CSV file)
df = pd.read_csv("UPI_Fraud_Detection_Project/data/processed_upi_transactions.csv")

# Handle missing values
df.fillna(method='ffill', inplace=True)  # Forward fill missing values

# Remove duplicate entries
df.drop_duplicates(inplace=True)

# Normalize transaction amount using Min-Max scaling
scaler = MinMaxScaler()
df['normalized_amount'] = scaler.fit_transform(df[['transaction_amount']])

# Feature Engineering: Creating transaction frequency feature
df['transaction_count'] = df.groupby('user_id')['user_id'].transform('count')

# Convert categorical data (merchant ID, user ID) into numerical format
df['merchant_id'] = df['merchant_id'].astype('category').cat.codes
df['user_id'] = df['user_id'].astype('category').cat.codes

# Save preprocessed data to a new file
df.to_csv("processed_upi_transactions.csv", index=False)

print("Data preprocessing complete. Processed file saved as 'processed_upi_transactions.csv'.")