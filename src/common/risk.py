"""Risk level bucketing shared by the API and the health engine."""

MODERATE_RISK_THRESHOLD = 0.35
HIGH_RISK_THRESHOLD = 0.65

RISK_COLORS = {"Low": "green", "Moderate": "amber", "High": "red"}


def risk_level(prob: float) -> str:
    if prob >= HIGH_RISK_THRESHOLD:
        return "High"
    if prob >= MODERATE_RISK_THRESHOLD:
        return "Moderate"
    return "Low"


def risk_color(level: str) -> str:
    return RISK_COLORS[level]


def prediction_summary(prob: float, threshold: float = 0.5) -> dict:
    """Probability (as a percentage), binary prediction and risk level."""
    return {
        "prediction": int(prob >= threshold),
        "probability": round(prob * 100, 1),
        "risk_level": risk_level(prob),
    }
