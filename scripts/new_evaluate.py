"""
Model Evaluation — Summary Only
Evaluates predict_diabetes() and predict_heart() and prints a single
summary table of accuracy / precision / recall / f1 / roc_auc.

Usage:
    python -u scripts/evaluate.py
    python -u scripts/evaluate.py --model heart
    python -u scripts/evaluate.py --model diabetes
"""

import argparse
import sys
from pathlib import Path

import joblib
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    balanced_accuracy_score, confusion_matrix, ConfusionMatrixDisplay,
)
from sklearn.model_selection import train_test_split

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(ROOT))
sys.path.append(str(SCRIPTS_DIR))

from predict_diabetes import predict_diabetes
from predict_heart import predict_heart

RAW_DIR = ROOT / "data" / "raw"
RANDOM_STATE = 42
TEST_SIZE = 0.2
PLOTS_DIR = ROOT / "notebooks" / "eval_plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_diabetes():
    df = pd.read_csv(RAW_DIR / "diabetes_prediction_dataset.csv")
    label_col = next(c for c in ["diabetes", "Diabetes", "target", "outcome", "Outcome"] if c in df.columns)

    _, test_df = train_test_split(df, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df[label_col])

    y_true, y_pred, y_proba = [], [], []
    for _, row in test_df.iterrows():
        result = predict_diabetes({
            "gender": row["gender"], "age": row["age"],
            "hypertension": int(row["hypertension"]), "heart_disease": int(row["heart_disease"]),
            "smoking_history": row["smoking_history"], "bmi": row["bmi"],
            "HbA1c_level": row["HbA1c_level"], "blood_glucose_level": row["blood_glucose_level"],
        })
        y_true.append(int(row[label_col]))
        y_pred.append(result["prediction"])
        y_proba.append(result["probability"])

    return compute_metrics("diabetes", y_true, y_pred, y_proba)


def evaluate_heart():
    sys.path.insert(0, str(SCRIPTS_DIR))
    from retrain_heart import load_and_prepare_data

    X, y = load_and_prepare_data()
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    model = joblib.load(ROOT / "models" / "heart_model.pkl")
    scaler = joblib.load(ROOT / "models" / "heart_scaler.pkl")
    threshold = float(joblib.load(ROOT / "models" / "heart_threshold.pkl"))
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=X_test.columns, index=X_test.index
    )
    y_proba = model.predict_proba(X_test_scaled)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    return compute_metrics("heart", y_test.tolist(), y_pred.tolist(), y_proba.tolist())


def compute_metrics(name, y_true, y_pred, y_proba):
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    return {
        "disease": name,
        "n_samples": len(y_true),
        # Display balanced accuracy as "accuracy" because raw accuracy is
        # misleading for the imbalanced diabetes dataset.
        "accuracy": balanced_accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_proba),
        "tn": int(cm[0, 0]),
        "fp": int(cm[0, 1]),
        "fn": int(cm[1, 0]),
        "tp": int(cm[1, 1]),
        "specificity": cm[0, 0] / (cm[0, 0] + cm[0, 1]) if (cm[0, 0] + cm[0, 1]) else 0.0,
        "y_true": y_true,
        "y_pred": y_pred,
    }


def save_confusion_matrices(metrics):
    labels = ["No Disease", "Disease"]
    cm = confusion_matrix(metrics["y_true"], metrics["y_pred"], labels=[0, 1])

    for normalized, suffix, values_format in [
        (False, "", "d"),
        (True, "_normalized", ".2f"),
    ]:
        matrix = cm.astype(float) / cm.sum(axis=1, keepdims=True) if normalized else cm
        display = ConfusionMatrixDisplay(matrix, display_labels=labels)
        display.plot(cmap="Blues", values_format=values_format)
        title = f"{metrics['disease'].capitalize()} — Confusion Matrix"
        if normalized:
            title += " (Normalized)"
        plt.title(title)
        plt.tight_layout()
        output_path = PLOTS_DIR / f"{metrics['disease']}_confusion_matrix{suffix}.png"
        plt.savefig(output_path, dpi=150)
        plt.close()
        print(f"Saved {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["diabetes", "heart", "both"], default="both")
    args = parser.parse_args()
    targets = ["diabetes", "heart"] if args.model == "both" else [args.model]

    summary = []
    for disease in targets:
        metrics = evaluate_diabetes() if disease == "diabetes" else evaluate_heart()
        save_confusion_matrices(metrics)
        summary.append(metrics)

    print("\n" + "=" * 70)
    print("PERFORMANCE SUMMARY")
    print("=" * 70)
    summary_table = pd.DataFrame(summary).set_index("disease")
    print(summary_table.drop(columns=["n_samples", "y_true", "y_pred"]).round(4).to_string())
    print("=" * 70)


if __name__ == "__main__":
    main()