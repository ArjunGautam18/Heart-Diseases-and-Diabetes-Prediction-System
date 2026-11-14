"""
STEP 2 (Diabetes): Create missing flags

Note: This dataset has NO true missing values (isna() is all zero).
'No Info' in smoking_history is a category, not missing.
We still create flag columns for consistency with the heart disease pipeline.
"""

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "diabetes_prediction_dataset.csv"
df = pd.read_csv(DATA_PATH)

# This dataset has no real missing values
print("True missing values (isna):")
print(df.isna().sum())

# Create flags anyway (all will be 0) – keeps pipeline consistent
# We also flag the 'No Info' category as a special case
df["smoking_no_info_flag"] = (df["smoking_history"] == "No Info").astype(int)

print("\nCreated flag columns:")
print(df[["smoking_history", "smoking_no_info_flag"]].head(10))

print("\nFlag distribution:")
print(df["smoking_no_info_flag"].value_counts())

# Save
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_with_flags.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved → {OUT_PATH}")