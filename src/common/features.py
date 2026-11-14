"""Feature engineering shared by preprocessing, training and the API.

Keeping a single implementation here guarantees that the features produced at
inference time match the ones the models were trained on.
"""
import os

import pandas as pd

from src.common.paths import RAW_DIR

HEART_COLUMNS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num"
]

HEART_ENGINEERED_COLUMNS = [
    "Age_Group", "Age_Over55", "High_BP", "High_Chol",
    "Thalach_Low", "Age_Treach", "Chol_Thalach"
]


def load_heart_dataframe(path=None):
    """Read heart.data, binarise the target and median-impute numeric columns."""
    df = pd.read_csv(
        path or os.path.join(RAW_DIR, "heart.data"),
        header=None, names=HEART_COLUMNS, na_values="?"
    )

    df["num"] = (df["num"] > 0).astype(int)
    df = df.dropna(subset=["num"])

    numeric_cols = df.columns.drop("num")
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())

    return df


def engineer_heart_features(df):
    """Add age/BP/cholesterol buckets and interaction terms to heart data."""
    df = df.copy()

    df["Age_Group"] = pd.cut(df["age"], bins=[0, 40, 55, 70, 120], labels=[0, 1, 2, 3]).astype(float)
    df["Age_Over55"] = (df["age"] >= 55).astype(int)
    df["High_BP"] = (df["trestbps"] >= 130).astype(int)
    df["High_Chol"] = (df["chol"] >= 240).astype(int)
    df["Thalach_Low"] = (df["thalach"] < 100).astype(int)
    df["Age_Treach"] = df["age"] * df["trestbps"] / 100.0
    df["Chol_Thalach"] = df["chol"] * df["thalach"] / 1000.0

    return df


def engineer_diabetes_features(df):
    """Add glucose/BMI/age indicators, interactions and a clinical risk score."""
    df = df.copy()

    if "Glucose" in df.columns:
        df["Glucose_Normal"]   = (df["Glucose"] < 100).astype(int)
        df["Glucose_Prediab"]  = ((df["Glucose"] >= 100) & (df["Glucose"] < 126)).astype(int)
        df["Glucose_Diabetic"] = (df["Glucose"] >= 126).astype(int)

    if "BMI" in df.columns:
        df["BMI_Category"] = pd.cut(
            df["BMI"], bins=[0, 18.5, 25, 30, 100], labels=[0, 1, 2, 3]
        ).astype(float)
        df["BMI_Obese"]    = (df["BMI"] >= 30).astype(int)
        df["BMI_Severe"]   = (df["BMI"] >= 35).astype(int)

    if "Age" in df.columns:
        df["Age_Group"]  = pd.cut(
            df["Age"], bins=[0, 30, 45, 60, 120], labels=[0, 1, 2, 3]
        ).astype(float)
        df["Age_Over45"] = (df["Age"] >= 45).astype(int)

    if "Glucose" in df.columns and "BMI" in df.columns:
        df["Glucose_BMI"] = df["Glucose"] * df["BMI"] / 100

    if "Glucose" in df.columns and "Age" in df.columns:
        df["Glucose_Age"] = df["Glucose"] * df["Age"] / 100

    if "Glucose" in df.columns and "Insulin" in df.columns:
        df["Insulin_Resistance"] = df["Glucose"] * df["Insulin"] / 1000
        df["Insulin_Zero"]       = (df["Insulin"] == 0).astype(int)

    if "BloodPressure" in df.columns and "BMI" in df.columns:
        df["BP_BMI"] = df["BloodPressure"] * df["BMI"] / 100

    if "DiabetesPedigreeFunction" in df.columns and "Age" in df.columns:
        df["Pedigree_Age"] = df["DiabetesPedigreeFunction"] * df["Age"]

    risk = pd.Series(0.0, index=df.index)
    if "Glucose" in df.columns:
        risk += (df["Glucose"] >= 126).astype(float) * 3.0
        risk += (df["Glucose"] >= 100).astype(float) * 1.5
    if "BMI" in df.columns:
        risk += (df["BMI"] >= 30).astype(float) * 2.0
        risk += (df["BMI"] >= 35).astype(float) * 1.0
    if "Age" in df.columns:
        risk += (df["Age"] >= 45).astype(float) * 1.5
    if "DiabetesPedigreeFunction" in df.columns:
        risk += (df["DiabetesPedigreeFunction"] > 0.5).astype(float) * 1.5
    if "Pregnancies" in df.columns:
        risk += (df["Pregnancies"] >= 4).astype(float) * 1.0
    df["Clinical_Risk_Score"] = risk

    return df
