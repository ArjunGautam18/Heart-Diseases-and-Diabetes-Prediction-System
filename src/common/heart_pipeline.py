"""Shared heart-disease feature engineering for training and inference."""

import numpy as np
import pandas as pd


def engineer_heart_features(df: pd.DataFrame) -> pd.DataFrame:
    """Transform raw heart records into the numeric training feature matrix."""
    result = df.copy()

    for column in ["sex", "cp", "restecg", "slope", "thal", "dataset"]:
        if column in result:
            result[column] = result[column].astype(str).str.strip()

    for column in ["trestbps", "chol", "fbs", "restecg", "thalch", "exang",
                   "oldpeak", "slope", "ca", "thal"]:
        result[f"{column}_missing"] = result[column].isna().astype(int) if column in result else 0

    for column in ["age", "trestbps", "chol", "thalch", "oldpeak", "ca"]:
        if column in result:
            result[column] = pd.to_numeric(result[column], errors="coerce")
            result[column] = result[column].fillna(result[column].median())

    for column in ["fbs", "exang"]:
        if column in result:
            result[column] = result[column].fillna(0).astype(int)

    for column in ["restecg", "slope", "thal"]:
        if column in result:
            mode = result[column].mode(dropna=True)
            result[column] = result[column].fillna(mode.iloc[0] if not mode.empty else "normal").str.lower()

    result["cp"] = result["cp"].fillna("asymptomatic").str.lower()
    result["dataset"] = result.get("dataset", pd.Series("Cleveland", index=result.index)).fillna("Cleveland")
    result["chol_per_age"] = result["chol"] / result["age"].replace(0, np.nan)
    result["chol_per_age"] = result["chol_per_age"].fillna(result["chol_per_age"].median())
    result["max_hr_reserve"] = 220 - result["age"] - result["thalch"]
    result["bp_chol_ratio"] = result["trestbps"] / result["chol"].replace(0, np.nan)
    result["bp_chol_ratio"] = result["bp_chol_ratio"].fillna(result["bp_chol_ratio"].median())
    result["high_oldpeak"] = (result["oldpeak"] >= 2).astype(int)
    result["ca_present"] = (result["ca"] > 0).astype(int)
    result["age_group"] = pd.cut(
        result["age"], bins=[0, 40, 50, 60, 70, 100],
        labels=["<40", "40-50", "50-60", "60-70", "70+"],
    )

    category_values = {
        "sex": ["Female", "Male"],
        "dataset": ["Cleveland", "Hungary", "Switzerland", "VA Long Beach"],
        "cp": ["asymptomatic", "atypical angina", "non-anginal", "typical angina"],
        "restecg": ["lv hypertrophy", "normal", "st-t abnormality"],
        "slope": ["downsloping", "flat", "upsloping"],
        "thal": ["fixed defect", "normal", "reversable defect"],
        "age_group": ["<40", "40-50", "50-60", "60-70", "70+"],
    }
    for column, categories in category_values.items():
        result[column] = pd.Categorical(result[column], categories=categories)

    encoded = pd.get_dummies(
        result,
        columns=["sex", "dataset", "cp", "restecg", "slope", "thal", "age_group"],
        drop_first=True,
    )
    return encoded.select_dtypes(include=[np.number, bool]).astype(float)


def transform_heart_input(data: dict, expected_columns: list[str]) -> pd.DataFrame:
    """Transform one API payload and require an exact saved feature contract."""
    row = pd.DataFrame([data])
    transformed = engineer_heart_features(row)
    missing = sorted(set(expected_columns) - set(transformed.columns))
    if missing:
        raise ValueError(f"Heart artifact requires unavailable features: {missing}")
    return transformed.reindex(columns=expected_columns)