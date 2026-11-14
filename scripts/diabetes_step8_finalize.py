"""
STEP 8 (Diabetes): Finalize and save all deployment artifacts
"""

from pathlib import Path
import joblib

ARTIFACTS = Path(__file__).resolve().parent.parent / "models" / "diabetes"

model          = joblib.load(ARTIFACTS / "logistic_model.joblib")
preprocessor   = joblib.load(ARTIFACTS / "preprocessor.joblib")
best_threshold = joblib.load(ARTIFACTS / "best_threshold.joblib")

feature_info = {
    "numeric_features": [
        "age", "bmi", "HbA1c_level", "blood_glucose_level",
        "hypertension", "heart_disease"
    ],
    "categorical_features": [
        "gender", "smoking_history",
        "hba1c_band", "glucose_band",
        "bmi_category", "age_group"
    ],
    "best_threshold": float(best_threshold)
}

joblib.dump(feature_info, ARTIFACTS / "feature_info.joblib")

print("All deployment artifacts ready in:")
print(ARTIFACTS)
print("\nFiles created:")
for f in sorted(ARTIFACTS.glob("*")):
    print("  -", f.name)

print("\nDiabetes pipeline complete!")