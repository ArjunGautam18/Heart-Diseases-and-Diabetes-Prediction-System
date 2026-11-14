"""
STEP 1: Load and inspect the heart disease dataset
"""
import pandas as pd

from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'heart_disease_uci.csv'
df = pd.read_csv(DATA_PATH)

# Basic shape and structure
print("Shape (rows, columns):", df.shape)
print("\nColumn data types:")
print(df.dtypes)

# Preview first few rows
print("\nFirst 5 rows:")
print(df.head())

# Missing values per column
print("\nMissing values per column:")
print(df.isna().sum())

# Missing values as a percentage
print("\nMissing values (%):")
print((df.isna().mean() * 100).round(1))

# How many collection sites, and target class balance
print("\nCollection sites (dataset column):")
print(df['dataset'].value_counts())

print("\nTarget ('num') distribution (0=no disease, 1-4=severity levels):")
print(df['num'].value_counts().sort_index())

