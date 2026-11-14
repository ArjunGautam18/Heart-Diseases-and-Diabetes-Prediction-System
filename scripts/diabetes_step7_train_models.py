"""
STEP 7 (Diabetes): Train model with class_weight='balanced' + threshold tuning
"""

from pathlib import Path
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    roc_auc_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, precision_recall_curve
)

ARTIFACTS = Path(__file__).resolve().parent.parent / "models" / "diabetes"

X_train, X_test, y_train, y_test = joblib.load(ARTIFACTS / "splits.joblib")
preprocessor = joblib.load(ARTIFACTS / "preprocessor.joblib")

# Full pipeline with balanced class weights
model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", LogisticRegression(
        class_weight="balanced",
        max_iter=1000,
        random_state=42,
        solver="lbfgs"
    ))
])

model.fit(X_train, y_train)

# Default threshold
y_pred  = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1]

print("=== Default threshold (0.5) ===")
print(f"ROC-AUC  : {roc_auc_score(y_test, y_proba):.4f}")
print(f"Precision: {precision_score(y_test, y_pred):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred):.4f}")
print(f"F1       : {f1_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["No Diabetes", "Diabetes"]))
print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# ===== Find F1-optimal threshold =====
precisions, recalls, thresholds = precision_recall_curve(y_test, y_proba)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-8)

best_idx = np.argmax(f1_scores[:-1])
best_threshold = thresholds[best_idx]
best_f1 = f1_scores[best_idx]

print(f"\nBest F1 threshold : {best_threshold:.4f}")
print(f"Best F1 score     : {best_f1:.4f}")

y_pred_opt = (y_proba >= best_threshold).astype(int)

print("\n=== Optimal threshold metrics ===")
print(f"ROC-AUC  : {roc_auc_score(y_test, y_proba):.4f}")
print(f"Precision: {precision_score(y_test, y_pred_opt):.4f}")
print(f"Recall   : {recall_score(y_test, y_pred_opt):.4f}")
print(f"F1       : {f1_score(y_test, y_pred_opt):.4f}")
print("\nClassification Report (optimal):")
print(classification_report(y_test, y_pred_opt, target_names=["No Diabetes", "Diabetes"]))
print("Confusion Matrix (optimal):")
print(confusion_matrix(y_test, y_pred_opt))

# Save model + threshold
joblib.dump(model, ARTIFACTS / "logistic_model.joblib")
joblib.dump(best_threshold, ARTIFACTS / "best_threshold.joblib")

print(f"\nModel & threshold saved to → {ARTIFACTS}")