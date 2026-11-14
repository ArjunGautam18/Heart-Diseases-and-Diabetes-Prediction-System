"""
Heart Disease Model — Retraining with Cross-Validation & Tuning

Rebuilds the heart disease model from raw data using the SAME feature
engineering as predict_heart.py, then compares Logistic Regression,
Random Forest, and Gradient Boosting with cross-validation, tunes the
best one, and saves updated artifacts compatible with predict_heart.py.

Usage:
    python -u scripts/retrain_heart.py
"""

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    balanced_accuracy_score, confusion_matrix,
)
from sklearn.model_selection import (
    train_test_split, cross_val_score, GridSearchCV, StratifiedKFold,
)
from sklearn.preprocessing import StandardScaler
from src.common.heart_pipeline import engineer_heart_features

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
RAW_DIR = ROOT / "data" / "raw"
MODELS_DIR = ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


# ------------------- Feature Engineering (mirrors predict_heart.py) -------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reproduces the same feature engineering used at inference time in
    predict_heart.py's preprocess_heart_input(), applied here to the
    full raw training dataframe.
    """
    return engineer_heart_features(df)
    df = df.copy()

    # Normalize categorical text
    for col in ["sex", "cp", "restecg", "slope", "thal", "dataset"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Missing-value flags (before imputing)
    for col in ["trestbps", "chol", "fbs", "restecg", "thalch",
                "exang", "oldpeak", "slope", "ca", "thal"]:
        df[f"{col}_missing"] = df[col].isna().astype(int) if col in df.columns else 0

    # Impute numeric with median, categorical with mode
    numeric_cols = ["age", "trestbps", "chol", "thalch", "oldpeak", "ca"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    for col in ["fbs", "exang"]:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    for col in ["restecg", "slope", "thal"]:
        if col in df.columns:
            mode_val = df[col].mode(dropna=True)
            fill_val = mode_val.iloc[0] if not mode_val.empty else "normal"
            df[col] = df[col].fillna(fill_val).str.lower()

    if "cp" in df.columns:
        df["cp"] = df["cp"].fillna("asymptomatic").str.lower()

    if "dataset" not in df.columns:
        df["dataset"] = "Cleveland"
    else:
        df["dataset"] = df["dataset"].fillna("Cleveland")

    # Engineered numeric features
    df["chol_per_age"] = df["chol"] / df["age"].replace(0, np.nan)
    df["chol_per_age"] = df["chol_per_age"].fillna(df["chol_per_age"].median())

    df["max_hr_reserve"] = 220 - df["age"] - df["thalch"]

    df["bp_chol_ratio"] = df["trestbps"] / df["chol"].replace(0, np.nan)
    df["bp_chol_ratio"] = df["bp_chol_ratio"].fillna(df["bp_chol_ratio"].median())

    df["high_oldpeak"] = (df["oldpeak"] >= 2).astype(int)
    df["ca_present"] = (df["ca"] > 0).astype(int)

    # Age group buckets
    df["age_group"] = pd.cut(
        df["age"], bins=[0, 40, 50, 60, 70, 100],
        labels=["<40", "40-50", "50-60", "60-70", "70+"]
    )

    # One-hot encode categoricals (drop_first=True, matching training-time convention)
    cat_cols = ["sex", "dataset", "cp", "restecg", "slope", "thal", "age_group"]
    df_encoded = pd.get_dummies(df, columns=cat_cols, drop_first=True)

    return df_encoded


def load_and_prepare_data():
    csv_path = RAW_DIR / "heart_disease_uci.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find {csv_path}")

    df = pd.read_csv(csv_path)

    label_col = next(c for c in ["num", "target", "heart_disease", "condition"] if c in df.columns)
    df = df.dropna(subset=[label_col]).copy()
    y = (df[label_col].astype(float) > 0).astype(int)

    feature_source_cols = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalch", "exang", "oldpeak", "slope", "ca", "thal", "dataset",
    ]
    feature_source_cols = [c for c in feature_source_cols if c in df.columns]
    X_raw = df[feature_source_cols]

    X_encoded = engineer_features(X_raw)

    # Drop any leftover non-numeric columns just in case
    X_encoded = X_encoded.select_dtypes(include=[np.number, bool])
    X_encoded = X_encoded.astype(float)

    return X_encoded, y


# ------------------- Model Comparison -------------------

def compare_models(X_train, y_train):
    print("\n" + "=" * 60)
    print("Cross-Validated Model Comparison (5-fold, ROC-AUC)")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    candidates = {
        "LogisticRegression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=6, class_weight="balanced",
            random_state=RANDOM_STATE
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200, max_depth=3, learning_rate=0.05,
            random_state=RANDOM_STATE
        ),
    }

    results = {}
    for name, model in candidates.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="roc_auc")
        results[name] = scores.mean()
        print(f"{name:20s}  mean AUC = {scores.mean():.4f}  (+/- {scores.std():.4f})")

    best_name = max(results, key=results.get)
    print(f"\nBest model: {best_name} (AUC={results[best_name]:.4f})")
    return best_name, candidates[best_name]


# ------------------- Hyperparameter Tuning -------------------

def tune_model(best_name, X_train, y_train):
    print("\n" + "=" * 60)
    print(f"Tuning {best_name}")
    print("=" * 60)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    if best_name == "RandomForest":
        base = RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE)
        param_grid = {
            "n_estimators": [200, 300, 400],
            "max_depth": [4, 6, 8, None],
            "min_samples_leaf": [1, 2, 4],
        }
    elif best_name == "GradientBoosting":
        base = GradientBoostingClassifier(random_state=RANDOM_STATE)
        param_grid = {
            "n_estimators": [100, 200, 300],
            "max_depth": [2, 3, 4],
            "learning_rate": [0.01, 0.05, 0.1],
        }
    else:  # LogisticRegression
        base = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=RANDOM_STATE)
        param_grid = {
            "C": [0.01, 0.1, 1.0, 10.0],
            "penalty": ["l2"],
        }

    search = GridSearchCV(base, param_grid, cv=cv, scoring="roc_auc", n_jobs=-1)
    search.fit(X_train, y_train)

    print(f"Best params: {search.best_params_}")
    print(f"Best CV AUC: {search.best_score_:.4f}")

    return search.best_estimator_


# ------------------- Threshold Selection -------------------

def find_best_threshold(model, X_val, y_val):
    proba = model.predict_proba(X_val)[:, 1]
    candidates = np.unique(np.r_[0.05, np.linspace(0.10, 0.90, 161), 0.95])
    scores = [
        balanced_accuracy_score(y_val, (proba >= threshold).astype(int))
        for threshold in candidates
    ]
    best_idx = int(np.argmax(scores))
    best_threshold = float(candidates[best_idx])

    predictions = (proba >= best_threshold).astype(int)
    print(f"\nBest threshold (max balanced accuracy): {best_threshold:.4f}")
    print(f"  Balanced accuracy: {scores[best_idx]:.4f}")
    print(f"  Precision:         {precision_score(y_val, predictions, zero_division=0):.4f}")
    print(f"  Recall:            {recall_score(y_val, predictions, zero_division=0):.4f}")

    return float(best_threshold)


# ------------------- Main -------------------

def main():
    print("Loading and engineering heart disease data...")
    X, y = load_and_prepare_data()
    print(f"Total samples: {len(X)}, Positive rate: {y.mean():.2%}")
    print(f"Feature count: {X.shape[1]}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=X_train.columns, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=X_test.columns, index=X_test.index
    )

    best_name, _ = compare_models(X_train_scaled, y_train)
    tuned_model = tune_model(best_name, X_train_scaled, y_train)

    best_threshold = find_best_threshold(tuned_model, X_test_scaled, y_test)

    # Final evaluation on held-out test set
    proba = tuned_model.predict_proba(X_test_scaled)[:, 1]
    preds = (proba >= best_threshold).astype(int)

    print("\n" + "=" * 60)
    print("FINAL TEST SET PERFORMANCE")
    print("=" * 60)
    print(f"Accuracy   : {accuracy_score(y_test, preds):.4f}")
    print(f"Balanced Acc: {balanced_accuracy_score(y_test, preds):.4f}")
    print(f"Precision  : {precision_score(y_test, preds, zero_division=0):.4f}")
    print(f"Recall     : {recall_score(y_test, preds, zero_division=0):.4f}")
    print(f"F1 Score   : {f1_score(y_test, preds, zero_division=0):.4f}")
    print(f"ROC-AUC    : {roc_auc_score(y_test, proba):.4f}")
    tn, fp, fn, tp = confusion_matrix(y_test, preds, labels=[0, 1]).ravel()
    print(f"Confusion Matrix: TN={tn} FP={fp} FN={fn} TP={tp}")

    # Save artifacts, matching the filenames predict_heart.py expects
    joblib.dump(tuned_model, MODELS_DIR / "heart_model.pkl")
    joblib.dump(best_threshold, MODELS_DIR / "heart_threshold.pkl")
    joblib.dump(scaler, MODELS_DIR / "heart_scaler.pkl")
    joblib.dump(list(X_train.columns), MODELS_DIR / "heart_raw_columns.pkl")
    joblib.dump(list(X_train.columns), MODELS_DIR / "heart_features.pkl")

    print(f"\nSaved updated artifacts to {MODELS_DIR}")
    print("  - heart_model.pkl")
    print("  - heart_threshold.pkl")
    print("  - heart_scaler.pkl")
    print("  - heart_raw_columns.pkl")
    print("  - heart_features.pkl")


if __name__ == "__main__":
    main()