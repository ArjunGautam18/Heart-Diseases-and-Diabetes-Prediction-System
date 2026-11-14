"""
STEP 9: Evaluate the best model — confusion matrix, ROC curve, feature importance
Builds on the trained model saved in step 8.
"""
from pathlib import Path
import sys
import pandas as pd
import numpy as np
import joblib
import matplotlib
matplotlib.use('Agg')  # no display needed, just save files
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import (confusion_matrix, ConfusionMatrixDisplay,
                              roc_curve, roc_auc_score, classification_report)

PROC_DIR = Path(__file__).resolve().parent.parent / 'data' / 'processed'
MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'
PLOTS_DIR = Path(__file__).resolve().parent.parent / 'notebooks' / 'eval_plots'
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

model = joblib.load(MODELS_DIR / 'heart_model.pkl')
best_name = type(model).__name__
scaler = joblib.load(MODELS_DIR / 'heart_scaler.pkl')
threshold = float(joblib.load(MODELS_DIR / 'heart_threshold.pkl'))

# Use the saved split only when it matches the current model's feature contract.
X_test = pd.read_csv(PROC_DIR / 'heart_X_test.csv')
y_test = pd.read_csv(PROC_DIR / 'heart_y_test.csv').squeeze()
expected_columns = list(model.feature_names_in_)
if list(X_test.columns) != expected_columns:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from retrain_heart import load_and_prepare_data

    X, y = load_and_prepare_data()
    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_test = X_test.loc[:, expected_columns]

# The current heart artifact family is trained on the saved scaled features.
X_eval = pd.DataFrame(
    scaler.transform(X_test),
    columns=expected_columns,
    index=X_test.index,
)

proba = model.predict_proba(X_eval)[:, 1]
pred = (proba >= threshold).astype(int)

# --- Classification report ---
print(f"Evaluating: {best_name} at threshold {threshold:.4f}\n")
print(classification_report(y_test, pred, target_names=['No Disease', 'Disease']))

# --- Confusion matrix ---
cm = confusion_matrix(y_test, pred)
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['No Disease', 'Disease'])
disp.plot(cmap='Blues')
plt.title(f'Confusion Matrix — {best_name}')
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'heart_confusion_matrix.png')
plt.close()
print(f"Saved confusion matrix to {PLOTS_DIR / 'heart_confusion_matrix.png'}")

# Row-normalized view shows the percentage correct for each actual class.
disp = ConfusionMatrixDisplay(
    confusion_matrix=confusion_matrix(y_test, pred, normalize='true'),
    display_labels=['No Disease', 'Disease']
)
disp.plot(cmap='Blues', values_format='.2f')
plt.title(f'Heart — Normalized Confusion Matrix ({best_name})')
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'heart_confusion_matrix_normalized.png')
plt.close()
print(f"Saved normalized confusion matrix to {PLOTS_DIR / 'heart_confusion_matrix_normalized.png'}")

# --- ROC curve ---
fpr, tpr, _ = roc_curve(y_test, proba)
auc = roc_auc_score(y_test, proba)
plt.figure()
plt.plot(fpr, tpr, label=f'{best_name} (AUC = {auc:.3f})')
plt.plot([0, 1], [0, 1], 'k--', label='Random guess')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve — Heart Disease Prediction')
plt.legend()
plt.tight_layout()
plt.savefig(PLOTS_DIR / 'heart_roc_curve.png')
plt.close()
print(f"Saved ROC curve to {PLOTS_DIR / 'heart_roc_curve.png'}")

# --- Feature importance (only meaningful for tree-based models) ---
if hasattr(model, 'feature_importances_'):
    importances = pd.Series(model.feature_importances_, index=X_test.columns).sort_values(ascending=False)
    print("\nTop 10 features:")
    print(importances.head(10))
elif hasattr(model, 'coef_'):
    # For Logistic Regression, coefficient magnitude ~ importance (features are scaled)
    importances = pd.Series(np.abs(model.coef_[0]), index=X_test.columns).sort_values(ascending=False)
    print("\nTop 10 features (by |coefficient|, scaled features):")
    print(importances.head(10))