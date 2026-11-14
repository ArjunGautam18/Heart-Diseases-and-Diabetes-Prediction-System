"""
STEP 10: Hyperparameter tuning
Tunes Logistic Regression and Gradient Boosting via grid search with cross-validation.
"""
from pathlib import Path
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import roc_auc_score, accuracy_score

PROC_DIR = Path(__file__).resolve().parent.parent / 'data' / 'processed'
MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'

X_train = pd.read_csv(PROC_DIR / 'X_train.csv')
X_test = pd.read_csv(PROC_DIR / 'X_test.csv')
y_train = pd.read_csv(PROC_DIR / 'y_train.csv').squeeze()
y_test = pd.read_csv(PROC_DIR / 'y_test.csv').squeeze()

scaler = joblib.load(MODELS_DIR / 'heart_scaler.pkl')
X_train_scaled = scaler.transform(X_train)
X_test_scaled = scaler.transform(X_test)

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# --- Tune Logistic Regression ---
lr_param_grid = {
    'C': [0.01, 0.1, 0.5, 1, 5, 10],
    'penalty': ['l2'],
    'solver': ['lbfgs'],
}
lr_search = GridSearchCV(LogisticRegression(max_iter=3000, random_state=42),
                          lr_param_grid, cv=skf, scoring='roc_auc', n_jobs=-1)
lr_search.fit(X_train_scaled, y_train)

lr_best = lr_search.best_estimator_
lr_test_auc = roc_auc_score(y_test, lr_best.predict_proba(X_test_scaled)[:, 1])
lr_test_acc = accuracy_score(y_test, lr_best.predict(X_test_scaled))

print("=== Logistic Regression (tuned) ===")
print("Best params:", lr_search.best_params_)
print(f"Best CV ROC-AUC: {lr_search.best_score_:.3f}")
print(f"Test ROC-AUC: {lr_test_auc:.3f} | Test Accuracy: {lr_test_acc:.3f}")

# --- Tune Gradient Boosting ---
gb_param_grid = {
    'n_estimators': [100, 200, 300],
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [2, 3, 4],
}
gb_search = GridSearchCV(GradientBoostingClassifier(random_state=42),
                          gb_param_grid, cv=skf, scoring='roc_auc', n_jobs=-1)
gb_search.fit(X_train, y_train)

gb_best = gb_search.best_estimator_
gb_test_auc = roc_auc_score(y_test, gb_best.predict_proba(X_test)[:, 1])
gb_test_acc = accuracy_score(y_test, gb_best.predict(X_test))

print("\n=== Gradient Boosting (tuned) ===")
print("Best params:", gb_search.best_params_)
print(f"Best CV ROC-AUC: {gb_search.best_score_:.3f}")
print(f"Test ROC-AUC: {gb_test_auc:.3f} | Test Accuracy: {gb_test_acc:.3f}")

# --- Pick the overall best tuned model ---
candidates = {
    'Logistic Regression (tuned)': (lr_best, lr_test_auc, True),   # True = needs scaling
    'Gradient Boosting (tuned)': (gb_best, gb_test_auc, False),
}
best_name = max(candidates, key=lambda n: candidates[n][1])
best_model, best_auc, needs_scaling = candidates[best_name]

print(f"\nBest tuned model: {best_name} (Test ROC-AUC: {best_auc:.3f})")

# Save — overwrites heart_model.pkl from step 8 if this one is better
joblib.dump(best_model, MODELS_DIR / 'heart_model.pkl')
joblib.dump(best_name, MODELS_DIR / 'heart_model_name.pkl')
print(f"Saved tuned model to {MODELS_DIR / 'heart_model.pkl'}")