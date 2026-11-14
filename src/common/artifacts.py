"""Loading of the pickled models, scalers, feature lists and thresholds."""
import os
from pathlib import Path

import joblib
import pandas as pd

from src.common.paths import MODELS_DIR

DEFAULT_DIABETES_THRESHOLD = 0.5
DIABETES_MODELS_DIR = Path(MODELS_DIR) / "diabetes"


def validate_artifacts():
    """Fail startup when the deployed model family is incomplete or incompatible."""
    required = [
        Path(MODELS_DIR) / name for name in
        ["heart_model.pkl", "heart_scaler.pkl", "heart_features.pkl", "heart_raw_columns.pkl",
         "heart_threshold.pkl"]
    ] + [DIABETES_MODELS_DIR / name for name in
         ["logistic_model.joblib", "preprocessor.joblib", "feature_info.joblib", "best_threshold.joblib"]]
    missing = [str(path.relative_to(MODELS_DIR.parent)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Incomplete model artifact set: {missing}")

    heart_model = joblib.load(Path(MODELS_DIR) / "heart_model.pkl")
    heart_columns = joblib.load(Path(MODELS_DIR) / "heart_raw_columns.pkl")
    model_columns = list(getattr(heart_model, "feature_names_in_", heart_columns))
    if model_columns != list(heart_columns):
        raise ValueError("heart_model.pkl and heart_raw_columns.pkl have different feature contracts")


def artifact_path(name):
    return os.path.join(MODELS_DIR, name)


def load_artifact(name):
    return joblib.load(artifact_path(name))


def diabetes_raw_features_path():
    """Newer runs write diabetes_raw_features.pkl; older ones diabetes_features.pkl."""
    path = artifact_path("diabetes_raw_features.pkl")
    return path if os.path.exists(path) else artifact_path("diabetes_features.pkl")


def load_heart_artifacts():
    return {
        "model": load_artifact("heart_model.pkl"),
        "scaler": load_artifact("heart_scaler.pkl"),
        "features": load_artifact("heart_features.pkl"),
        "raw_columns": load_artifact("heart_raw_columns.pkl"),
        "threshold": float(load_artifact("heart_threshold.pkl")),
    }


def load_diabetes_artifacts():
    """Load the current 8-input diabetes API artifact family."""
    model_dir = DIABETES_MODELS_DIR
    return {
        "model": joblib.load(model_dir / "logistic_model.joblib"),
        "preprocessor": joblib.load(model_dir / "preprocessor.joblib"),
        "features": joblib.load(model_dir / "feature_info.joblib"),
        "threshold": float(joblib.load(model_dir / "best_threshold.joblib")),
    }


def build_feature_row(payload, features, default=0):
    """One-row DataFrame with the model's feature order, missing keys defaulted."""
    return pd.DataFrame([[payload.get(f, default) for f in features]], columns=features)
