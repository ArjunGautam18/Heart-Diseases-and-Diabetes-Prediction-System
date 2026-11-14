"""
Gemini-powered chatbot for free-text health questions,
grounded in the user's prediction context.
"""

import json
import os

try:
    from health_coach import generate_advice
except ImportError:
    from scripts.health_coach import generate_advice

try:
    import google.generativeai as genai
except ImportError:
    genai = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = genai.GenerativeModel("gemini-3.6-flash")
    return _model


def extract_report_fields(image_bytes: bytes, mime_type: str, disease: str = "heart") -> dict:
    """Return heart-form fields extracted from a medical report image."""
    if not GEMINI_API_KEY or genai is None:
        raise RuntimeError("Vision extraction requires GEMINI_API_KEY and the Gemini package.")
    if disease == "diabetes":
        prompt = (
            "Read this multi-column medical report carefully and return only valid JSON. "
            "Pair every value with its own label; never copy a value from a neighboring column. "
            "Use null when a field is not visibly present. Return exactly these keys: "
            "patientName, age, gender, hypertension, heart_disease, smoking_history, bmi, "
            "HbA1c_level, blood_glucose_level. Use gender Male/Female/Other, hypertension "
            "and heart_disease as 0 or 1, and smoking_history as never, former, current, "
            "not current, ever, or No Info. Do not infer missing values."
        )
    else:
        prompt = (
        "Read this multi-column medical report carefully and return only valid JSON. "
        "Pair every value with its own label; never copy a value from a neighboring column. "
        "Use null when a field is not visibly present. Use exactly these keys: "
        "patientName, age, gender, height, weight, bloodPressureSystolic, cholesterolTotal, "
        "fastingBloodSugar, bloodSugarAbove120, hypertension, diabetes, chestPain, "
        "familyHistory, smoking, alcoholConsumption, regularExercise, healthyDiet, highStress. "
        "gender must be Male or Female. Yes/No fields must be exactly Yes or No. "
        "chestPain must be None, Chest pain during activity, or Chest pain at rest. "
        "Do not infer missing values and do not add markdown or explanation."
        )
    response = _get_model().generate_content(
        [prompt, {"mime_type": mime_type, "data": image_bytes}],
        generation_config={"response_mime_type": "application/json"},
    )
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    values = json.loads(raw)
    if disease == "diabetes":
        allowed = {
            "patientName", "age", "gender", "hypertension", "heart_disease",
            "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level",
        }
        result = {key: values[key] for key in allowed if values.get(key) is not None}
        numeric_ranges = {
            "age": (1, 120), "bmi": (10, 80), "HbA1c_level": (2, 20),
            "blood_glucose_level": (20, 700),
        }
        for key, (minimum, maximum) in numeric_ranges.items():
            if key in result:
                try:
                    result[key] = float(result[key])
                    if not minimum <= result[key] <= maximum:
                        del result[key]
                except (TypeError, ValueError):
                    del result[key]
        for key in ["age", "hypertension", "heart_disease"]:
            if key in result:
                result[key] = int(float(result[key]))
        return result

    allowed = {
        "patientName", "age", "gender", "height", "weight", "bloodPressureSystolic",
        "cholesterolTotal", "fastingBloodSugar", "bloodSugarAbove120", "hypertension",
        "diabetes", "chestPain", "familyHistory", "smoking", "alcoholConsumption",
        "regularExercise", "healthyDiet", "highStress",
    }
    report = {key: values[key] for key in allowed if values.get(key) is not None}
    result = {}
    field_map = {
        "gender": "sex", "height": "heightCm", "weight": "weightKg",
        "bloodPressureSystolic": "trestbps", "cholesterolTotal": "chol",
        "bloodSugarAbove120": "fbs", "alcoholConsumption": "alcohol",
        "regularExercise": "exercise", "healthyDiet": "diet", "highStress": "stress",
        "chestPain": "cp", "familyHistory": "familyHistory",
    }
    for key, value in report.items():
        result[field_map.get(key, key)] = value
    if "fastingBloodSugar" in report and "fbs" not in result:
        result["fbs"] = 1 if float(report["fastingBloodSugar"]) > 120 else 0
    if result.get("cp") == "None":
        result["cp"] = "asymptomatic"
    elif result.get("cp") == "Chest pain at rest":
        result["cp"] = "atypical angina"
    elif result.get("cp") == "Chest pain during activity":
        result["cp"] = "typical angina"
    numeric_ranges = {
        "age": (1, 120), "heightCm": (50, 250), "weightKg": (2, 300),
        "bmi": (10, 80), "trestbps": (70, 250), "chol": (80, 600),
        "thalch": (40, 240), "oldpeak": (0, 10), "ca": (0, 4),
    }
    for key, (minimum, maximum) in numeric_ranges.items():
        if key in result:
            try:
                result[key] = float(result[key])
                if not minimum <= result[key] <= maximum:
                    del result[key]
            except (TypeError, ValueError):
                del result[key]
    for key in ["age", "heightCm", "weightKg", "trestbps", "chol", "thalch", "ca"]:
        if key in result and float(result[key]).is_integer():
            result[key] = int(result[key])
    if "fbs" in result:
        result["fbs"] = 1 if str(result["fbs"]).lower() in {"1", "yes", "true"} else 0
    if "exang" in result:
        result["exang"] = 1 if str(result["exang"]).lower() in {"1", "yes", "true"} else 0
    return result


def _offline_response(message: str, disease: str = "", risk_level: str = "", data: dict = None) -> str:
    question = message.lower()
    condition = disease.lower() if disease else "your result"
    level = risk_level.lower() if risk_level else "the reported"

    if any(word in question for word in ["urgent", "emergency", "danger", "symptom"]):
        return (
            "Seek urgent medical help for chest pain or pressure, severe shortness of breath, "
            "fainting, sudden weakness, confusion, or symptoms that are rapidly worsening. "
            "This application cannot diagnose emergencies."
        )
    if any(word in question for word in ["food", "diet", "eat", "snack"]):
        advice = generate_advice(disease, risk_level, data or {})
        diet = " ".join(advice["diet_recommendations"])
        return (
            f"For your {level} {condition} result: {diet} "
            f"{advice['disclaimer']}"
        )
    if any(word in question for word in ["exercise", "walk", "workout", "activity"]):
        advice = generate_advice(disease, risk_level, data or {})
        exercise = " ".join(advice["exercise_recommendations"])
        return (
            f"For your {level} {condition} result: {exercise} "
            f"{advice['disclaimer']}"
        )
    if any(word in question for word in ["risk", "result", "score", "mean"]):
        return (
            f"Your screening shows {level} risk for {condition}. This is an estimate based on "
            "the information entered and is not a diagnosis. Discuss concerning results with "
            "a qualified healthcare professional."
        )
    if "diabetes" in question or disease.lower() == "diabetes":
        return (
            "Helpful habits include balanced meals, regular activity, monitoring blood sugar "
            "when advised, taking prescribed medicines, and attending follow-up appointments."
        )
    if "heart" in question or disease.lower() == "heart":
        return (
            "Heart health is supported by controlling blood pressure and cholesterol, avoiding "
            "smoking, staying active, managing stress, and following medical advice."
        )
    return (
        "I can provide general information about your screening result, heart health, diabetes, "
        "food, exercise, and warning symptoms. Please ask a specific question."
    )


def get_chat_response(message: str, disease: str = "", risk_level: str = "", data: dict = None) -> str:
    if not GEMINI_API_KEY or genai is None:
        return _offline_response(message, disease, risk_level, data)

    data = data or {}

    context_lines = []
    if disease:
        context_lines.append(f"Prediction type: {disease}")
    if risk_level:
        context_lines.append(f"Risk level: {risk_level}")
    if data:
        details = ", ".join(f"{k}={v}" for k, v in data.items())
        context_lines.append(f"User's input values: {details}")

    context = "\n".join(context_lines) if context_lines else "No prediction context available."

    system_instruction = (
        "You are a friendly health assistant embedded in a heart disease and diabetes "
        "risk prediction app. Answer the user's question clearly and concisely, "
        "using the prediction context below if relevant. "
        "Always stay general and educational — never diagnose, never claim certainty, "
        "and remind the user to consult a healthcare professional for personal medical decisions "
        "when appropriate. Keep answers under 150 words unless the user asks for more detail.\n\n"
        f"Context:\n{context}"
    )

    try:
        model = _get_model()
        response = model.generate_content(
            [system_instruction, f"User question: {message}"]
        )
        return response.text.strip()
    except Exception:
        return _offline_response(message, disease, risk_level)