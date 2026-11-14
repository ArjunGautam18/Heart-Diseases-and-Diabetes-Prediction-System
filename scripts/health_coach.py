"""
Health Coach Module
Generates rule-based diet & exercise recommendations based on
prediction results and the user's actual input values.
"""


def get_diabetes_advice(risk_level: str, data: dict) -> dict:
    diet_tips = []
    exercise_tips = []

    bmi = data.get("bmi", 25)
    glucose = data.get("blood_glucose_level", 100)
    hba1c = data.get("HbA1c_level", 5.5)

    if risk_level == "High":
        diet_tips += [
            "Cut back on refined carbs and added sugar (white bread, soda, pastries).",
            "Favor high-fiber foods: leafy greens, legumes, whole grains.",
            "Space meals evenly through the day to avoid glucose spikes.",
        ]
        exercise_tips += [
            "Aim for at least 150 minutes of moderate activity per week (brisk walking, cycling).",
            "Add light resistance training 2x/week — muscle improves insulin sensitivity.",
        ]
    elif risk_level == "Moderate":
        diet_tips += [
            "Reduce sugary drinks and snacks; watch portion sizes at meals.",
            "Include more vegetables and lean protein in daily meals.",
        ]
        exercise_tips += [
            "30 minutes of walking most days can meaningfully lower risk.",
        ]
    else:
        diet_tips += [
            "Keep up a balanced diet with whole foods and limited processed sugar.",
        ]
        exercise_tips += [
            "Maintain regular activity — even 20-30 minutes a day helps sustain low risk.",
        ]

    if bmi >= 30:
        diet_tips.append("Your BMI suggests focusing on gradual, sustainable weight loss (0.5-1kg/week).")
    if glucose >= 140:
        diet_tips.append("Your glucose reading is elevated — consider discussing testing frequency with a doctor.")
    if hba1c >= 6.0:
        diet_tips.append("Your HbA1c is in a range worth monitoring closely with a healthcare provider.")

    return {"diet": diet_tips, "exercise": exercise_tips}


def get_heart_advice(risk_level: str, data: dict) -> dict:
    diet_tips = []
    exercise_tips = []

    chol = data.get("chol", 200)
    trestbps = data.get("trestbps", 120)
    oldpeak = data.get("oldpeak", 0)

    if risk_level == "High":
        diet_tips += [
            "Reduce saturated fat: limit red meat, fried food, and full-fat dairy.",
            "Increase omega-3 sources (fatty fish, walnuts, flaxseed) which support heart health.",
            "Cut sodium intake — avoid processed and packaged foods where possible.",
        ]
        exercise_tips += [
            "Consult a doctor before starting a new exercise program given elevated risk.",
            "Once cleared, start with low-intensity activity (short walks) and build gradually.",
        ]
    elif risk_level == "Moderate":
        diet_tips += [
            "Adopt a Mediterranean-style diet: vegetables, olive oil, fish, whole grains.",
            "Limit added salt and sugary beverages.",
        ]
        exercise_tips += [
            "150 minutes/week of moderate cardio (brisk walking, swimming) is a good target.",
        ]
    else:
        diet_tips += [
            "Maintain a heart-healthy diet rich in vegetables, fiber, and healthy fats.",
        ]
        exercise_tips += [
            "Keep up regular cardio activity to sustain your current low risk.",
        ]

    if chol >= 240:
        diet_tips.append("Your cholesterol is elevated — reducing saturated fat intake can help.")
    if trestbps >= 140:
        diet_tips.append("Your resting blood pressure is high — reducing sodium and stress may help.")
    if oldpeak >= 2:
        exercise_tips.append("Your ST depression reading suggests exercise intensity should be guided by a doctor.")

    return {"diet": diet_tips, "exercise": exercise_tips}


def generate_advice(disease: str, risk_level: str, data: dict) -> dict:
    """
    disease: "diabetes" or "heart"
    risk_level: "Low" | "Moderate" | "High"
    data: the original input dict sent to the prediction endpoint
    """
    if disease == "diabetes":
        advice = get_diabetes_advice(risk_level, data)
    elif disease == "heart":
        advice = get_heart_advice(risk_level, data)
    else:
        advice = {"diet": [], "exercise": []}

    disclaimer = (
        "This is general guidance, not medical advice. "
        "Please consult a healthcare professional for personalized recommendations."
    )

    return {
        "disease": disease,
        "risk_level": risk_level,
        "diet_recommendations": advice["diet"],
        "exercise_recommendations": advice["exercise"],
        "disclaimer": disclaimer,
    }