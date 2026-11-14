"""
STEP 3: Flag missingness before imputing
Builds on data/processed/heart_step2.csv from step 2.
"""
from pathlib import Path
import pandas as pd

IN_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step2.csv'
df = pd.read_csv(IN_PATH)

# Columns that have missing values (from step 1's inspection)
cols_with_missing = ['trestbps', 'chol', 'fbs', 'restecg',
                      'thalch', 'exang', 'oldpeak', 'slope', 'ca', 'thal']

# Add a "<col>_missing" indicator column for each — 1 if missing, 0 if present.
# Do this BEFORE any imputation, since imputing first would erase the signal.
for col in cols_with_missing:
    df[f'{col}_missing'] = df[col].isna().astype(int)

# Sanity check: print how many rows are flagged missing per column,
# and confirm it matches step 1's numbers.
print("Missing counts (should match Step 1's numbers):")
for col in cols_with_missing:
    print(f"  {col}: {df[f'{col}_missing'].sum()}")

print("\nShape after adding missing-flag columns:", df.shape)

# Save intermediate result for step 4 (imputation) to build on
OUT_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step3.csv'
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved to {OUT_PATH}")