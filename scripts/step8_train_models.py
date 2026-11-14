"""
STEP 8: Train and compare models
Builds on the train/test splits and scaler saved in step 7.
"""
from pathlib import Path
import pandas as pd
import joblib
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
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

models = {
    'Logistic Regression': LogisticRegression(max_iter=2000, random_state=42),
    'Random Forest': RandomForestClassifier(n_estimators=300, max_depth=6, random_state=42),
    'Gradient Boosting': GradientBoostingClassifier(n_estimators=200, max_depth=3, random_state=42),
}

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
results = {}
fitted_models = {}

for name, model in models.items():
    # Logistic Regression needs scaled input; tree models don't
    Xtr = X_train_scaled if name == 'Logistic Regression' else X_train
    Xte = X_test_scaled if name == 'Logistic Regression' else X_test

    cv_auc = cross_val_score(model, Xtr, y_train, cv=skf, scoring='roc_auc')
    model.fit(Xtr, y_train)
    proba = model.predict_proba(Xte)[:, 1]
    pred = model.predict(Xte)

    test_auc = roc_auc_score(y_test, proba)
    test_acc = accuracy_score(y_test, pred)

    results[name] = {'cv_auc_mean': cv_auc.mean(), 'cv_auc_std': cv_auc.std(),
                      'test_auc': test_auc, 'test_acc': test_acc}
    fitted_models[name] = model

    print(f"\n=== {name} ===")
    print(f"CV ROC-AUC: {cv_auc.mean():.3f} +/- {cv_auc.std():.3f}")
    print(f"Test ROC-AUC: {test_auc:.3f} | Test Accuracy: {test_acc:.3f}")

# Pick the best model by test ROC-AUC
best_name = max(results, key=lambda n: results[n]['test_auc'])
best_model = fitted_models[best_name]
print(f"\nBest model: {best_name} (Test ROC-AUC: {results[best_name]['test_auc']:.3f})")

# Save the best model — overwrites your existing heart_model.pkl
joblib.dump(best_model, MODELS_DIR / 'heart_model.pkl')
joblib.dump(best_name, MODELS_DIR / 'heart_model_name.pkl')
print(f"\nSaved best model to {MODELS_DIR / 'heart_model.pkl'}")