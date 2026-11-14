"""
Model Evaluation Script — Smart Healthcare System

Evaluates the trained diabetes and heart disease models against their
held-out test sets, printing standard metrics and saving confusion
matrix / ROC curve plots to notebooks/eval_plots/.

Usage:
    python -u scripts/evaluate.py               # evaluate both models
    python -u scripts/evaluate.py --model heart      # heart only
    python -u scripts/evaluate.py --model diabetes   # diabetes only
"""

import argparse
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split

try:
    import matplotlib.pyplot as plt
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data" / "processed"
PLOTS_DIR = ROOT / "notebooks" / "eval_plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def load_test_split(disease: str, expected_columns=None):
    """
    Loads X_test / y_test for the given disease from data/processed.
    Adjust the filenames below if your step7_split_scale.py saves under
    different names.
    """
    x_path = DATA_DIR / f"{disease}_X_test.csv"
    y_path = DATA_DIR / f"{disease}_y_test.csv"

    if not x_path.exists() or not y_path.exists():
        raise FileNotFoundError(
            f"Could not find test split for '{disease}' at:\n"
            f"  {x_path}\n  {y_path}\n"
            f"Check the filenames saved by your split/scale step."
        )

    X_test = pd.read_csv(x_path)
    y_test = pd.read_csv(y_path).squeeze("columns")

    if expected_columns is not None and list(X_test.columns) != list(expected_columns):
        print("  Processed split does not match the saved model; rebuilding from raw data.")
        if disease == "diabetes":
            raw = pd.read_csv(DATA_DIR.parent / "raw" / "diabetes_prediction_dataset.csv")
            X = raw[[
                "gender", "age", "hypertension", "heart_disease",
                "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level",
            ]]
            y = raw["diabetes"].astype(int)
        else:
            sys.path.insert(0, str(ROOT / "scripts"))
            from retrain_heart import load_and_prepare_data

            X, y = load_and_prepare_data()

        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        X_test = X_test.loc[:, expected_columns]

    return X_test, y_test


def load_artifacts(disease: str):
    if disease == "diabetes":
        model_dir = MODELS_DIR / "diabetes"
        model_path = model_dir / "logistic_model.joblib"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Current diabetes model is missing: {model_path}"
            )
        model = joblib.load(model_path)
        threshold = joblib.load(model_dir / "best_threshold.joblib")
        scaler = None  # diabetes pipeline doesn't use a separate scaler per predict_diabetes.py
        return model, float(threshold), scaler

    elif disease == "heart":
        model = joblib.load(MODELS_DIR / "heart_model.pkl")
        threshold = joblib.load(MODELS_DIR / "heart_threshold.pkl")
        scaler = joblib.load(MODELS_DIR / "heart_scaler.pkl")
        return model, float(threshold), scaler

    else:
        raise ValueError(f"Unknown disease: {disease}")


def evaluate(disease: str):
    print(f"\n{'=' * 60}")
    print(f"Evaluating: {disease.upper()}")
    print(f"{'=' * 60}")

    model, threshold, scaler = load_artifacts(disease)
    expected_columns = getattr(model, "feature_names_in_", None)
    X_test, y_test = load_test_split(disease, expected_columns)

    if scaler is not None:
        X_eval = pd.DataFrame(scaler.transform(X_test), columns=X_test.columns)
    else:
        X_eval = X_test

    proba = model.predict_proba(X_eval)[:, 1]
    preds = (proba >= threshold).astype(int)

    acc = accuracy_score(y_test, preds)
    prec = precision_score(y_test, preds, zero_division=0)
    rec = recall_score(y_test, preds, zero_division=0)
    f1 = f1_score(y_test, preds, zero_division=0)
    auc = roc_auc_score(y_test, proba)
    cm = confusion_matrix(y_test, preds)

    print(f"Threshold used : {threshold:.4f}")
    print(f"Accuracy       : {acc:.4f}")
    print(f"Precision      : {prec:.4f}")
    print(f"Recall         : {rec:.4f}")
    print(f"F1 Score       : {f1:.4f}")
    print(f"ROC-AUC        : {auc:.4f}")
    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(classification_report(y_test, preds, zero_division=0))

    if HAS_PLOTTING:
        save_confusion_matrix(cm, disease)
        save_roc_curve(y_test, proba, auc, disease)
    else:
        print("(matplotlib not installed — skipping plot generation. "
              "Run: pip install matplotlib)")

    return {
        "disease": disease,
        "accuracy": acc,
        "precision": prec,
        "recall": rec,
        "f1": f1,
        "roc_auc": auc,
        "threshold": threshold,
    }


def save_confusion_matrix(cm, disease: str):
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, cmap="Blues")

    labels = ["No Disease", "Disease"]
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"{disease.capitalize()} — Confusion Matrix")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                     color="white" if cm[i, j] > cm.max() / 2 else "black")

    fig.colorbar(im)
    fig.tight_layout()

    out_path = PLOTS_DIR / f"{disease}_confusion_matrix.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved confusion matrix -> {out_path}")

    normalized = cm / cm.sum(axis=1, keepdims=True)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"{disease.capitalize()} — Normalized Confusion Matrix")

    for i in range(normalized.shape[0]):
        for j in range(normalized.shape[1]):
            ax.text(j, i, f"{normalized[i, j]:.1%}", ha="center", va="center",
                    color="white" if normalized[i, j] > 0.5 else "black")

    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    normalized_path = PLOTS_DIR / f"{disease}_confusion_matrix_normalized.png"
    fig.savefig(normalized_path, dpi=150)
    plt.close(fig)
    print(f"Saved normalized confusion matrix -> {normalized_path}")


def save_roc_curve(y_test, proba, auc, disease: str):
    fpr, tpr, _ = roc_curve(y_test, proba)

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(fpr, tpr, label=f"ROC curve (AUC = {auc:.3f})")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random guess")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"{disease.capitalize()} — ROC Curve")
    ax.legend(loc="lower right")
    fig.tight_layout()

    out_path = PLOTS_DIR / f"{disease}_roc_curve.png"
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"Saved ROC curve -> {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate trained models.")
    parser.add_argument(
        "--model",
        choices=["diabetes", "heart", "both"],
        default="both",
        help="Which model to evaluate (default: both)",
    )
    args = parser.parse_args()

    targets = ["diabetes", "heart"] if args.model == "both" else [args.model]

    summary = []
    for disease in targets:
        try:
            result = evaluate(disease)
            summary.append(result)
        except Exception as e:
            print(f"\n[ERROR] Failed to evaluate '{disease}': {e}")

    if summary:
        print(f"\n{'=' * 60}")
        print("Summary")
        print(f"{'=' * 60}")
        df = pd.DataFrame(summary).set_index("disease")
        print(df.round(4))


if __name__ == "__main__":
    main()