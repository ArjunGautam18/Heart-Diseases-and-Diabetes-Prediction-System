"""Diabetes prediction module for the deployed model."""

from pathlib import Path

import joblib
import pandas as pd

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "models" / "diabetes"

model_path = ARTIFACTS_DIR / "logistic_model.joblib"
if not model_path.exists():
    model_path = ARTIFACTS_DIR / "diabetes_model.joblib"

model = joblib.load(model_path)
best_threshold = joblib.load(ARTIFACTS_DIR / "best_threshold.joblib")

feature_info = {
    "numeric_features": ["age", "hypertension", "heart_disease", "bmi", "HbA1c_level", "blood_glucose_level"],
    "categorical_features": ["gender", "smoking_history"],
    "best_threshold": float(best_threshold),
}

FEATURE_COLUMNS = feature_info["numeric_features"] + feature_info["categorical_features"]


def predict_diabetes(data: dict) -> dict:
    payload = pd.DataFrame([data])

    payload["gender"] = payload["gender"].astype(str).str.strip().str.title()
    payload["smoking_history"] = payload["smoking_history"].astype(str).str.strip()
    payload["smoking_history"] = payload["smoking_history"].replace({"No Info": "No Info"})

    missing = [col for col in FEATURE_COLUMNS if col not in payload.columns]
    if missing:
        raise ValueError(f"Missing required diabetes fields: {missing}")

    proba = model.predict_proba(payload[FEATURE_COLUMNS])[0, 1]
    pred = int(proba >= best_threshold)
    risk = "Low" if proba < 0.3 else "Moderate" if proba < 0.6 else "High"
    health_score = round((1 - proba) * 100, 1)

    return {
        "disease": "Diabetes",
        "prediction": pred,
        "probability": round(float(proba), 4),
        "risk_level": risk,
        "health_score": health_score,
        "message": "Diabetes detected" if pred == 1 else "No diabetes detected",
    }