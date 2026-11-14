from fastapi.testclient import TestClient

from src import app as app_module
from src import auth


def test_diabetes_api_accepts_real_dataset_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, 'AUTH_DB', tmp_path / 'auth.sqlite3')
    auth.initialize_auth()
    with TestClient(app_module.app) as client:
        credentials = {'name': 'Dataset Tester', 'email': 'dataset@example.com', 'password': 'correct horse battery staple'}
        client.post('/auth/register', json=credentials)
        client.post('/auth/login', json=credentials)
        payload = {
            'gender': 'Female',
            'age': 54,
            'hypertension': 0,
            'heart_disease': 0,
            'smoking_history': 'No Info',
            'bmi': 27.32,
            'HbA1c_level': 6.6,
            'blood_glucose_level': 80,
        }
        response = client.post('/predict/diabetes', json=payload)
        assert response.status_code == 200, response.text
        data = response.json()
        assert 0.0 <= float(data['probability']) <= 1.0
        assert data['disease'] == 'Diabetes'
        assert data['risk_level'] in {'Low', 'Moderate', 'High'}
