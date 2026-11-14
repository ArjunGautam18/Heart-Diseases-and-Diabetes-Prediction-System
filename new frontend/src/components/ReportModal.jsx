import React from 'react';

export default function ReportModal({ record, onClose }) {
  if (!record) return null;

  const getBadgeClass = (level) => {
    if (level === 'High') return 'badge badge-high';
    if (level === 'Moderate') return 'badge badge-moderate';
    return 'badge badge-low';
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#1E293B' }}>
              Patient Diagnostic Screening Report
            </h2>
            <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>
              Record ID: {record.id} &bull; Generated: {record.date} at {record.time}
            </div>
          </div>
          <button className="btn btn-secondary btn-small" onClick={onClose}>
            &times; Close
          </button>
        </div>

        {/* Patient Demographics */}
        <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '10px', color: '#334155' }}>
            Patient Information
          </h3>
          <div className="grid-3" style={{ fontSize: '13px', rowGap: '8px' }}>
            <div><strong>Patient ID:</strong> {record.patientId}</div>
            <div><strong>Full Name:</strong> {record.name}</div>
            <div><strong>Age / Gender:</strong> {record.age} yrs / {record.gender}</div>
            <div><strong>Phone:</strong> {record.phone || 'None'}</div>
            <div><strong>Examiner:</strong> {record.examiner}</div>
            <div><strong>Smoking Status:</strong> {record.smoking}</div>
          </div>
        </div>

        {/* Vitals Recorded */}
        <div className="card" style={{ padding: '16px', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '10px', color: '#334155' }}>
            Physiological Measurements
          </h3>
          <div className="grid-3" style={{ fontSize: '13px' }}>
            <div><strong>Blood Pressure:</strong> {record.systolicBP}/{record.diastolicBP} mmHg</div>
            <div><strong>Body Mass Index:</strong> {record.bmi ? `${record.bmi} kg/m²` : 'N/A'}</div>
            <div><strong>Fasting Sugar:</strong> {record.fastingSugar ? `${record.fastingSugar} mg/dL` : 'Not recorded'}</div>
          </div>
        </div>

        {/* Risk Scores Grid */}
        <div className="grid-2" style={{ marginBottom: '16px' }}>
          {/* Heart Disease Summary */}
          <div className="risk-result-panel" style={{ marginTop: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>Heart Disease Risk</strong>
              <span className={getBadgeClass(record.heartRisk)}>
                {record.heartRisk} ({record.heartScore}%)
              </span>
            </div>
            <div style={{ marginTop: '10px', fontSize: '13px' }}>
              <span style={{ fontWeight: 500, color: '#475569' }}>Contributing Indicators:</span>
              <ul className="factor-list">
                {record.heartFactors && record.heartFactors.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Diabetes Summary */}
          <div className="risk-result-panel" style={{ marginTop: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>Type 2 Diabetes Risk</strong>
              <span className={getBadgeClass(record.diabetesRisk)}>
                {record.diabetesRisk} ({record.diabetesScore}%)
              </span>
            </div>
            <div style={{ marginTop: '10px', fontSize: '13px' }}>
              <span style={{ fontWeight: 500, color: '#475569' }}>Contributing Indicators:</span>
              <ul className="factor-list">
                {record.diabetesFactors && record.diabetesFactors.map((f, i) => (
                  <li key={i}>{f}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>

        {/* Clinical Notes & Recommendations */}
        <div style={{ backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '4px', padding: '14px', marginBottom: '20px' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#1E293B', marginBottom: '6px' }}>
            Urgency: <span style={{ color: record.urgency.includes('Immediate') ? '#DC2626' : '#2C6E6B' }}>{record.urgency}</span>
          </div>
          {record.notes && (
            <div style={{ fontSize: '13px', color: '#475569', marginTop: '6px' }}>
              <strong>Examiner Notes:</strong> {record.notes}
            </div>
          )}
          {record.recommendations && record.recommendations.length > 0 && (
            <div style={{ marginTop: '8px', fontSize: '13px', color: '#475569' }}>
              <strong>Recommended Clinical Pathways:</strong>
              <ul style={{ marginLeft: '20px', marginTop: '4px' }}>
                {record.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          <button className="btn btn-secondary btn-small" onClick={handlePrint}>
            {/* Print Report */}

          </button>
          <button className="btn btn-primary btn-small" onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
