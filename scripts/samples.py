"""Sample payloads shared by the manual API test scripts."""

DIABETES_EXTREME = {
    "Pregnancies": 1,
    "Glucose": 500,
    "BloodPressure": 80,
    "SkinThickness": 20,
    "Insulin": 100,
    "BMI": 30,
    "DiabetesPedigreeFunction": 0.5,
    "Age": 60,
}

DIABETES_NORMAL = {
    "Pregnancies": 1,
    "Glucose": 110,
    "BloodPressure": 80,
    "SkinThickness": 20,
    "Insulin": 80,
    "BMI": 25,
    "DiabetesPedigreeFunction": 0.2,
    "Age": 35,
}

HEART_SAMPLE = {
    "age": 55, "sex": 1, "cp": 3, "trestbps": 140, "chol": 250, "fbs": 0,
    "restecg": 1, "thalach": 120, "exang": 0, "oldpeak": 1.2, "slope": 2,
    "ca": 0, "thal": 2,
}