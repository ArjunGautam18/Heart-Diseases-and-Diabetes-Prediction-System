"""
STEP 6 (Diabetes): Stratified train/test split + scaling
"""

from pathlib import Path
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "diabetes_ready.csv"
df = pd.read_csv(DATA_PATH)

numeric_features = [
    "age", "bmi", "HbA1c_level", "blood_glucose_level",
    "hypertension", "heart_disease"
]
categorical_features = [
    "gender", "smoking_history",
    "hba1c_band", "glucose_band",
    "bmi_category", "age_group"
]

X = df[numeric_features + categorical_features]
y = df["diabetes"]

# 80/20 stratified split (critical because of ~91.5% / 8.5% imbalance)
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print(f"Train shape: {X_train.shape}")
print(f"Test  shape: {X_test.shape}")
print(f"Train diabetes rate: {y_train.mean():.4f}")
print(f"Test  diabetes rate: {y_test.mean():.4f}")

# Preprocessor
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), numeric_features),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical_features)
    ]
)

X_train_processed = preprocessor.fit_transform(X_train)
X_test_processed  = preprocessor.transform(X_test)

# Save everything
ARTIFACTS = Path(__file__).resolve().parent.parent / "models" / "diabetes"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

joblib.dump(preprocessor, ARTIFACTS / "preprocessor.joblib")
joblib.dump((X_train, X_test, y_train, y_test), ARTIFACTS / "splits.joblib")
joblib.dump((X_train_processed, X_test_processed), ARTIFACTS / "processed_splits.joblib")

print(f"\nArtifacts saved to → {ARTIFACTS}")