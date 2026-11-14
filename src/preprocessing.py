import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / 'data'
RAW_DIR = DATA_DIR / 'raw'
MODELS_DIR = ROOT / 'models'
PROCESSED_DIR = DATA_DIR / 'processed'

HEART_FEATURES = [
    'age', 'sex', 'cp', 'trestbps', 'chol', 'fbs', 'restecg',
    'thalach', 'exang', 'oldpeak', 'slope', 'ca', 'thal'
]

DIABETES_FEATURES = [
    'Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness',
    'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age'
]


def ensure_dirs():
    MODELS_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)


def load_heart_dataset():
    path = RAW_DIR / 'heart.data'
    names = HEART_FEATURES + ['target']
    df = pd.read_csv(path, header=None, names=names)
    df['target'] = df['target'].astype(int)
    df = df.replace('?', np.nan)
    for col in HEART_FEATURES:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['target'])
    df[HEART_FEATURES] = df[HEART_FEATURES].apply(pd.to_numeric, errors='coerce')
    return df


def prepare_heart_data():
    df = load_heart_dataset()
    X = df[HEART_FEATURES].copy()
    y = (df['target'] > 0).astype(int)
    return X, y


def load_diabetes_dataset():
    path = RAW_DIR / 'diabetes.csv'
    df = pd.read_csv(path)
    missing_cols = ['Glucose', 'BloodPressure', 'BMI', 'SkinThickness', 'Insulin']
    for col in missing_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df.loc[df[col] == 0, col] = np.nan
    df = df.dropna(subset=['Outcome'])
    return df


def prepare_diabetes_data():
    df = load_diabetes_dataset()
    X = df[DIABETES_FEATURES].copy()
    y = df['Outcome'].astype(int)
    return X, y


def make_preprocessor(feature_names):
    return ColumnTransformer(
        transformers=[
            (
                'numeric',
                Pipeline([
                    ('imputer', SimpleImputer(strategy='median')),
                    ('scaler', StandardScaler()),
                ]),
                feature_names,
            )
        ],
        remainder='drop',
    )


def build_pipeline(model):
    return Pipeline([
        ('preprocess', None),
        ('model', model),
    ])


def select_threshold(y_true, probabilities, score_function='f1'):
    best_threshold = 0.5
    best_score = -1.0
    for threshold in np.linspace(0.3, 0.7, 81):
        predictions = (probabilities >= threshold).astype(int)
        if score_function == 'f1':
            score = f1_score(y_true, predictions)
        elif score_function == 'precision':
            score = precision_score(y_true, predictions, zero_division=0)
        elif score_function == 'recall':
            score = recall_score(y_true, predictions, zero_division=0)
        else:
            score = f1_score(y_true, predictions)
        if score > best_score:
            best_score = score
            best_threshold = threshold
    return float(best_threshold), best_score


def compute_classification_metrics(y_true, y_pred, probabilities):
    return {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred, zero_division=0),
        'recall': recall_score(y_true, y_pred, zero_division=0),
        'f1': f1_score(y_true, y_pred, zero_division=0),
        'roc_auc': roc_auc_score(y_true, probabilities),
        'confusion_matrix': confusion_matrix(y_true, y_pred),
    }


def save_metadata(path, payload):
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2)


def load_metadata(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def train_test_split_data(X, y, test_size=0.2, random_state=42):
    return train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y,
    )
