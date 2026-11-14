"""
STEP 11: Final evaluation, threshold tuning, and deployment prep
Works with whichever model is currently saved as heart_model.pkl (from step 8 or step 10).
"""
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import (roc_auc_score, precision_recall_curve, f1_score,
                              accuracy_score, recall_score, precision_score,
                              classification_report)

PROC_DIR = Path(__file__).resolve().parent.parent / 'data' / 'processed'
MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

X_test = pd.read_csv(PROC_DIR / 'X_test.csv')
y_test = pd.read_csv(PROC_DIR / 'y_test.csv').squeeze()
X_train = pd.read_csv(PROC_DIR / 'X_train.csv')

model = joblib.load(MODELS_DIR / 'heart_model.pkl')
best_name = joblib.load(MODELS_DIR / 'heart_model_name.pkl')
scaler = joblib.load(MODELS_DIR / 'heart_scaler.pkl')
feature_columns = joblib.load(MODELS_DIR / 'heart_raw_columns.pkl')

needs_scaling = 'Logistic Regression' in best_name
X_eval = scaler.transform(X_test) if needs_scaling else X_test

proba = model.predict_proba(X_eval)[:, 1]

# --- Find the threshold that maximizes F1 (balances precision & recall) ---
precisions, recalls, thresholds = precision_recall_curve(y_test, proba)
f1_scores = 2 * (precisions * recalls) / (precisions + recalls + 1e-9)
best_idx = np.argmax(f1_scores[:-1])  # last point has no threshold
best_threshold = thresholds[best_idx]

print(f"Model: {best_name}")
print(f"Default threshold (0.5) vs F1-optimal threshold ({best_threshold:.3f}):\n")

for label, thresh in [("Default (0.5)", 0.5), ("F1-optimal", best_threshold)]:
    pred = (proba >= thresh).astype(int)
    print(f"--- {label} ---")
    print(f"  Accuracy:  {accuracy_score(y_test, pred):.3f}")
    print(f"  Precision: {precision_score(y_test, pred):.3f}")
    print(f"  Recall:    {recall_score(y_test, pred):.3f}")
    print(f"  F1:        {f1_score(y_test, pred):.3f}")

print(f"\nROC-AUC (threshold-independent): {roc_auc_score(y_test, proba):.3f}")

# --- Save deployment artifacts ---
joblib.dump(best_threshold, MODELS_DIR / 'heart_threshold.pkl')
joblib.dump(feature_columns, MODELS_DIR / 'heart_features.pkl')

print(f"\nSaved decision threshold to {MODELS_DIR / 'heart_threshold.pkl'}")
print(f"Saved feature list ({len(feature_columns)} columns) to {MODELS_DIR / 'heart_features.pkl'}")

# --- Simple predict function template for your API/script ---
print("\n" + "="*60)
print("Use this pattern in your API/prediction script:")
print("="*60)
print("""
model = joblib.load('models/heart_model.pkl')
scaler = joblib.load('models/heart_scaler.pkl')
threshold = joblib.load('models/heart_threshold.pkl')
feature_columns = joblib.load('models/heart_features.pkl')
model_name = joblib.load('models/heart_model_name.pkl')

def predict(raw_input_df):
    # raw_input_df must already be through the same cleaning/encoding pipeline
    X = raw_input_df[feature_columns]
    if 'Logistic Regression' in model_name:
        X = scaler.transform(X)
    proba = model.predict_proba(X)[:, 1][0]
    prediction = int(proba >= threshold)
    return {'prediction': prediction, 'probability': float(proba)}
""")