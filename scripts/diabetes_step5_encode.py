"""
STEP 5 (Diabetes): Encode categorical columns
"""

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_engineered.csv"
df = pd.read_csv(DATA_PATH)

# Collapse rare gender category (only 18 rows)
df["gender"] = df["gender"].replace({"Other": "Female"})

print("Gender after collapsing 'Other':")
print(df["gender"].value_counts())

print("\nSmoking history (kept as-is, including 'No Info'):")
print(df["smoking_history"].value_counts())

# Feature lists that will be used later
numeric_features = [
    "age", "bmi", "HbA1c_level", "blood_glucose_level",
    "hypertension", "heart_disease"
]

categorical_features = [
    "gender", "smoking_history",
    "hba1c_band", "glucose_band",
    "bmi_category", "age_group"
]

print("\nNumeric features:", numeric_features)
print("Categorical features:", categorical_features)

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_ready.csv"
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved → {OUT_PATH}")