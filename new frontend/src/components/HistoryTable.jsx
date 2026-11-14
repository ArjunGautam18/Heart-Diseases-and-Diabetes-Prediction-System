import React, { useState } from 'react';
import { exportToCSV } from '../utils/storage';

export default function HistoryTable({ records, onDeleteRecord, onResetRecords, onViewRecord, onNewScreening }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');

  const filteredRecords = records.filter((r) => {
    const matchesSearch =
      r.patientId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.notes.toLowerCase().includes(searchTerm.toLowerCase());

    if (riskFilter === 'all') return matchesSearch;
    if (riskFilter === 'high') {
      return matchesSearch && (r.heartRisk === 'High' || r.diabetesRisk === 'High');
    }
    if (riskFilter === 'moderate') {
      return (
        matchesSearch &&
        (r.heartRisk === 'Moderate' || r.diabetesRisk === 'Moderate') &&
        r.heartRisk !== 'High' &&
        r.diabetesRisk !== 'High'
      );
    }
    if (riskFilter === 'low') {
      return matchesSearch && r.heartRisk === 'Low' && r.diabetesRisk === 'Low';
    }
    return matchesSearch;
  });

  const getBadgeClass = (level) => {
    if (level === 'High') return 'badge badge-high';
    if (level === 'Moderate') return 'badge badge-moderate';
    return 'badge badge-low';
  };

  return (
    <div>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 className="card-title" style={{ border: 'none', marginBottom: '4px' }}>
              Patient Screening History &amp; Logs
            </h2>
            <p className="card-subtitle" style={{ marginBottom: 0 }}>
              Complete record of diagnostic symptom checklists and risk scores
            </p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            
            <button
              id="new-screen-top-btn"
              className="btn btn-primary btn-small"
              onClick={onNewScreening}
            >
              + New Screening
            </button>
          </div>
        </div>

        {/* Filter and Search Bar */}
        <div className="grid-3" style={{ marginBottom: '16px' }}>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="search-input">Search Records</label>
            <input
              id="search-input"
              type="text"
              className="input-field"
              placeholder="Search by Patient ID, Name, or Note..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label className="form-label" htmlFor="risk-filter-select">Filter by Risk Category</label>
            <select
              id="risk-filter-select"
              className="select-field"
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
            >
              <option value="all">All Risk Levels ({records.length})</option>
              <option value="high">High Risk Cases</option>
              <option value="moderate">Moderate Risk</option>
              <option value="low">Low Risk / Normal</option>
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end' }}>
            
          </div>
        </div>

        {/* Table View */}
        {filteredRecords.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '36px 12px', color: '#64748B', backgroundColor: '#FAFAFC', border: '1px dashed #CBD5E1', borderRadius: '4px' }}>
            <p style={{ fontWeight: 500 }}>No screening records matched your query.</p>
            <p style={{ fontSize: '13px', marginTop: '4px' }}>Try clearing the search filter or conduct a new screening.</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Date &amp; Time</th>
                  <th>Patient ID</th>
                  <th>Name</th>
                  <th>Age / Sex</th>
                  <th>Vitals (BP / Sugar)</th>
                  <th>Heart Disease Risk</th>
                  <th>Diabetes Risk</th>
                  <th>Clinical Urgency</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecords.map((r) => (
                  <tr key={r.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '12px', color: '#64748B' }}>{r.id}</td>
                    <td>
                      <div>{r.date}</div>
                      <div style={{ fontSize: '11px', color: '#94A3B8' }}>{r.time}</div>
                    </td>
                    <td style={{ fontWeight: 600, color: '#1E293B' }}>{r.patientId}</td>
                    <td>
                      <div>{r.name}</div>
                      {r.phone && <div style={{ fontSize: '11px', color: '#64748B' }}>{r.phone}</div>}
                    </td>
                    <td>{r.age} yrs / {r.gender}</td>
                    <td>
                      <div>{r.systolicBP}/{r.diastolicBP} mmHg</div>
                      <div style={{ fontSize: '11px', color: '#64748B' }}>
                        {r.fastingSugar ? `${r.fastingSugar} mg/dL` : 'FBS not logged'}
                      </div>
                    </td>
                    <td>
                      <span className={getBadgeClass(r.heartRisk)}>
                        {r.heartRisk} ({r.heartScore}%)
                      </span>
                    </td>
                    <td>
                      <span className={getBadgeClass(r.diabetesRisk)}>
                        {r.diabetesRisk} ({r.diabetesScore}%)
                      </span>
                    </td>
                    <td>
                      <span style={{ fontSize: '12px', fontWeight: 500, color: r.urgency.includes('Immediate') ? '#DC2626' : '#334155' }}>
                        {r.urgency}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className="btn btn-secondary btn-small"
                          onClick={() => onViewRecord(r)}
                        >
                          Details
                        </button>
                        <button
                          className="btn btn-danger btn-small"
                          onClick={() => {
                            if (window.confirm(`Delete record for ${r.name} (${r.patientId})?`)) {
                              onDeleteRecord(r.id);
                            }
                          }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
