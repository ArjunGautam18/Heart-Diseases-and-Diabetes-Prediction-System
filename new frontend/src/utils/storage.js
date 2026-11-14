// Storage utility for patient logs and user session management
// Uses browser localStorage for simplicity

const STORAGE_KEY = 'heartcare_patient_logs';
const SESSION_KEY = 'heartcare_user_session';

// Initial sample patient logs for demonstration
export const INITIAL_RECORDS = [
  {
    id: 'REC-101',
    date: '2026-08-14',
    time: '09:30 AM',
    patientId: 'PT-401',
    name: 'Robert Chen',
    age: 58,
    gender: 'Male',
    phone: '555-0192',
    systolicBP: 146,
    diastolicBP: 92,
    fastingSugar: 135,
    bmi: 29.1,
    smoking: 'former',
    heartScore: 75,
    heartRisk: 'High',
    heartFactors: ['Chest pain or tightness', 'High blood pressure (146/92 mmHg)', 'Former smoker', 'Age factor (58 years)'],
    diabetesScore: 68,
    diabetesRisk: 'High',
    diabetesFactors: ['Excessive thirst (polydipsia)', 'Frequent urination (polyuria)', 'High fasting glucose (135 mg/dL)'],
    urgency: 'Immediate Medical Attention',
    examiner: 'singhabhishek0805@gmail.com',
    notes: 'Patient noted chest tightness during morning walks. Advised ECG and blood tests.',
  },
  {
    id: 'REC-102',
    date: '2026-08-12',
    time: '02:15 PM',
    patientId: 'PT-402',
    name: 'Eleanor Vance',
    age: 46,
    gender: 'Female',
    phone: '555-0144',
    systolicBP: 122,
    diastolicBP: 78,
    fastingSugar: 110,
    bmi: 26.3,
    smoking: 'never',
    heartScore: 18,
    heartRisk: 'Low',
    heartFactors: ['No critical heart symptoms identified'],
    diabetesScore: 48,
    diabetesRisk: 'Moderate',
    diabetesFactors: ['Excessive thirst (polydipsia)', 'Pre-diabetic fasting glucose (110 mg/dL)', 'Family history of diabetes'],
    urgency: 'Doctor Consultation Advised',
    examiner: 'singhabhishek0805@gmail.com',
    notes: 'Follow-up for pre-diabetes lifestyle management.',
  },
  {
    id: 'REC-103',
    date: '2026-08-10',
    time: '11:00 AM',
    patientId: 'PT-403',
    name: 'Marcus Sterling',
    age: 31,
    gender: 'Male',
    phone: '555-0188',
    systolicBP: 118,
    diastolicBP: 76,
    fastingSugar: 88,
    bmi: 22.5,
    smoking: 'never',
    heartScore: 5,
    heartRisk: 'Low',
    heartFactors: ['No critical heart symptoms identified'],
    diabetesScore: 8,
    diabetesRisk: 'Low',
    diabetesFactors: ['No major diabetic symptoms reported'],
    urgency: 'Routine Checkup',
    examiner: 'singhabhishek0805@gmail.com',
    notes: 'Routine health screening. Vitals normal.',
  },
];

export function getRecords() {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    if (!data) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_RECORDS));
      return INITIAL_RECORDS;
    }
    return JSON.parse(data);
  } catch (e) {
    console.error('Error reading records', e);
    return INITIAL_RECORDS;
  }
}

export function saveRecord(newRecord) {
  const current = getRecords();
  const updated = [newRecord, ...current];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export function deleteRecord(recordId) {
  const current = getRecords();
  const updated = current.filter((r) => r.id !== recordId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  return updated;
}

export function resetRecords() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_RECORDS));
  return INITIAL_RECORDS;
}

export function getSession() {
  try {
    const data = localStorage.getItem(SESSION_KEY);
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

export function setSession(user) {
  if (!user) {
    localStorage.removeItem(SESSION_KEY);
  } else {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
  }
}

export function exportToCSV(records) {
  const headers = [
    'Record ID',
    'Date',
    'Time',
    'Patient ID',
    'Name',
    'Age',
    'Gender',
    'Systolic BP',
    'Diastolic BP',
    'Fasting Sugar',
    'BMI',
    'Heart Score (%)',
    'Heart Risk Level',
    'Diabetes Score (%)',
    'Diabetes Risk Level',
    'Urgency',
    'Examiner Notes',
  ];

  const rows = records.map((r) => [
    `"${r.id}"`,
    `"${r.date}"`,
    `"${r.time}"`,
    `"${r.patientId}"`,
    `"${r.name}"`,
    r.age,
    `"${r.gender}"`,
    r.systolicBP,
    r.diastolicBP,
    r.fastingSugar || 'N/A',
    r.bmi || 'N/A',
    r.heartScore,
    `"${r.heartRisk}"`,
    r.diabetesScore,
    `"${r.diabetesRisk}"`,
    `"${r.urgency}"`,
    `"${(r.notes || '').replace(/"/g, '""')}"`,
  ]);

  const csv = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `HeartCare_Patient_Records_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}
