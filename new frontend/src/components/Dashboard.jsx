import React from 'react';

export default function Dashboard({ records, onNavigate, onViewRecord }) {
  const total = records.length;
  const highRisk = records.filter(
    (r) => r.heartRisk === 'High' || r.diabetesRisk === 'High'
  ).length;
  const moderateRisk = records.filter(
    (r) =>
      (r.heartRisk === 'Moderate' || r.diabetesRisk === 'Moderate') &&
      r.heartRisk !== 'High' &&
      r.diabetesRisk !== 'High'
  ).length;
  const lowRisk = records.filter(
    (r) => r.heartRisk === 'Low' && r.diabetesRisk === 'Low'
  ).length;

  const recentRecords = records.slice(0, 5);

  const getBadgeClass = (level) => {
    if (level === 'High') return 'badge badge-high';
    if (level === 'Moderate') return 'badge badge-moderate';
    return 'badge badge-low';
  };

  return (
    <div>
      {/* 1. Quick Stats Grid */}
      <div className="grid-4" style={{ marginBottom: '24px' }}>
        <div className="stat-box">
          <div className="stat-label">Total Screenings</div>
          <div className="stat-value">{total}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">High Risk Cases</div>
          <div className="stat-value" style={{ color: '#DC2626' }}>{highRisk}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Moderate Risk</div>
          <div className="stat-value" style={{ color: '#D97706' }}>{moderateRisk}</div>
        </div>
        <div className="stat-box">
          <div className="stat-label">Low Risk / Normal</div>
          <div className="stat-value" style={{ color: '#059669' }}>{lowRisk}</div>
        </div>
      </div>

      {/* 2. Main Dashboard Panel */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 className="card-title" style={{ marginBottom: '4px', border: 'none' }}>
              Recent Patient Screenings
            </h2>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Latest logged risk evaluations and clinical statuses
            </p>
          </div>
          <button
            id="start-screening-btn"
            className="btn btn-primary"
            onClick={() => onNavigate('form')}
          >
            + New Risk screening
          </button>
        </div>

        {recentRecords.length === 0 ? (
          <p style={{ color: '#64748B', padding: '20px 0' }}>
            No patient records logged yet. Click "New patient " to evaluate a patient.
          </p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Patient ID</th>
                  <th>Name</th>
                  <th>Age / Sex</th>
                  <th>Blood Pressure</th>
                  <th>Heart Risk</th>
                  <th>Diabetes Risk</th>
                  <th>Urgency</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentRecords.map((rec) => (
                  <tr key={rec.id}>
                    <td>{rec.date}</td>
                    <td style={{ fontWeight: 500 }}>{rec.patientId}</td>
                    <td>{rec.name}</td>
                    <td>{rec.age} y / {rec.gender}</td>
                    <td>{rec.systolicBP}/{rec.diastolicBP} mmHg</td>
                    <td>
                      <span className={getBadgeClass(rec.heartRisk)}>
                        {rec.heartRisk} ({rec.heartScore}%)
                      </span>
                    </td>
                    <td>
                      <span className={getBadgeClass(rec.diabetesRisk)}>
                        {rec.diabetesRisk} ({rec.diabetesScore}%)
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '12px', color: rec.urgency.includes('Immediate') ? '#DC2626' : '#475569' }}>
                        {rec.urgency}
                      </span>
                    </td>
                    <td>
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => onViewRecord(rec)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {total > 5 && (
          <div style={{ marginTop: '16px', textAlign: 'right' }}>
            <button
              className="btn btn-secondary btn-small"
              onClick={() => onNavigate('history')}
            >
              View All {total} Patient Records &rarr;
            </button>
          </div>
        )}
      </div>

      {/* 3. Clinical Guidelines Note */}
      <div className="card" style={{ backgroundColor: '#F8FAFC' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#334155', marginBottom: '8px' }}>
          Prediction system for Heart Disease & Diabetes
        </h3>
        <p style={{ fontSize: '13px', color: '#64748B', lineHeight: '1.6' }}>
          Our AI-powered system predicts the risk of heart disease and diabetes from symptoms and clinical parameters to support early detection and better healthcare decisions.
        </p>
      </div>
    </div>
  );
}
