"""
Heart Disease Prediction Module
"""

from pathlib import Path
import joblib
import pandas as pd
import numpy as np
from src.common.heart_pipeline import transform_heart_input
from src.common.artifacts import load_heart_artifacts

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "models"

# Load artifacts
_artifacts = load_heart_artifacts()
model = _artifacts["model"]
best_threshold = _artifacts["threshold"]
scaler = _artifacts["scaler"]
raw_columns = _artifacts["raw_columns"]
features = _artifacts["features"]


def preprocess_heart_input(input_data: dict) -> pd.DataFrame:
    """
    Takes raw form values and reproduces the exact feature engineering +
    one-hot encoding pipeline used in training (steps 3-6), so the model
    receives a properly populated feature vector instead of mostly zeros.
    """
    return transform_heart_input(input_data, list(raw_columns))
    d = dict(input_data)  # don't mutate caller's dict

    # --- Raw numeric fields (with sane fallbacks) ---
    age = float(d.get("age", 50))
    trestbps = float(d.get("trestbps", 130))
    chol = float(d.get("chol", 200))
    fbs = int(d.get("fbs", 0))
    thalch = float(d.get("thalch", d.get("thalach", 150)))  # accept either spelling
    exang = int(d.get("exang", 0))
    oldpeak = float(d.get("oldpeak", 0))
    ca = float(d.get("ca", 0))

    sex = d.get("sex", "Male")
    cp = str(d.get("cp", "asymptomatic")).lower()
    restecg = str(d.get("restecg", "normal")).lower()
    slope = str(d.get("slope", "flat")).lower()
    thal = str(d.get("thal", "normal")).lower()
    dataset = d.get("dataset", "Cleveland")  # not a real clinical field, default to baseline

    row = {
        "age": age,
        "trestbps": trestbps,
        "chol": chol,
        "fbs": fbs,
        "thalch": thalch,
        "exang": exang,
        "oldpeak": oldpeak,
        "ca": ca,
    }

    # --- Missing-value flags (0 since the form always supplies these) ---
    for col in ["trestbps", "chol", "fbs", "restecg", "thalch",
                "exang", "oldpeak", "slope", "ca", "thal"]:
        row[f"{col}_missing"] = 0

    # --- Engineered features (mirrors step5_feature_engineering.py) ---
    row["chol_per_age"] = chol / age if age else 0
    row["max_hr_reserve"] = 220 - age - thalch
    row["bp_chol_ratio"] = trestbps / chol if chol else 0
    row["high_oldpeak"] = int(oldpeak >= 2)
    row["ca_present"] = int(ca > 0)

    # age_group bucket (mirrors pd.cut bins=[0,40,50,60,70,100])
    if age < 40:
        age_group = "<40"
    elif age < 50:
        age_group = "40-50"
    elif age < 60:
        age_group = "50-60"
    elif age < 70:
        age_group = "60-70"
    else:
        age_group = "70+"

    # --- One-hot encodings (mirrors step6_encode.py, drop_first=True) ---
    row["sex_Male"] = int(sex == "Male")

    row["dataset_Hungary"] = int(dataset == "Hungary")
    row["dataset_Switzerland"] = int(dataset == "Switzerland")
    row["dataset_VA Long Beach"] = int(dataset == "VA Long Beach")

    row["cp_atypical angina"] = int(cp == "atypical angina")
    row["cp_non-anginal"] = int(cp == "non-anginal")
    row["cp_typical angina"] = int(cp == "typical angina")

    row["restecg_normal"] = int(restecg == "normal")
    row["restecg_st-t abnormality"] = int(restecg == "st-t abnormality")

    row["slope_flat"] = int(slope == "flat")
    row["slope_upsloping"] = int(slope == "upsloping")

    row["thal_normal"] = int(thal == "normal")
    row["thal_reversable defect"] = int(thal == "reversable defect")

    row["age_group_50-60"] = int(age_group == "50-60")
    row["age_group_60-70"] = int(age_group == "60-70")
    row["age_group_70+"] = int(age_group == "70+")
    row["age_group_<40"] = int(age_group == "<40")

    return pd.DataFrame([row])


def predict_heart(input_data: dict):
    """
    input_data: dict of raw feature values from the API request
    Returns: dict with prediction, probability, risk level, and health score
    """
    df = preprocess_heart_input(input_data)

    # Reindex to guarantee exact column order/set the model expects
    df = df.reindex(columns=raw_columns, fill_value=0)

    df_scaled = pd.DataFrame(
        scaler.transform(df),
        columns=df.columns
    )

    model_probability = float(model.predict_proba(df_scaled)[:, 1][0])

    # These fields are not present in the heart training dataset. Apply their
    # bounded contribution separately instead of pretending the model learned them.
    context_adjustment = 0.0
    context_factors = []
    yes_fields = {
        "hypertension": (0.05, "Hypertension"),
        "diabetes": (0.04, "Diabetes history"),
        "smoking": (0.04, "Smoking"),
        "familyHistory": (0.05, "Family history"),
        "stress": (0.02, "High stress"),
        "alcohol": (0.01, "Alcohol consumption"),
    }
    for field, (weight, label) in yes_fields.items():
        if str(input_data.get(field, "No")).strip().lower() == "yes":
            context_adjustment += weight
            context_factors.append(label)

    if str(input_data.get("exercise", "Yes")).strip().lower() == "no":
        context_adjustment += 0.03
        context_factors.append("Limited regular exercise")
    if str(input_data.get("diet", "Yes")).strip().lower() == "no":
        context_adjustment += 0.02
        context_factors.append("Unhealthy diet" )

    bmi = input_data.get("bmi")
    if bmi is None and input_data.get("heightCm") and input_data.get("weightKg"):
        height_m = float(input_data["heightCm"]) / 100
        bmi = float(input_data["weightKg"]) / (height_m * height_m)
    if bmi is not None and float(bmi) >= 30:
        context_adjustment += 0.04
        context_factors.append("BMI in obese range")

    context_adjustment = min(context_adjustment, 0.15)
    proba = min(model_probability + context_adjustment, 0.99)
    prediction = int(proba >= best_threshold)

    if proba < 0.3:
        risk_level = "Low"
    elif proba < 0.6:
        risk_level = "Moderate"
    else:
        risk_level = "High"

    health_score = round((1 - proba) * 100, 1)

    return {
        "prediction": prediction,
        "probability": round(float(proba), 4),
        "model_probability": round(model_probability, 4),
        "context_adjustment": round(context_adjustment, 4),
        "context_factors": context_factors,
        "risk_level": risk_level,
        "health_score": health_score,
        "message": "Heart disease risk detected" if prediction == 1 else "No significant heart disease risk detected",
    }


if __name__ == "__main__":
    sample = {
        "age": 63, "sex": "Male", "cp": "typical angina",
        "trestbps": 145, "chol": 233, "fbs": 1,
        "restecg": "lv hypertrophy", "thalch": 150, "exang": 0,
        "oldpeak": 2.3, "slope": "downsloping", "ca": 0, "thal": "fixed defect"
    }
    print(predict_heart(sample))