"""
STEP 4: Impute missing values, per collection site
Builds on data/processed/heart_step3.csv from step 3.
"""
from pathlib import Path
import pandas as pd
import numpy as np

IN_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step3.csv'
df = pd.read_csv(IN_PATH)

# Numeric columns: fill with the MEDIAN, computed within each site (dataset).
num_cols = ['trestbps', 'chol', 'thalch', 'oldpeak', 'ca']
for col in num_cols:
    df[col] = df.groupby('dataset')[col].transform(lambda s: s.fillna(s.median()))
    # Fallback: if a whole site has no values for this column, use the global median
    df[col] = df[col].fillna(df[col].median())

# Categorical / binary columns: fill with the MODE, computed within each site.
cat_cols = ['fbs', 'restecg', 'exang', 'slope', 'thal']
for col in cat_cols:
    df[col] = df.groupby('dataset')[col].transform(
        lambda s: s.fillna(s.mode()[0] if not s.mode().empty else np.nan)
    )
    df[col] = df[col].fillna(df[col].mode()[0])

# Sanity check: no missing values should remain in the original feature columns
original_cols = ['age','sex','dataset','cp','trestbps','chol','fbs','restecg',
                  'thalch','exang','oldpeak','slope','ca','thal']
print("Remaining missing values per column:")
print(df[original_cols].isna().sum())
print("\nTotal remaining missing values:", df[original_cols].isna().sum().sum())

print("\nShape after imputation:", df.shape)

# Save intermediate result for step 5 (feature engineering) to build on
OUT_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step4.csv'
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved to {OUT_PATH}")