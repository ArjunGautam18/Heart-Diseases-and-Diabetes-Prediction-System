"""
STEP 1 (Diabetes): Load and inspect the diabetes dataset
"""

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "diabetes_prediction_dataset.csv"
df = pd.read_csv(DATA_PATH)

print("Shape (rows, columns):", df.shape)
print("\nColumn data types:")
print(df.dtypes)

print("\nFirst 5 rows:")
print(df.head())

print("\nStandard missing values (df.isna()) – expect all zero:")
print(df.isna().sum())

print("\nGender value counts:")
print(df["gender"].value_counts())

print("\nSmoking history value counts:")
print(df["smoking_history"].value_counts())

print("\nTarget (diabetes) distribution:")
print(df["diabetes"].value_counts())
print(df["diabetes"].value_counts(normalize=True).round(3))

print("\nBasic statistics:")
print(df.describe())