
"""
Train models for Heart Disease prediction with light feature engineering.
Trains Logistic Regression, Random Forest, XGBoost — picks best by CV F1.

Run from project root: python src/train_heart.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report
from xgboost import XGBClassifier

from src.common.datasets import save_processed, split_and_scale
from src.common.features import (
    HEART_ENGINEERED_COLUMNS, engineer_heart_features, load_heart_dataframe
)
from src.common.metrics import compute_metrics, print_metrics, save_evaluation_panel, save_roc_curve
from src.common.paths import MODELS_DIR, PROCESSED_DIR, ensure_dirs

CLASS_LABELS = ["No Disease", "Disease"]

print("="*50)
print("Training models for: HEART DISEASE (with feature engineering)")
print("="*50)

df = load_heart_dataframe()
df_eng = engineer_heart_features(df)

# Original numeric features plus the engineered ones, without duplicates
feature_cols = [c for c in df.columns if c != "num"] + HEART_ENGINEERED_COLUMNS
feature_cols = [c for i, c in enumerate(feature_cols) if c in df_eng.columns and c not in feature_cols[:i]]

X = df_eng[feature_cols]
y = df_eng["num"]

split = split_and_scale(X, y)
X_train_scaled, X_test_scaled = split["X_train_scaled"], split["X_test_scaled"]
y_train, y_test = split["y_train"], split["y_test"]

ensure_dirs(MODELS_DIR, PROCESSED_DIR)
joblib.dump(split["scaler"], os.path.join(MODELS_DIR, "heart_scaler.pkl"))
joblib.dump(feature_cols, os.path.join(MODELS_DIR, "heart_features.pkl"))
save_processed("heart", split, X.columns)

print(f"Features used ({len(feature_cols)}): {feature_cols}")

# Train candidate models on scaled training data
candidates = {
    "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42),
    "Random Forest": RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42),
    "XGBoost": XGBClassifier(n_estimators=200, max_depth=5, learning_rate=0.1,
                               eval_metric='logloss', random_state=42)
}

results = {}
for name, model in candidates.items():
    scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='f1')
    results[name] = scores.mean()
    print(f"  {name}: CV F1 = {scores.mean():.4f} (+/- {scores.std():.4f})")

best_name = max(results, key=results.get)
best_model = candidates[best_name]
print(f"\nBest model: {best_name} (F1={results[best_name]:.4f})")

best_model.fit(X_train_scaled, y_train)

proba = best_model.predict_proba(X_test_scaled)[:, 1]
pred = (proba >= 0.5).astype(int)
metrics = compute_metrics(y_test, pred, proba)

print("\n" + "=" * 62)
print("  FINAL HEART TEST RESULTS")
print("=" * 62)
print_metrics(metrics)
print(f"\n{classification_report(y_test, pred, target_names=CLASS_LABELS, zero_division=0)}")

save_evaluation_panel(
    y_test, proba, metrics,
    model_name=best_name,
    disease_label="Heart Disease",
    class_labels=CLASS_LABELS,
    output_paths=[os.path.join(PROCESSED_DIR, "heart_evaluation_plot.png")],
)
save_roc_curve(
    y_test, proba, metrics["auc"],
    title="Heart Disease: ROC Curve",
    output_path=os.path.join(PROCESSED_DIR, "heart_roc_curve.png"),
)

joblib.dump(best_model, os.path.join(MODELS_DIR, "heart_model.pkl"))
joblib.dump(best_name, os.path.join(MODELS_DIR, "heart_model_name.pkl"))
print("Saved -> models/heart_model.pkl")
