"""
Health Score, Risk Assessment, and Personalized Recommendation Engine
Takes ML model probability outputs and produces structured health insights.

Used by app.py — not run directly.
"""
from src.common.risk import risk_color, risk_level


# ── HEALTH SCORE ─────────────────────────────────────────────────────────────
def compute_health_score(heart_prob: float, diabetes_prob: float,
                          age: int = None, bmi: float = None,
                          glucose: float = None, bp: float = None) -> dict:
    """
    Produces a 0-100 health score from model probabilities + optional vitals.
    Lower disease probability = higher health score.
    """
    # Core score from model predictions (80% weight)
    heart_component   = (1 - heart_prob)   * 40   # 40% weight
    diabetes_component = (1 - diabetes_prob) * 40  # 40% weight

    # Vitals component (20% weight) — graceful if not provided
    vitals_component = 20  # start at full vitals score, deduct for risk factors
    if bmi is not None:
        if bmi < 18.5 or bmi >= 35:
            vitals_component -= 8
        elif bmi >= 30:
            vitals_component -= 4
    if glucose is not None:
        if glucose >= 140:
            vitals_component -= 6
        elif glucose >= 100:
            vitals_component -= 2
    if bp is not None:
        if bp >= 140:
            vitals_component -= 4
        elif bp >= 120:
            vitals_component -= 1
    vitals_component = max(0, vitals_component)

    total = round(heart_component + diabetes_component + vitals_component)
    total = max(0, min(100, total))

    # Status label
    if total >= 80:
        status = "Excellent"
        color  = "green"
    elif total >= 65:
        status = "Good"
        color  = "teal"
    elif total >= 50:
        status = "Fair"
        color  = "amber"
    else:
        status = "Poor"
        color  = "red"

    return {
        "score": total,
        "status": status,
        "color": color,
        "breakdown": {
            "heart_contribution":    round(heart_component, 1),
            "diabetes_contribution": round(diabetes_component, 1),
            "vitals_contribution":   round(vitals_component, 1)
        }
    }


# ── RISK ASSESSMENT ───────────────────────────────────────────────────────────
def compute_risk(heart_prob: float, diabetes_prob: float,
                 age: int = None, bmi: float = None) -> dict:
    """
    Produces per-disease and combined risk levels with a factor breakdown.
    """
    # Combined risk: weighted average probability
    combined_prob = (heart_prob * 0.5) + (diabetes_prob * 0.5)
    if age and age >= 60:
        combined_prob = min(1.0, combined_prob + 0.05)
    if bmi and bmi >= 30:
        combined_prob = min(1.0, combined_prob + 0.05)

    combined_level = risk_level(combined_prob)

    # Factor breakdown — percentage contribution of each factor to overall risk
    factors = {
        "Heart Disease Risk": round(heart_prob * 100, 1),
        "Diabetes Risk":      round(diabetes_prob * 100, 1),
        "Age Factor":         round(min(100, max(0, ((age or 35) - 20) / 60 * 100)), 1),
        "BMI Factor":         round(min(100, max(0, ((bmi or 25) - 18) / 22 * 100)), 1) if bmi else 0
    }

    # Care urgency
    if combined_level == "High":
        urgency = "Seek medical attention soon"
    elif combined_level == "Moderate":
        urgency = "Schedule a health checkup within 1-2 months"
    else:
        urgency = "Maintain current healthy habits"

    return {
        "heart": {
            "probability": round(heart_prob * 100, 1),
            "level": risk_level(heart_prob),
            "color": risk_color(risk_level(heart_prob))
        },
        "diabetes": {
            "probability": round(diabetes_prob * 100, 1),
            "level": risk_level(diabetes_prob),
            "color": risk_color(risk_level(diabetes_prob))
        },
        "combined": {
            "level": combined_level,
            "color": risk_color(combined_level),
            "probability": round(combined_prob * 100, 1)
        },
        "factors": factors,
        "care_urgency": urgency
    }


# ── PERSONALIZED RECOMMENDATIONS ─────────────────────────────────────────────
def generate_recommendations(heart_prob: float, diabetes_prob: float,
                               age: int = None, bmi: float = None,
                               glucose: float = None) -> list:
    """
    Returns a list of condition-specific, prioritized health recommendations.
    Each item has: icon, text, priority, category.
    """
    recs = []

    # ── Heart-specific recommendations ──
    if heart_prob >= 0.65:
        recs.append({
            "icon": "🫀",
            "text": "High heart disease risk detected. Schedule a cardiology consultation and ECG within the next 2 weeks.",
            "priority": "High",
            "category": "heart"
        })
        recs.append({
            "icon": "🧂",
            "text": "Reduce sodium intake to under 1,500mg/day to lower blood pressure and reduce cardiac strain.",
            "priority": "High",
            "category": "heart"
        })
    elif heart_prob >= 0.35:
        recs.append({
            "icon": "🫀",
            "text": "Moderate heart disease risk. Discuss cholesterol levels and blood pressure management with your doctor.",
            "priority": "Medium",
            "category": "heart"
        })

    # ── Diabetes-specific recommendations ──
    if diabetes_prob >= 0.65:
        recs.append({
            "icon": "🩸",
            "text": "High diabetes risk detected. Get an HbA1c blood test immediately and consult an endocrinologist.",
            "priority": "High",
            "category": "diabetes"
        })
        recs.append({
            "icon": "🥗",
            "text": "Cut refined carbohydrates and sugary drinks. Switch to whole grains, legumes, and low-glycemic foods.",
            "priority": "High",
            "category": "diabetes"
        })
    elif diabetes_prob >= 0.35:
        recs.append({
            "icon": "🩸",
            "text": "Moderate diabetes risk. Monitor fasting blood glucose monthly and reduce simple sugar intake.",
            "priority": "Medium",
            "category": "diabetes"
        })

    # ── BMI-specific ──
    if bmi and bmi >= 30:
        recs.append({
            "icon": "⚖️",
            "text": f"BMI of {bmi:.1f} is in the obese range. A 5-10% weight reduction significantly lowers both heart and diabetes risk.",
            "priority": "High",
            "category": "weight"
        })
    elif bmi and bmi >= 25:
        recs.append({
            "icon": "⚖️",
            "text": f"BMI of {bmi:.1f} is slightly elevated. Aim for a gradual 0.5–1 kg/week loss through diet and exercise.",
            "priority": "Medium",
            "category": "weight"
        })

    # ── Glucose-specific ──
    if glucose and glucose >= 126:
        recs.append({
            "icon": "🔬",
            "text": f"Fasting glucose of {glucose:.0f} mg/dL is in the diabetic range. Immediate medical evaluation required.",
            "priority": "High",
            "category": "glucose"
        })
    elif glucose and glucose >= 100:
        recs.append({
            "icon": "🔬",
            "text": f"Fasting glucose of {glucose:.0f} mg/dL suggests pre-diabetes. Reduce sugar intake and increase physical activity.",
            "priority": "Medium",
            "category": "glucose"
        })

    # ── Age-specific ──
    if age and age >= 60:
        recs.append({
            "icon": "📅",
            "text": "Annual cardiovascular screening and HbA1c tests are recommended for your age group.",
            "priority": "Medium",
            "category": "screening"
        })

    # ── Universal lifestyle recommendations ──
    both_high = heart_prob >= 0.35 and diabetes_prob >= 0.35
    recs.append({
        "icon": "🏃",
        "text": "Aim for 150 minutes of moderate aerobic activity per week (e.g. brisk walking, cycling, swimming).",
        "priority": "High" if both_high else "Medium",
        "category": "exercise"
    })
    recs.append({
        "icon": "💧",
        "text": "Stay well hydrated — drink 8-10 glasses of water daily. Avoid sugary drinks and excessive caffeine.",
        "priority": "Low",
        "category": "lifestyle"
    })
    recs.append({
        "icon": "😴",
        "text": "Prioritize 7-9 hours of quality sleep per night. Poor sleep raises cortisol and worsens insulin resistance.",
        "priority": "Medium",
        "category": "lifestyle"
    })

    if len(recs) < 3:
        recs.append({
            "icon": "✅",
            "text": "Your risk levels are currently low. Maintain a balanced diet, regular exercise, and annual health checkups.",
            "priority": "Low",
            "category": "general"
        })

    # Sort: High first, then Medium, then Low
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    recs.sort(key=lambda x: priority_order[x["priority"]])

    return recs[:6]  # cap at 6 recommendations for clean UI


# ── COMBINED RUNNER ───────────────────────────────────────────────────────────
def full_health_analysis(heart_prob: float, diabetes_prob: float,
                          age: int = None, bmi: float = None,
                          glucose: float = None, bp: float = None) -> dict:
    """
    Single call that returns health score + risk assessment + recommendations.
    This is what app.py calls and returns as one JSON response.
    """
    return {
        "health_score":     compute_health_score(heart_prob, diabetes_prob, age, bmi, glucose, bp),
        "risk_assessment":  compute_risk(heart_prob, diabetes_prob, age, bmi),
        "recommendations":  generate_recommendations(heart_prob, diabetes_prob, age, bmi, glucose)
    }