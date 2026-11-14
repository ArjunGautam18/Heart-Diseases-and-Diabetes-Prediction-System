import React, { useState } from 'react';
import { calculateRisk } from '../utils/screeningLogic';

export default function ScreeningForm({ user, onSaveRecord, onCancel }) {
  // Patient details state
  const [patientData, setPatientData] = useState({
    patientId: `PT-${Math.floor(100 + Math.random() * 900)}`,
    name: '',
    age: '45',
    gender: 'Male',
    phone: '',
  });

  // Clinical Vitals state
  const [vitals, setVitals] = useState({
    systolicBP: '120',
    diastolicBP: '80',
    fastingSugar: '',
    bmi: '24.5',
    heightCm: '170',
    weightKg: '70',
    smoking: 'never',
    familyHeartHistory: false,
    familyDiabetesHistory: false,
  });

  // Heart Symptoms state
  const [heartSymptoms, setHeartSymptoms] = useState({
    chestPain: false,
    shortnessOfBreath: false,
    radiatingPain: false,
    palpitations: false,
    swollenFeet: false,
    dizziness: false,
    fatigue: false,
  });

  // Diabetes Symptoms state
  const [diabetesSymptoms, setDiabetesSymptoms] = useState({
    excessiveThirst: false,
    frequentUrination: false,
    weightLoss: false,
    blurredVision: false,
    numbness: false,
    slowHealing: false,
    frequentHunger: false,
  });

  const [notes, setNotes] = useState('');
  const [result, setResult] = useState(null);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Auto-calculate BMI when height and weight are provided
  const handleHeightWeightChange = (height, weight) => {
    const hM = Number(height) / 100;
    const wKg = Number(weight);
    if (hM > 0 && wKg > 0) {
      const calculatedBmi = (wKg / (hM * hM)).toFixed(1);
      setVitals((prev) => ({
        ...prev,
        heightCm: height,
        weightKg: weight,
        bmi: calculatedBmi,
      }));
    } else {
      setVitals((prev) => ({ ...prev, heightCm: height, weightKg: weight }));
    }
  };

  const handleCalculate = (e) => {
    if (e) e.preventDefault();
    const computed = calculateRisk(patientData, vitals, heartSymptoms, diabetesSymptoms);
    setResult(computed);
    setSavedSuccess(false);
  };

  const handleSave = () => {
    if (!result) {
      handleCalculate();
    }
    const computed = result || calculateRisk(patientData, vitals, heartSymptoms, diabetesSymptoms);
    
    const now = new Date();
    const record = {
      id: `REC-${Date.now().toString().slice(-4)}`,
      date: now.toISOString().slice(0, 10),
      time: now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      patientId: patientData.patientId,
      name: patientData.name || 'Anonymous Patient',
      age: Number(patientData.age) || 0,
      gender: patientData.gender,
      phone: patientData.phone,
      systolicBP: Number(vitals.systolicBP) || 120,
      diastolicBP: Number(vitals.diastolicBP) || 80,
      fastingSugar: vitals.fastingSugar ? Number(vitals.fastingSugar) : null,
      bmi: Number(vitals.bmi) || 24,
      smoking: vitals.smoking,
      heartScore: computed.heartScore,
      heartRisk: computed.heartRisk,
      heartFactors: computed.heartFactors,
      diabetesScore: computed.diabetesScore,
      diabetesRisk: computed.diabetesRisk,
      diabetesFactors: computed.diabetesFactors,
      urgency: computed.urgency,
      recommendations: computed.recommendations,
      examiner: user?.email || 'singhabhishek0805@gmail.com',
      notes: notes,
    };

    onSaveRecord(record);
    setSavedSuccess(true);
  };

  const getBadgeClass = (level) => {
    if (level === 'High') return 'badge badge-high';
    if (level === 'Moderate') return 'badge badge-moderate';
    return 'badge badge-low';
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1E293B' }}>
            Patient Risk Screening Form
          </h2>
          <p style={{ fontSize: '13px', color: '#64748B' }}>
            Enter patients Health Information.
          </p>
        </div>
        <button className="btn btn-secondary btn-small" onClick={onCancel}>
          &larr; Back to Dashboard
        </button>
      </div>

      <form onSubmit={(e) => { e.preventDefault(); handleCalculate(); }}>
        {/* Section 1: Patient Information */}
        <div className="card">
          <h3 className="card-title">1. Patient Identification</h3>
          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="pat-id">Patient ID</label>
              <input
                id="pat-id"
                type="text"
                className="input-field"
                value={patientData.patientId}
                onChange={(e) => setPatientData({ ...patientData, patientId: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="pat-name">Patient Full Name</label>
              <input
                id="pat-name"
                type="text"
                className="input-field"
                placeholder="e.g. John Doe"
                value={patientData.name}
                onChange={(e) => setPatientData({ ...patientData, name: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="pat-age">Age (Years)</label>
              <input
                id="pat-age"
                type="number"
                min="1"
                max="120"
                className="input-field"
                value={patientData.age}
                onChange={(e) => setPatientData({ ...patientData, age: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="pat-gender">Gender</label>
              <select
                id="pat-gender"
                className="select-field"
                value={patientData.gender}
                onChange={(e) => setPatientData({ ...patientData, gender: e.target.value })}
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="pat-phone">Contact Number (Optional)</label>
              <input
                id="pat-phone"
                type="text"
                className="input-field"
                placeholder="e.g. 555-0199"
                value={patientData.phone}
                onChange={(e) => setPatientData({ ...patientData, phone: e.target.value })}
              />
            </div>
          </div>
        </div>

        {/* Section 2: Clinical Vitals & Measurements */}
        <div className="card">
          <h3 className="card-title">2. Physiological Vitals &amp; Baseline Metrics</h3>
          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="sys-bp">Systolic BP (mmHg)</label>
              <input
                id="sys-bp"
                type="number"
                className="input-field"
                placeholder="120"
                value={vitals.systolicBP}
                onChange={(e) => setVitals({ ...vitals, systolicBP: e.target.value })}
                required
              />
              <span className="input-help">Normal: &lt; 120 mmHg</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="dia-bp">Diastolic BP (mmHg)</label>
              <input
                id="dia-bp"
                type="number"
                className="input-field"
                placeholder="80"
                value={vitals.diastolicBP}
                onChange={(e) => setVitals({ ...vitals, diastolicBP: e.target.value })}
                required
              />
              <span className="input-help">Normal: &lt; 80 mmHg</span>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="fbs-input">Fasting Blood Sugar (mg/dL)</label>
              <input
                id="fbs-input"
                type="number"
                className="input-field"
                placeholder="Optional (e.g. 95)"
                value={vitals.fastingSugar}
                onChange={(e) => setVitals({ ...vitals, fastingSugar: e.target.value })}
              />
              <span className="input-help">Normal: 70 - 99 mg/dL</span>
            </div>
          </div>

          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="height-input">Height (cm)</label>
              <input
                id="height-input"
                type="number"
                className="input-field"
                value={vitals.heightCm}
                onChange={(e) => handleHeightWeightChange(e.target.value, vitals.weightKg)}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="weight-input">Weight (kg)</label>
              <input
                id="weight-input"
                type="number"
                className="input-field"
                value={vitals.weightKg}
                onChange={(e) => handleHeightWeightChange(vitals.heightCm, e.target.value)}
              />
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="bmi-input">Calculated BMI</label>
              <input
                id="bmi-input"
                type="number"
                step="0.1"
                className="input-field"
                value={vitals.bmi}
                onChange={(e) => setVitals({ ...vitals, bmi: e.target.value })}
              />
              <span className="input-help">Normal: 18.5 - 24.9</span>
            </div>
          </div>

          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="smoking-select">Smoking History</label>
              <select
                id="smoking-select"
                className="select-field"
                value={vitals.smoking}
                onChange={(e) => setVitals({ ...vitals, smoking: e.target.value })}
              >
                <option value="never">Non-smoker</option>
                <option value="former">Former smoker</option>
                <option value="current">Current smoker</option>
              </select>
            </div>
            <div className="form-group" style={{ paddingTop: '24px' }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={vitals.familyHeartHistory}
                  onChange={(e) => setVitals({ ...vitals, familyHeartHistory: e.target.checked })}
                />
                <span>Family History of Heart Disease</span>
              </label>
            </div>
            <div className="form-group" style={{ paddingTop: '24px' }}>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={vitals.familyDiabetesHistory}
                  onChange={(e) => setVitals({ ...vitals, familyDiabetesHistory: e.target.checked })}
                />
                <span>Family History of Diabetes</span>
              </label>
            </div>
          </div>
        </div>

        {/* Section 3: Symptom Checklists (2 Columns) */}
        <div className="grid-2">
          {/* Heart Symptoms Column */}
          <div className="card">
            <h3 className="card-title">3. Cardiovascular/Heart disease Symptoms</h3>
            <p className="card-subtitle">Check all symptoms experienced in the past 30 days:</p>

            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.chestPain}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, chestPain: e.target.checked })}
                />
                <div>
                  <strong>Chest Pain / Pressure</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Tightness or squeezing discomfort in chest</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.shortnessOfBreath}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, shortnessOfBreath: e.target.checked })}
                />
                <div>
                  <strong>Shortness of Breath (Dyspnea)</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Breathlessness upon mild exertion or when lying down</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.radiatingPain}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, radiatingPain: e.target.checked })}
                />
                <div>
                  <strong>Radiating Pain</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Discomfort spreading to left arm, neck, shoulder, or jaw</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.palpitations}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, palpitations: e.target.checked })}
                />
                <div>
                  <strong>Heart Palpitations</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Sensation of fluttering, racing, or skipped beats</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.swollenFeet}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, swollenFeet: e.target.checked })}
                />
                <div>
                  <strong>Peripheral Swelling (Edema)</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Fluid retention in feet, ankles, or lower legs</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.dizziness}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, dizziness: e.target.checked })}
                />
                <div>
                  <strong>Dizziness or Lightheadedness</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Unsteady episodes or feeling faint</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={heartSymptoms.fatigue}
                  onChange={(e) => setHeartSymptoms({ ...heartSymptoms, fatigue: e.target.checked })}
                />
                <div>
                  <strong>Unexplained Severe Fatigue</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Persistent exhaustion without clear physical cause</div>
                </div>
              </label>
            </div>
          </div>

          {/* Diabetes Symptoms Column */}
          <div className="card">
            <h3 className="card-title">4. Diabetes Symptoms</h3>
            <p className="card-subtitle">Check all symptoms experienced regularly:</p>

            <div className="checkbox-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.excessiveThirst}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, excessiveThirst: e.target.checked })}
                />
                <div>
                  <strong>Excessive Thirst (Polydipsia)</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Constant dry mouth, unquenched even with high water intake</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.frequentUrination}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, frequentUrination: e.target.checked })}
                />
                <div>
                  <strong>Frequent Urination (Polyuria)</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Urination needing repeated night awakenings</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.weightLoss}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, weightLoss: e.target.checked })}
                />
                <div>
                  <strong>Unexplained Weight Loss</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Dropping weight without changes in diet or workout</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.blurredVision}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, blurredVision: e.target.checked })}
                />
                <div>
                  <strong>Blurred Vision</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Difficulty focusing or transient cloudy eyesight</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.numbness}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, numbness: e.target.checked })}
                />
                <div>
                  <strong>Tingling or Numbness in Extremities</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Pins-and-needles sensation in fingers or toes</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.slowHealing}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, slowHealing: e.target.checked })}
                />
                <div>
                  <strong>Slow-Healing Cuts &amp; Sores</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Minor skin injuries taking unusually long to heal</div>
                </div>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={diabetesSymptoms.frequentHunger}
                  onChange={(e) => setDiabetesSymptoms({ ...diabetesSymptoms, frequentHunger: e.target.checked })}
                />
                <div>
                  <strong>Increased Hunger (Polyphagia)</strong>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>Constant hunger shortly after eating</div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Section 4: Clinical Notes & Action */}
        <div className="card">
          <h3 className="card-title">5. Examiner Notes (Optional)</h3>
          <div className="form-group">
            <textarea
              className="textarea-field"
              rows={2}
              placeholder="Clinical observation, patient comments, or follow-up directives..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              id="calculate-risk-btn"
              type="submit"
              className="btn btn-primary"
            >
              Calculate Risk Assessment
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => {
                setHeartSymptoms({
                  chestPain: false,
                  shortnessOfBreath: false,
                  radiatingPain: false,
                  palpitations: false,
                  swollenFeet: false,
                  dizziness: false,
                  fatigue: false,
                });
                setDiabetesSymptoms({
                  excessiveThirst: false,
                  frequentUrination: false,
                  weightLoss: false,
                  blurredVision: false,
                  numbness: false,
                  slowHealing: false,
                  frequentHunger: false,
                });
                setResult(null);
                setSavedSuccess(false);
              }}
            >
              Clear Checklists
            </button>
          </div>
        </div>
      </form>

      {/* Computed Risk Result Display */}
      {result && (
        <div className="card" style={{ border: '1px solid #94A3B8' }}>
          <h3 className="card-title" style={{ color: '#0F172A' }}>
            Screening Assessment Results
          </h3>

          <div className="grid-2" style={{ marginBottom: '20px' }}>
            {/* Heart Result */}
            <div className="risk-result-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: '15px' }}>Heart Disease Risk</span>
                <span className={getBadgeClass(result.heartRisk)}>
                  {result.heartRisk} ({result.heartScore}%)
                </span>
              </div>
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: 500, color: '#334155' }}>
                  Contributing Factors:
                </div>
                <ul className="factor-list">
                  {result.heartFactors.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Diabetes Result */}
            <div className="risk-result-panel">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: '15px' }}>Type 2 Diabetes Risk</span>
                <span className={getBadgeClass(result.diabetesRisk)}>
                  {result.diabetesRisk} ({result.diabetesScore}%)
                </span>
              </div>
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontSize: '13px', fontWeight: 500, color: '#334155' }}>
                  Contributing Factors:
                </div>
                <ul className="factor-list">
                  {result.diabetesFactors.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div style={{ padding: '12px 16px', backgroundColor: '#F1F5F9', borderRadius: '4px', marginBottom: '20px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#1E293B' }}>
              Clinical Urgency: <span style={{ color: result.urgency.includes('Immediate') ? '#DC2626' : '#2C6E6B' }}>{result.urgency}</span>
            </div>
            <div style={{ marginTop: '6px', fontSize: '13px', color: '#475569' }}>
              <strong>Recommended Actions:</strong>
              <ul style={{ marginLeft: '20px', marginTop: '4px' }}>
                {result.recommendations.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button
              id="save-record-btn"
              type="button"
              className="btn btn-primary"
              onClick={handleSave}
            >
              {savedSuccess ? 'Saved to Patient Log!' : 'Save Record to Patient History'}
            </button>
            {savedSuccess && (
              <span style={{ fontSize: '13px', color: '#059669', fontWeight: 500 }}>
                Record successfully added to history table.
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
