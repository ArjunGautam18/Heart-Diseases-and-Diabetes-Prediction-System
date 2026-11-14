import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Ensure project root is on sys.path so we can import src modules
sys.path.insert(0, BASE_DIR)

from src.common.artifacts import build_feature_row, load_diabetes_artifacts
from src.common.features import engineer_diabetes_features
from src.common.risk import risk_level

artifacts = load_diabetes_artifacts()
raw_feats = artifacts["raw_features"]

sample = {f: 0 for f in raw_feats}
sample.update({
    "Glucose": 500,
    "BMI": 30,
    "Age": 60,
    "Insulin": 100,
    "Pregnancies": 2,
    "DiabetesPedigreeFunction": 0.5,
})

raw_row = build_feature_row(sample, raw_feats)
print("Raw row:")
print(raw_row.to_dict(orient='records')[0])

engineered = engineer_diabetes_features(raw_row)
print("\nEngineered columns:")
print(list(engineered.columns))
print(engineered.to_dict(orient='records')[0])

engineered_sel = engineered[artifacts["model_features"]]
print("\nSelected model features (ordered):")
print(engineered_sel.to_dict(orient='records')[0])

scaled = artifacts["scaler"].transform(engineered_sel)
print("\nScaled vector:")
print(scaled)

prob = float(artifacts["model"].predict_proba(scaled)[0][1])
thresh = artifacts["threshold"]
print(f"\nPredicted probability: {prob:.6f}")
print(f"Threshold: {thresh}")
print(f"Prediction (>=threshold): {int(prob >= thresh)}")
print(f"Risk level heuristic: {risk_level(prob)}")
