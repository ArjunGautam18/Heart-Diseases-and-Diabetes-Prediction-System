"""
STEP 7: Train/test split and feature scaling
Builds on data/processed/heart_step6_encoded.csv from step 6.
"""
from pathlib import Path
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

IN_PATH = Path(__file__).resolve().parent.parent / 'data' / 'processed' / 'heart_step6_encoded.csv'
df = pd.read_csv(IN_PATH)

# Drop columns that shouldn't be used as predictors:
# 'num' is the raw 0-4 severity (we predict 'target' instead, to avoid leaking the answer)
X = df.drop(columns=['num', 'target'])
y = df['target']

print("Feature matrix shape:", X.shape)
print("Target shape:", y.shape)

# 80/20 split, stratified so both sets keep the same ~55/45 class balance
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

print("\nTrain shape:", X_train.shape, "| Test shape:", X_test.shape)
print("Train target balance:\n", y_train.value_counts(normalize=True).round(3))
print("Test target balance:\n", y_test.value_counts(normalize=True).round(3))

# Scale features — needed for Logistic Regression; harmless for tree models.
# IMPORTANT: fit the scaler on TRAIN only, then apply it to test (no leakage).
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Save everything step 8 (model training) will need
OUT_DIR = Path(__file__).resolve().parent.parent / 'data' / 'processed'
OUT_DIR.mkdir(parents=True, exist_ok=True)

X_train.to_csv(OUT_DIR / 'X_train.csv', index=False)
X_test.to_csv(OUT_DIR / 'X_test.csv', index=False)
y_train.to_csv(OUT_DIR / 'y_train.csv', index=False)
y_test.to_csv(OUT_DIR / 'y_test.csv', index=False)

MODELS_DIR = Path(__file__).resolve().parent.parent / 'models'
MODELS_DIR.mkdir(parents=True, exist_ok=True)
joblib.dump(scaler, MODELS_DIR / 'heart_scaler.pkl')
joblib.dump(list(X.columns), MODELS_DIR / 'heart_raw_columns.pkl')

print(f"\nSaved train/test splits to {OUT_DIR}")
print(f"Saved fitted scaler to {MODELS_DIR / 'heart_scaler.pkl'}")