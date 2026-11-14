import test from 'node:test';
import assert from 'node:assert/strict';
import { extractDiabetesFromText } from './diabetesReportParser.js';

test('extractDiabetesFromText handles the Meridian Family and Cardiac Clinic report format', () => {
  const sample = `Meridian Family & Cardiac Clinic
PATIENT NAME
Marcus Whitfield
AGE
58
GENDER
Male
PATIENT ID
PT-88312
VITALS & LABORATORY RESULTS
HEIGHT
178 cm
WEIGHT
94 kg
BMI
29.7 (overweight)
BLOOD PRESSURE
132/84 mmHg
FASTING BLOOD GLUCOSE
146 mg/dL
HBA1C
7.4%
RANDOM BLOOD GLUCOSE
198 mg/dL
SMOKING
No
HYPERTENSION
No
FAMILY HISTORY OF DIABETES
Yes
`;

  const result = extractDiabetesFromText(sample, {
    age: 0,
    gender: 'Female',
    hypertension: 0,
    heart_disease: 0,
    smoking_history: 'No Info',
    bmi: 0,
    HbA1c_level: 0,
    blood_glucose_level: 0,
  });

  assert.equal(result.patientName, 'Marcus Whitfield');
  assert.equal(result.nextData.age, 58);
  assert.equal(result.nextData.gender, 'Male');
  assert.equal(result.nextData.hypertension, 0);
  assert.equal(result.nextData.bmi, 29.7);
  assert.equal(result.nextData.HbA1c_level, 7.4);
  assert.equal(result.nextData.blood_glucose_level, 146);
  assert.equal(result.nextData.smoking_history, 'never');
});
