"""
STEP 4 (Diabetes): Engineer clinically meaningful features
"""

from pathlib import Path
import pandas as pd

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_imputed.csv"
df = pd.read_csv(DATA_PATH)

def engineer_features(df):
    df = df.copy()

    # HbA1c risk band (clinical cutoffs)
    def hba1c_band(x):
        if x >= 6.5:
            return "diabetic"
        elif x >= 5.7:
            return "prediabetic"
        else:
            return "normal"
    df["hba1c_band"] = df["HbA1c_level"].apply(hba1c_band)

    # Blood glucose risk band
    def glucose_band(x):
        if x >= 126:
            return "high"
        elif x >= 100:
            return "borderline"
        else:
            return "normal"
    df["glucose_band"] = df["blood_glucose_level"].apply(glucose_band)

    # BMI category (WHO)
    def bmi_category(x):
        if x < 18.5:
            return "underweight"
        elif x < 25:
            return "normal"
        elif x < 30:
            return "overweight"
        else:
            return "obese"
    df["bmi_category"] = df["bmi"].apply(bmi_category)

    # Age groups
    def age_group(x):
        if x < 18:
            return "child"
        elif x < 40:
            return "young_adult"
        elif x < 60:
            return "middle_aged"
        else:
            return "senior"
    df["age_group"] = df["age"].apply(age_group)

    return df

df = engineer_features(df)

print("Engineered features created successfully.")
print(df[["hba1c_band", "glucose_band", "bmi_category", "age_group"]].head(10))

print("\nValue counts:")
for col in ["hba1c_band", "glucose_band", "bmi_category", "age_group"]:
    print(f"\n{col}:")
    print(df[col].value_counts())

OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_engineered.csv"
df.to_csv(OUT_PATH, index=False)
print(f"\nSaved → {OUT_PATH}")