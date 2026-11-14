"""Train/test splitting, scaling and processed-CSV persistence."""
import os

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.common.paths import PROCESSED_DIR

TEST_SIZE = 0.2
RANDOM_STATE = 42


def split_and_scale(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """Stratified split followed by a StandardScaler fitted on the training rows."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "scaler": scaler,
        "X_train_scaled": X_train_scaled,
        "X_test_scaled": X_test_scaled,
    }


def save_processed(prefix, split, columns):
    """Write the scaled train/test matrices and targets to data/processed."""
    pd.DataFrame(split["X_train_scaled"], columns=columns).to_csv(
        os.path.join(PROCESSED_DIR, f"{prefix}_X_train.csv"), index=False)
    pd.DataFrame(split["X_test_scaled"], columns=columns).to_csv(
        os.path.join(PROCESSED_DIR, f"{prefix}_X_test.csv"), index=False)
    split["y_train"].to_csv(os.path.join(PROCESSED_DIR, f"{prefix}_y_train.csv"), index=False)
    split["y_test"].to_csv(os.path.join(PROCESSED_DIR, f"{prefix}_y_test.csv"), index=False)


def load_processed(prefix):
    """Read back the scaled train/test matrices and targets."""
    return (
        pd.read_csv(os.path.join(PROCESSED_DIR, f"{prefix}_X_train.csv")),
        pd.read_csv(os.path.join(PROCESSED_DIR, f"{prefix}_y_train.csv")).squeeze(),
        pd.read_csv(os.path.join(PROCESSED_DIR, f"{prefix}_X_test.csv")),
        pd.read_csv(os.path.join(PROCESSED_DIR, f"{prefix}_y_test.csv")).squeeze(),
    )
