import sys
from pathlib import Path
import pandas as pd
import joblib
from sklearn.metrics import precision_recall_curve, f1_score

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parent
sys.path.append(str(SCRIPTS_DIR))

ARTIFACTS_DIR = ROOT / "models" / "diabetes"
model_path = ARTIFACTS_DIR / "logistic_model.joblib"
if not model_path.exists():
    model_path = ARTIFACTS_DIR / "diabetes_model.joblib"
model = joblib.load(model_path)

df = pd.read_csv(ROOT / "data" / "raw" / "diabetes_prediction_dataset.csv")
from sklearn.model_selection import train_test_split
_, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df["diabetes"])

FEATURE_COLUMNS = ["age", "hypertension", "heart_disease", "bmi", "HbA1c_level",
                    "blood_glucose_level", "gender", "smoking_history"]
X = test_df.copy()
X["gender"] = X["gender"].astype(str).str.strip().str.title()
X["smoking_history"] = X["smoking_history"].astype(str).str.strip()
y_true = test_df["diabetes"].values

proba = model.predict_proba(X[FEATURE_COLUMNS])[:, 1]

precisions, recalls, thresholds = precision_recall_curve(y_true, proba)

print(f"{'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F1':>10}")
for t in [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]:
    preds = (proba >= t).astype(int)
    f1 = f1_score(y_true, preds)
    p = ((preds == 1) & (y_true == 1)).sum() / max((preds == 1).sum(), 1)
    r = ((preds == 1) & (y_true == 1)).sum() / max((y_true == 1).sum(), 1)
    print(f"{t:>10.2f} {p:>10.4f} {r:>10.4f} {f1:>10.4f}")