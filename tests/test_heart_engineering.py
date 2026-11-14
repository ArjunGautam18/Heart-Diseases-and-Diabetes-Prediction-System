import pandas as pd
from src.common.heart_pipeline import engineer_heart_features


def test_heart_engineering_adds_risk_signals_for_high_risk_patient():
    row = pd.DataFrame([
        {
            'age': 67, 'sex': 'Male', 'cp': 'typical angina', 'trestbps': 160,
            'chol': 220, 'thalch': 88, 'exang': 1, 'oldpeak': 3.0,
            'fbs': 0, 'restecg': 'normal', 'slope': 'flat', 'ca': 1, 'thal': 'normal',
        }
    ])

    engineered = engineer_heart_features(row)

    assert engineered['max_hr_reserve'].iloc[0] == 65
    assert engineered['cp_typical angina'].iloc[0] == 1
    assert engineered['high_oldpeak'].iloc[0] == 1
    assert engineered['ca_present'].iloc[0] == 1
