// Simple Rule-Based Risk Screening Engine for Heart Disease and Diabetes
// Written in clean JavaScript for easy viva explanation

export function calculateRisk(patientData, vitals, heartSymptoms, diabetesSymptoms) {
  // 1. Calculate Heart Disease Risk (0 - 100)
  let heartScore = 0;
  let heartFactors = [];

  // Heart Symptoms
  if (heartSymptoms.chestPain) {
    heartScore += 25;
    heartFactors.push('Chest pain or tightness');
  }
  if (heartSymptoms.shortnessOfBreath) {
    heartScore += 15;
    heartFactors.push('Shortness of breath on exertion');
  }
  if (heartSymptoms.radiatingPain) {
    heartScore += 20;
    heartFactors.push('Pain radiating to arm or jaw');
  }
  if (heartSymptoms.palpitations) {
    heartScore += 10;
    heartFactors.push('Rapid or irregular heartbeats');
  }
  if (heartSymptoms.swollenFeet) {
    heartScore += 12;
    heartFactors.push('Swelling in feet or ankles (edema)');
  }
  if (heartSymptoms.dizziness) {
    heartScore += 8;
    heartFactors.push('Dizziness or lightheadedness');
  }
  if (heartSymptoms.fatigue) {
    heartScore += 5;
    heartFactors.push('Unusual fatigue');
  }

  // Heart Vitals & Medical History
  const sysBP = Number(vitals.systolicBP) || 120;
  const diaBP = Number(vitals.diastolicBP) || 80;
  const age = Number(patientData.age) || 30;
  const bmi = Number(vitals.bmi) || 24;

  if (sysBP >= 140 || diaBP >= 90) {
    heartScore += 15;
    heartFactors.push(`High blood pressure (${sysBP}/${diaBP} mmHg)`);
  } else if (sysBP >= 130 || diaBP >= 80) {
    heartScore += 8;
    heartFactors.push(`Pre-hypertension (${sysBP}/${diaBP} mmHg)`);
  }

  if (vitals.smoking === 'current') {
    heartScore += 15;
    heartFactors.push('Active smoker');
  } else if (vitals.smoking === 'former') {
    heartScore += 5;
    heartFactors.push('Former smoker');
  }

  if (vitals.familyHeartHistory) {
    heartScore += 12;
    heartFactors.push('Family history of heart disease');
  }

  if (age >= 55) {
    heartScore += 12;
    heartFactors.push(`Age factor (${age} years)`);
  } else if (age >= 45) {
    heartScore += 8;
  }

  if (bmi >= 30) {
    heartScore += 10;
    heartFactors.push(`High BMI (${bmi})`);
  }

  // 2. Calculate Type 2 Diabetes Risk (0 - 100)
  let diabetesScore = 0;
  let diabetesFactors = [];

  // Diabetes Symptoms
  if (diabetesSymptoms.excessiveThirst) {
    diabetesScore += 20;
    diabetesFactors.push('Excessive thirst (polydipsia)');
  }
  if (diabetesSymptoms.frequentUrination) {
    diabetesScore += 20;
    diabetesFactors.push('Frequent urination (polyuria)');
  }
  if (diabetesSymptoms.weightLoss) {
    diabetesScore += 15;
    diabetesFactors.push('Unexplained weight loss');
  }
  if (diabetesSymptoms.blurredVision) {
    diabetesScore += 12;
    diabetesFactors.push('Blurred vision');
  }
  if (diabetesSymptoms.numbness) {
    diabetesScore += 14;
    diabetesFactors.push('Numbness / tingling in hands or feet');
  }
  if (diabetesSymptoms.slowHealing) {
    diabetesScore += 12;
    diabetesFactors.push('Slow-healing wounds or sores');
  }
  if (diabetesSymptoms.frequentHunger) {
    diabetesScore += 8;
    diabetesFactors.push('Frequent hunger');
  }

  // Diabetes Vitals & Medical History
  const fbs = Number(vitals.fastingSugar) || 0;
  if (fbs >= 126) {
    diabetesScore += 30;
    diabetesFactors.push(`High fasting glucose (${fbs} mg/dL)`);
  } else if (fbs >= 100) {
    diabetesScore += 15;
    diabetesFactors.push(`Pre-diabetic fasting glucose (${fbs} mg/dL)`);
  }

  if (bmi >= 30) {
    diabetesScore += 15;
    diabetesFactors.push(`Obesity (BMI ${bmi})`);
  } else if (bmi >= 25) {
    diabetesScore += 8;
    diabetesFactors.push(`Overweight (BMI ${bmi})`);
  }

  if (vitals.familyDiabetesHistory) {
    diabetesScore += 15;
    diabetesFactors.push('Family history of diabetes');
  }

  if (age >= 45) {
    diabetesScore += 10;
    diabetesFactors.push(`Age over 45 (${age} years)`);
  }

  // Normalize scores to max 100
  const finalHeartScore = Math.min(100, heartScore);
  const finalDiabetesScore = Math.min(100, diabetesScore);

  // Categorize Risk Level
  const getRiskLevel = (score) => {
    if (score >= 50) return 'High';
    if (score >= 25) return 'Moderate';
    return 'Low';
  };

  const heartRisk = getRiskLevel(finalHeartScore);
  const diabetesRisk = getRiskLevel(finalDiabetesScore);

  // Overall Urgency determination
  let urgency = 'Routine Checkup';
  if (heartRisk === 'High' || diabetesRisk === 'High') {
    urgency = heartSymptoms.chestPain ? 'Immediate Medical Attention' : 'Clinical Follow-up Recommended';
  } else if (heartRisk === 'Moderate' || diabetesRisk === 'Moderate') {
    urgency = 'Doctor Consultation Advised';
  }

  // Clinical Summary Recommendations
  const recommendations = [];
  if (heartRisk === 'High') {
    recommendations.push('Schedule an ECG and lipid profile test promptly.');
  } else if (heartRisk === 'Moderate') {
    recommendations.push('Monitor blood pressure weekly and reduce dietary sodium.');
  }

  if (diabetesRisk === 'High') {
    recommendations.push('Perform an HbA1c blood test and fasting blood sugar profile.');
  } else if (diabetesRisk === 'Moderate') {
    recommendations.push('Adopt a low-glycemic diet and increase daily physical activity.');
  }

  if (heartRisk === 'Low' && diabetesRisk === 'Low') {
    recommendations.push('Maintain a healthy lifestyle and continue annual preventive checkups.');
  }

  return {
    heartScore: finalHeartScore,
    heartRisk,
    heartFactors: heartFactors.length > 0 ? heartFactors : ['No critical heart symptoms identified'],
    diabetesScore: finalDiabetesScore,
    diabetesRisk,
    diabetesFactors: diabetesFactors.length > 0 ? diabetesFactors : ['No major diabetic symptoms reported'],
    urgency,
    recommendations,
  };
}
