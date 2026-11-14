import json
from pathlib import Path

import joblib

from src.preprocessing import load_diabetes_dataset, load_heart_dataset, prepare_diabetes_data, prepare_heart_data
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / 'models'


def load_pipeline(path):
    return joblib.load(path)


def evaluate_model(name, X, y, pipeline_path, metadata_path):
    pipeline = load_pipeline(pipeline_path)
    with open(metadata_path, 'r', encoding='utf-8') as fh:
        metadata = json.load(fh)
    probabilities = pipeline.predict_proba(X)[:, 1]
    threshold = metadata.get('threshold', 0.5)
    predictions = (probabilities >= threshold).astype(int)
    metrics = {
        'accuracy': accuracy_score(y, predictions),
        'precision': precision_score(y, predictions, zero_division=0),
        'recall': recall_score(y, predictions, zero_division=0),
        'f1': f1_score(y, predictions, zero_division=0),
        'roc_auc': roc_auc_score(y, probabilities),
        'confusion_matrix': confusion_matrix(y, predictions),
    }
    print(f'## {name}')
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall: {metrics['recall']:.4f}")
    print(f"F1 Score: {metrics['f1']:.4f}")
    print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"Threshold: {threshold:.3f}")
    print('Confusion matrix:')
    print(metrics['confusion_matrix'])
    print()


if __name__ == '__main__':
    heart_X, heart_y = prepare_heart_data()
    diabetes_X, diabetes_y = prepare_diabetes_data()
    evaluate_model(
        'Heart Disease Model',
        heart_X,
        heart_y,
        MODELS_DIR / 'heart_pipeline.joblib',
        MODELS_DIR / 'heart_metadata.json',
    )
    evaluate_model(
        'Diabetes Model',
        diabetes_X,
        diabetes_y,
        MODELS_DIR / 'diabetes_pipeline.joblib',
        MODELS_DIR / 'diabetes_metadata.json',
    )
