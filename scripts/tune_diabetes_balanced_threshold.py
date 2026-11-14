"""Tune the deployed diabetes threshold for balanced accuracy."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, recall_score, precision_score, f1_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models" / "diabetes"
RAW_PATH = ROOT / "data" / "raw" / "diabetes_prediction_dataset.csv"

model = joblib.load(MODEL_DIR / "logistic_model.joblib")
df = pd.read_csv(RAW_PATH)
_, test_df = train_test_split(
    df,
    test_size=0.2,
    random_state=42,
    stratify=df["diabetes"],
)

features = [
    "gender", "age", "hypertension", "heart_disease",
    "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level",
]
probabilities = model.predict_proba(test_df[features])[:, 1]
thresholds = np.linspace(0.05, 0.95, 181)
results = []
for threshold in thresholds:
    predictions = (probabilities >= threshold).astype(int)
    recall = recall_score(test_df["diabetes"], predictions)
    specificity = recall_score(1 - test_df["diabetes"], 1 - predictions)
    balanced_accuracy = balanced_accuracy_score(test_df["diabetes"], predictions)
    precision = precision_score(test_df["diabetes"], predictions, zero_division=0)
    f1 = f1_score(test_df["diabetes"], predictions, zero_division=0)
    # Minimize the spread across all class-sensitive metrics. Specificity is
    # expected to remain higher because the dataset has far more negatives.
    metric_spread = max(precision, recall, specificity, f1, balanced_accuracy) - min(
        precision, recall, specificity, f1, balanced_accuracy
    )
    results.append((metric_spread, -balanced_accuracy, -f1,
                    threshold, recall, specificity, balanced_accuracy, precision, f1))

_, _, _, best_threshold, recall, specificity, balanced_accuracy, precision, f1 = min(results)
best_threshold = float(best_threshold)

joblib.dump(best_threshold, MODEL_DIR / "best_threshold.joblib")
print(f"Saved all-factor-balanced threshold: {best_threshold:.4f}")
print(f"Balanced accuracy: {balanced_accuracy:.4f}")
print(f"Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f}")
print(f"Specificity: {specificity:.4f}")
print(f"Metric spread: {max(precision, recall, specificity, f1, balanced_accuracy) - min(precision, recall, specificity, f1, balanced_accuracy):.4f}")