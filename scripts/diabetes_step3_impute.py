"""
STEP 3 (Diabetes): Impute missing values

This dataset has ZERO true missing values, so no imputation is needed.
We keep the step for pipeline consistency.
"""

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_with_flags.csv"
df = pd.read_csv(DATA_PATH)

print("Missing values before imputation:")
print(df.isna().sum())

# No imputation required – just pass through
print("\nNo imputation performed (dataset has no missing values).")

# Optional: you could replace 'No Info' with mode if you want,
# but it is better treated as its own category later.

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_imputed.csv"
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved → {OUT_PATH}")