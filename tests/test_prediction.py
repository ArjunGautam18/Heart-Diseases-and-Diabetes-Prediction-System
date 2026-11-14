import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src import auth


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(auth, "AUTH_DB", tmp_path / "auth.sqlite3")
    auth.initialize_auth()
    with TestClient(app_module.app) as test_client:
        credentials = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "correct horse battery staple",
        }
        assert test_client.post("/auth/register", json=credentials).status_code == 201
        assert test_client.post("/auth/login", json=credentials).status_code == 200
        yield test_client


def heart_payload():
    return {
        "age": 48, "sex": "Male", "cp": "typical angina", "trestbps": 130,
        "chol": 220, "fbs": 0, "restecg": "normal", "thalch": 160,
        "exang": 0, "oldpeak": 1.2, "slope": "flat", "ca": 0, "thal": "normal",
    }


def diabetes_payload():
    return {
        "gender": "Female", "age": 42, "hypertension": 0, "heart_disease": 0,
        "smoking_history": "never", "bmi": 28.5, "HbA1c_level": 5.5,
        "blood_glucose_level": 120,
    }


def test_authentication_is_required():
    with TestClient(app_module.app) as test_client:
        response = test_client.post("/predict/heart", json=heart_payload())
        assert response.status_code == 401


def test_authentication_round_trip(client):
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_heart_prediction_contract(client):
    response = client.post("/predict/heart", json=heart_payload())
    assert response.status_code == 200
    assert 0 <= response.json()["probability"] <= 1


def test_diabetes_prediction_contract(client):
    response = client.post("/predict/diabetes", json=diabetes_payload())
    assert response.status_code == 200
    assert 0 <= response.json()["probability"] <= 1


def test_invalid_clinical_values_are_rejected(client):
    payload = diabetes_payload()
    payload["age"] = -1
    response = client.post("/predict/diabetes", json=payload)
    assert response.status_code == 422


def test_logout_removes_session(client):
    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401
