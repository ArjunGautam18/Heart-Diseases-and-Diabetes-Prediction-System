"""
STEP 2: Fix data types and define the prediction target
"""
from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'raw' / 'heart_disease_uci.csv'
df = pd.read_csv(DATA_PATH)

# --- Fix boolean-like columns that came in as TRUE/FALSE strings ---
df['fbs']   = df['fbs'].map({'TRUE': 1, 'FALSE': 0, True: 1, False: 0})
df['exang'] = df['exang'].map({'TRUE': 1, 'FALSE': 0, True: 1, False: 0})

# --- Drop the id column (not a predictive feature) ---
df = df.drop(columns=['id'])

# --- Define the prediction target ---
# 'num' is 0-4 (0 = no disease, 1-4 = increasing severity).
# Convert to binary: 0 = no disease, 1 = disease present.
df['target'] = (df['num'] > 0).astype(int)

print("fbs values after fix:", df['fbs'].unique())
print("exang values after fix:", df['exang'].unique())
print("\nTarget class balance:")
print(df['target'].value_counts(normalize=True).round(3))
print("\nShape after this step:", df.shape)

# Save intermediate result so the next step can pick up from here
OUT_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step2.csv'
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved to {OUT_PATH}")