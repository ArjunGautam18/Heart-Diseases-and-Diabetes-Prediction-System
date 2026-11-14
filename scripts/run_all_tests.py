"""
Run All Tests — Smart Healthcare System
Tests predict_diabetes(), predict_heart(), and optionally the live API endpoints.

Usage:
    python -u scripts/run_all_tests.py            # local function tests only
    python -u scripts/run_all_tests.py --api       # also test live API (requires uvicorn running)
"""

import sys
import traceback
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPTS_DIR))

from predict_diabetes import predict_diabetes
from predict_heart import predict_heart

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"

results = []


def record(name, passed, detail=""):
    results.append((name, passed, detail))
    status = PASS if passed else FAIL
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


def run_test(name, fn):
    try:
        fn()
    except Exception as e:
        record(name, False, f"Exception: {e}")
        traceback.print_exc()


# ------------------- Diabetes Tests -------------------

def test_diabetes_low_risk():
    sample = {
        "gender": "Female",
        "age": 25,
        "hypertension": 0,
        "heart_disease": 0,
        "smoking_history": "never",
        "bmi": 21.0,
        "HbA1c_level": 4.8,
        "blood_glucose_level": 90,
    }
    result = predict_diabetes(sample)
    assert "prediction" in result, "Missing 'prediction' key"
    assert "probability" in result, "Missing 'probability' key"
    assert "risk_level" in result, "Missing 'risk_level' key"
    assert "health_score" in result, "Missing 'health_score' key"
    assert 0 <= result["probability"] <= 1, "Probability out of range"
    record("Diabetes: low-risk profile returns valid structure", True,
           f"risk={result['risk_level']}, prob={result['probability']}")


def test_diabetes_high_risk():
    sample = {
        "gender": "Male",
        "age": 65,
        "hypertension": 1,
        "heart_disease": 1,
        "smoking_history": "current",
        "bmi": 38.0,
        "HbA1c_level": 8.5,
        "blood_glucose_level": 220,
    }
    result = predict_diabetes(sample)
    record("Diabetes: high-risk profile returns valid structure", True,
           f"risk={result['risk_level']}, prob={result['probability']}")


def test_diabetes_different_inputs_give_different_outputs():
    low = predict_diabetes({
        "gender": "Female", "age": 22, "hypertension": 0, "heart_disease": 0,
        "smoking_history": "never", "bmi": 20.0, "HbA1c_level": 4.5,
        "blood_glucose_level": 85,
    })
    high = predict_diabetes({
        "gender": "Male", "age": 70, "hypertension": 1, "heart_disease": 1,
        "smoking_history": "current", "bmi": 40.0, "HbA1c_level": 9.0,
        "blood_glucose_level": 250,
    })
    assert low["probability"] != high["probability"], \
        "Different inputs produced identical probability — likely a preprocessing bug"
    record("Diabetes: distinct inputs yield distinct probabilities", True,
           f"low={low['probability']}, high={high['probability']}")


def test_diabetes_missing_field_raises():
    incomplete = {"gender": "Female", "age": 30}
    try:
        predict_diabetes(incomplete)
        record("Diabetes: missing fields raise an error", False, "No exception raised")
    except Exception:
        record("Diabetes: missing fields raise an error", True)


# ------------------- Heart Tests -------------------

def test_heart_low_risk():
    sample = {
        "age": 30, "sex": "Female", "cp": "typical angina",
        "trestbps": 110, "chol": 170, "fbs": 0,
        "restecg": "normal", "thalch": 180, "exang": 0,
        "oldpeak": 0, "slope": "upsloping", "ca": 0, "thal": "normal",
    }
    result = predict_heart(sample)
    assert "prediction" in result
    assert "probability" in result
    assert "risk_level" in result
    assert "health_score" in result
    assert 0 <= result["probability"] <= 1
    record("Heart: low-risk profile returns valid structure", True,
           f"risk={result['risk_level']}, prob={result['probability']}")


def test_heart_high_risk():
    sample = {
        "age": 63, "sex": "Male", "cp": "asymptomatic",
        "trestbps": 160, "chol": 280, "fbs": 1,
        "restecg": "lv hypertrophy", "thalch": 110, "exang": 1,
        "oldpeak": 3.0, "slope": "flat", "ca": 3, "thal": "reversable defect",
    }
    result = predict_heart(sample)
    record("Heart: high-risk profile returns valid structure", True,
           f"risk={result['risk_level']}, prob={result['probability']}")


def test_heart_different_inputs_give_different_outputs():
    low = predict_heart({
        "age": 28, "sex": "Female", "cp": "typical angina",
        "trestbps": 105, "chol": 160, "fbs": 0,
        "restecg": "normal", "thalch": 185, "exang": 0,
        "oldpeak": 0, "slope": "upsloping", "ca": 0, "thal": "normal",
    })
    high = predict_heart({
        "age": 68, "sex": "Male", "cp": "asymptomatic",
        "trestbps": 170, "chol": 300, "fbs": 1,
        "restecg": "st-t abnormality", "thalch": 100, "exang": 1,
        "oldpeak": 3.5, "slope": "flat", "ca": 3, "thal": "reversable defect",
    })
    assert low["probability"] != high["probability"], \
        "Different inputs produced identical probability — likely a preprocessing bug"
    record("Heart: distinct inputs yield distinct probabilities", True,
           f"low={low['probability']}, high={high['probability']}")


def test_heart_same_input_is_deterministic():
    sample = {
        "age": 54, "sex": "Male", "cp": "typical angina",
        "trestbps": 140, "chol": 250, "fbs": 0,
        "restecg": "normal", "thalch": 150, "exang": 0,
        "oldpeak": 1.0, "slope": "flat", "ca": 0, "thal": "normal",
    }
    r1 = predict_heart(sample)
    r2 = predict_heart(sample)
    assert r1["probability"] == r2["probability"], \
        "Same input gave different results across calls — non-deterministic bug"
    record("Heart: identical input is deterministic across calls", True)


def test_heart_missing_optional_fields_uses_defaults():
    minimal = {"age": 50, "sex": "Male", "cp": "typical angina"}
    try:
        result = predict_heart(minimal)
        record("Heart: partial input falls back to defaults without crashing", True,
               f"risk={result['risk_level']}")
    except Exception as e:
        record("Heart: partial input falls back to defaults without crashing", False, str(e))


# ------------------- Optional Live API Tests -------------------

def test_api_endpoints():
    import requests
    base = "http://127.0.0.1:8000"

    def check(name, method, path, payload=None):
        try:
            if method == "GET":
                r = requests.get(f"{base}{path}", timeout=5)
            else:
                r = requests.post(f"{base}{path}", json=payload, timeout=10)
            ok = r.status_code == 200
            record(name, ok, f"status={r.status_code}")
        except Exception as e:
            record(name, False, f"Request failed: {e}")

    check("API: /health returns 200", "GET", "/health")

    check("API: /predict/diabetes returns 200", "POST", "/predict/diabetes", {
        "gender": "Female", "age": 40, "hypertension": 0, "heart_disease": 0,
        "smoking_history": "never", "bmi": 24.0, "HbA1c_level": 5.2,
        "blood_glucose_level": 100,
    })

    check("API: /predict/heart returns 200", "POST", "/predict/heart", {
        "age": 45, "sex": "Male", "cp": "typical angina",
        "trestbps": 130, "chol": 220, "fbs": 0, "restecg": "normal",
        "thalch": 160, "exang": 0, "oldpeak": 0.5, "slope": "flat",
        "ca": 0, "thal": "normal",
    })

    check("API: /advice returns 200", "POST", "/advice", {
        "disease": "heart", "risk_level": "Moderate",
        "data": {"chol": 250, "trestbps": 145, "oldpeak": 1.2},
    })


# ------------------- Runner -------------------

def main():
    print("=" * 60)
    print("Smart Healthcare System — Running All Tests")
    print("=" * 60)

    run_test("diabetes_low_risk", test_diabetes_low_risk)
    run_test("diabetes_high_risk", test_diabetes_high_risk)
    run_test("diabetes_variance", test_diabetes_different_inputs_give_different_outputs)
    run_test("diabetes_missing_field", test_diabetes_missing_field_raises)

    run_test("heart_low_risk", test_heart_low_risk)
    run_test("heart_high_risk", test_heart_high_risk)
    run_test("heart_variance", test_heart_different_inputs_give_different_outputs)
    run_test("heart_determinism", test_heart_same_input_is_deterministic)
    run_test("heart_partial_input", test_heart_missing_optional_fields_uses_defaults)

    if "--api" in sys.argv:
        print("\n--- Live API tests (requires uvicorn running on :8000) ---")
        run_test("api_endpoints", test_api_endpoints)
    else:
        print("\n(Skipping live API tests — run with --api to include them)")

    print("\n" + "=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"Results: {passed}/{total} passed")
    print("=" * 60)

    if passed != total:
        sys.exit(1)


if __name__ == "__main__":
    main()