"""
STEP 6: Encode categorical columns
Builds on data/processed/heart_step5.csv from step 5.
"""
from pathlib import Path
import pandas as pd

IN_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step5.csv'
df = pd.read_csv(IN_PATH)

# Save the pre-encoding version too — useful for readable inspection/plots later
READABLE_OUT = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_cleaned_readable.csv'
df.to_csv(READABLE_OUT, index=False)
print(f"Saved human-readable (pre-encoding) version to {READABLE_OUT}")

# One-hot encode all categorical/text columns
cat_cols = ['sex', 'dataset', 'cp', 'restecg', 'slope', 'thal', 'age_group']
df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=True)

print("\nShape before encoding:", df.shape)
print("Shape after encoding:", df_encoded.shape)
print("\nNew dummy columns created:")
new_dummy_cols = [c for c in df_encoded.columns if c not in df.columns]
print(new_dummy_cols)

# Save the fully-encoded, model-ready dataset
OUT_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step6_encoded.csv'
df_encoded.to_csv(OUT_PATH, index=False)
print(f"\nSaved model-ready encoded data to {OUT_PATH}")