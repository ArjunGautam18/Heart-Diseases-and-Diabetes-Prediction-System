import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.common.artifacts import diabetes_raw_features_path, load_diabetes_artifacts
from src.common.paths import MODELS_DIR

print('model folder:', MODELS_DIR)
print('files:', sorted(os.listdir(MODELS_DIR)))
print('raw_path:', diabetes_raw_features_path())

artifacts = load_diabetes_artifacts()
raw_feats = artifacts["raw_features"]
model_feats = artifacts["model_features"]
model = artifacts["model"]

print('raw_feats type:', type(raw_feats), 'len:', len(raw_feats))
print(raw_feats)
print('model_feats type:', type(model_feats), 'len:', len(model_feats))
print(model_feats)
print('model type:', type(model))
if hasattr(model, 'feature_names_in_'):
    print('feature_names_in_:', model.feature_names_in_)
if hasattr(model, 'coef_'):
    print('coef shape:', model.coef_.shape)
