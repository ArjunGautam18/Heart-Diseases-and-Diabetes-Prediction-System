import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
import joblib

from src.common.datasets import save_processed, split_and_scale
from src.common.features import engineer_diabetes_features, load_heart_dataframe
from src.common.paths import MODELS_DIR, PROCESSED_DIR, RAW_DIR, ensure_dirs

ensure_dirs(PROCESSED_DIR, MODELS_DIR)


def preprocess_heart():
    df = load_heart_dataframe()

    X = df.drop(columns=["num"])
    y = df["num"]

    split = split_and_scale(X, y)

    joblib.dump(split["scaler"], os.path.join(MODELS_DIR, "heart_scaler.pkl"))
    joblib.dump(list(X.columns), os.path.join(MODELS_DIR, "heart_features.pkl"))
    save_processed("heart", split, X.columns)

    print(f"  Heart: train={split['X_train'].shape}, test={split['X_test'].shape}")


def preprocess_diabetes():
    candidate_paths = [
        os.path.join(RAW_DIR, "diabetes_prediction_dataset.csv"),
        os.path.join(RAW_DIR, "diabetes.csv"),
    ]
    path = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])
    df = pd.read_csv(path)

    if "diabetes" in df.columns:
        target_col = "diabetes"
    elif "Outcome" in df.columns:
        target_col = "Outcome"
    else:
        target_col = df.columns[-1]

    df = df.dropna(subset=[target_col])

    if target_col == "diabetes":
        feature_cols = [
            "gender", "age", "hypertension", "heart_disease",
            "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level"
        ]
        X = df[feature_cols].copy()
        y = df[target_col].astype(int)
        split = split_and_scale(X, y)
        joblib.dump(split["scaler"], os.path.join(MODELS_DIR, "diabetes_scaler.pkl"))
        joblib.dump(list(X.columns), os.path.join(MODELS_DIR, "diabetes_model_features.pkl"))
        joblib.dump(list(X.columns), os.path.join(MODELS_DIR, "diabetes_features.pkl"))
        print(f"  Diabetes dataset ready: {X.shape[0]} rows, {X.shape[1]} features")
        return

    light_missing = ["Glucose", "BloodPressure", "BMI"]
    for col in light_missing:
        if col in df.columns:
            df[col] = df[col].replace(0, pd.NA)

    heavy_missing = ["Insulin", "SkinThickness"]
    for col in heavy_missing:
        if col in df.columns:
            df[col] = df[col].replace(0, pd.NA)
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df.groupby(target_col)[col].transform(lambda x: x.fillna(x.median()))

    numeric_cols = df.select_dtypes(include="number").columns.drop(target_col, errors="ignore")
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    before_rows = df.shape[0]
    outlier_cols = ["Glucose", "BloodPressure", "BMI", "Age", "Pregnancies"]
    for col in outlier_cols:
        if col in df.columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR
            df = df[(df[col] >= lower) & (df[col] <= upper)]
    print(f"  Outlier removal: {before_rows} -> {df.shape[0]} rows")

    raw_feature_names = numeric_cols.tolist()
    df = engineer_diabetes_features(df)

    X = df.drop(columns=[target_col]).select_dtypes(include="number")
    y = df[target_col]

    split = split_and_scale(X, y)

    joblib.dump(split["scaler"], os.path.join(MODELS_DIR, "diabetes_scaler.pkl"))
    joblib.dump(raw_feature_names, os.path.join(MODELS_DIR, "diabetes_raw_features.pkl"))
    joblib.dump(list(X.columns), os.path.join(MODELS_DIR, "diabetes_model_features.pkl"))
    joblib.dump(raw_feature_names, os.path.join(MODELS_DIR, "diabetes_features.pkl"))
    print("\nDone.")