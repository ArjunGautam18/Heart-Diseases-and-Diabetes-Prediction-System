"""
STEP 12: End-to-end sanity check
Confirms the saved model artifacts produce consistent predictions,
and demonstrates how a single new patient's raw data should flow through.
"""
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

PROC_DIR = Path(__file__).resolve().parent.parent / 'data' / 'processed'
MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

model = joblib.load(MODELS_DIR / 'heart_model.pkl')
scaler = joblib.load(MODELS_DIR / 'heart_scaler.pkl')
threshold = joblib.load(MODELS_DIR / 'heart_threshold.pkl')
feature_columns = joblib.load(MODELS_DIR / 'heart_features.pkl')
model_name = joblib.load(MODELS_DIR / 'heart_model_name.pkl')

print(f"Loaded model: {model_name}")
print(f"Decision threshold: {threshold:.3f}")
print(f"Expected feature count: {len(feature_columns)}\n")

# --- CHECK 1: Reproduce step 11's exact test-set metrics using ONLY the saved artifacts ---
X_test = pd.read_csv(PROC_DIR / 'X_test.csv')
y_test = pd.read_csv(PROC_DIR / 'y_test.csv').squeeze()

# Confirm column order matches exactly what the model expects
assert list(X_test.columns) == list(feature_columns), \
    "MISMATCH: X_test columns don't match saved feature_columns order!"
print("CHECK 1 PASSED: X_test column order matches saved feature_columns.\n")

needs_scaling = 'Logistic Regression' in model_name
X_eval = scaler.transform(X_test[feature_columns]) if needs_scaling else X_test[feature_columns]
proba_all = model.predict_proba(X_eval)[:, 1]
pred_all = (proba_all >= threshold).astype(int)

from sklearn.metrics import accuracy_score, roc_auc_score
print(f"Reproduced test accuracy (at saved threshold): {accuracy_score(y_test, pred_all):.3f}")
print(f"Reproduced test ROC-AUC: {roc_auc_score(y_test, proba_all):.3f}")
print("(These should match step 11's numbers.)\n")

# --- CHECK 2: Single-row prediction, the way a live API request would work ---
def predict(raw_input_df):
    """raw_input_df must have gone through the same cleaning/encoding as training."""
    missing_cols = [c for c in feature_columns if c not in raw_input_df.columns]
    if missing_cols:
        raise ValueError(f"Input is missing expected columns: {missing_cols}")
    X = raw_input_df[feature_columns]
    if needs_scaling:
        X = scaler.transform(X)
    proba = model.predict_proba(X)[:, 1][0]
    prediction = int(proba >= threshold)
    return {'prediction': prediction, 'probability': round(float(proba), 4)}

# Grab one real row from the test set and run it through predict()
sample_row = X_test.iloc[[0]]
true_label = y_test.iloc[0]
result = predict(sample_row)

print("CHECK 2: Single-row prediction via predict()")
print(f"  True label:   {'Disease' if true_label == 1 else 'No Disease'}")
print(f"  Prediction:   {'Disease' if result['prediction'] == 1 else 'No Disease'}")
print(f"  Probability:  {result['probability']}")
print(f"  Matches batch prediction for same row: {result['prediction'] == pred_all[0]}")

# --- CHECK 3: What happens with a malformed/incomplete input (should fail loudly, not silently) ---
print("\nCHECK 3: Deliberately incomplete input (should raise a clear error)")
bad_input = sample_row.drop(columns=[feature_columns[0]])
try:
    predict(bad_input)
    print("  FAILED: predict() did not catch the missing column!")
except ValueError as e:
    print(f"  PASSED: predict() correctly raised -> {e}")