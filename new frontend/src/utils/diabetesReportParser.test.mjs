import test from 'node:test';
import assert from 'node:assert/strict';
import { extractDiabetesFromText } from './diabetesReportParser.js';

test('extractDiabetesFromText reads values next to their labels even when all fields appear on one line', () => {
  const sample = 'Patient Name John Doe Age 33 Gender Female Hypertension No Heart Disease No Smoking History No Info BMI 25 HbA1c Level 5.5 Blood Glucose Level 120';
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

  assert.equal(result.nextData.age, 33);
  assert.equal(result.nextData.gender, 'Female');
  assert.equal(result.nextData.hypertension, 0);
  assert.equal(result.nextData.heart_disease, 0);
  assert.equal(result.nextData.smoking_history, 'No Info');
  assert.equal(result.nextData.bmi, 25);
  assert.equal(result.nextData.HbA1c_level, 5.5);
  assert.equal(result.nextData.blood_glucose_level, 120);
});

test('extractDiabetesFromText handles alternate clinical labels such as Sex, A1C, and tobacco wording', () => {
  const sample = 'PATIENT INFO\nSex: Female\nAge: 58\nHTN: No\nCardiac disease: No\nSmoking: Former smoker\nBMI 29.7\nA1C: 7.4\nRandom Blood Sugar: 198 mg/dl';
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

  assert.equal(result.nextData.age, 58);
  assert.equal(result.nextData.gender, 'Female');
  assert.equal(result.nextData.hypertension, 0);
  assert.equal(result.nextData.heart_disease, 0);
  assert.equal(result.nextData.smoking_history, 'former');
  assert.equal(result.nextData.bmi, 29.7);
  assert.equal(result.nextData.HbA1c_level, 7.4);
  assert.equal(result.nextData.blood_glucose_level, 198);
});
