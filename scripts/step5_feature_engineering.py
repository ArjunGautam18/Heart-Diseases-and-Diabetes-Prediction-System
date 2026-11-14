"""
STEP 5: Feature engineering
Builds on data/processed/heart_step4.csv from step 4.
"""
from pathlib import Path
import pandas as pd
import numpy as np

IN_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step4.csv'
df = pd.read_csv(IN_PATH)

# Age groups — captures non-linear age effects a raw number might miss
df['age_group'] = pd.cut(df['age'], bins=[0, 40, 50, 60, 70, 100],
                          labels=['<40', '40-50', '50-60', '60-70', '70+'])

# Cholesterol relative to age — raw cholesterol reads differently at 30 vs 70
df['chol_per_age'] = df['chol'] / df['age']

# Heart-rate reserve: standard cardiology estimate (220 - age) minus measured max HR.
# A small reserve during a stress test is a classic risk indicator.
df['max_hr_reserve'] = 220 - df['age'] - df['thalch']

# Resting blood pressure relative to cholesterol
df['bp_chol_ratio'] = df['trestbps'] / df['chol'].replace(0, np.nan)
df['bp_chol_ratio'] = df['bp_chol_ratio'].fillna(df['bp_chol_ratio'].median())

# Flag for significant ST depression (oldpeak >= 2 is a commonly used clinical cutoff)
df['high_oldpeak'] = (df['oldpeak'] >= 2).astype(int)

# Flag for any major vessel blocked (ca > 0), simpler signal than the raw count
df['ca_present'] = (df['ca'] > 0).astype(int)

print("New columns added:")
new_cols = ['age_group', 'chol_per_age', 'max_hr_reserve', 'bp_chol_ratio',
            'high_oldpeak', 'ca_present']
print(df[new_cols].head())

print("\nShape after feature engineering:", df.shape)

# Save intermediate result for step 6 (encoding) to build on
OUT_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step5.csv'
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved to {OUT_PATH}")