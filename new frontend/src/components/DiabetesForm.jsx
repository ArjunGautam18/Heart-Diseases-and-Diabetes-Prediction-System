import { useState } from "react";
import { useNavigate } from "react-router-dom";
import jsPDF from "jspdf";
import { createWorker } from "tesseract.js";
import HealthCoachChat from "./HealthCoachChat";
import { extractDiabetesFromText } from "../utils/diabetesReportParser.js";
import { API_BASE } from "../utils/api";

const GENDER_OPTIONS = ["Female", "Male", "Other"];

const SMOKING_OPTIONS = [
  { label: "No Info", value: "No Info" },
  { label: "Never", value: "never" },
  { label: "Former", value: "former" },
  { label: "Current", value: "current" },
  { label: "Not Current", value: "not current" },
  { label: "Ever", value: "ever" },
];

const DIABETES_DEMO_PRESETS = {
  low: {
    age: 22, gender: "Female", hypertension: 0, heart_disease: 0,
    smoking_history: "never", bmi: 20.0, HbA1c_level: 4.5, blood_glucose_level: 85,
  },
  moderate: {
    age: 55, gender: "Male", hypertension: 1, heart_disease: 0,
    smoking_history: "current", bmi: 33.0, HbA1c_level: 5.8, blood_glucose_level: 130,
  },
  high: {
    age: 65, gender: "Male", hypertension: 1, heart_disease: 1,
    smoking_history: "current", bmi: 38.0, HbA1c_level: 8.5, blood_glucose_level: 220,
  },
};

const RISK_COLORS = {
  Low: "#16a34a",
  Moderate: "#d97706",
  High: "#dc2626",
};

function getDiabetesRiskFactors(formData) {
  const factors = [];

  if (formData.age >= 45) factors.push("Age 45+");
  if (formData.bmi >= 25) factors.push("High BMI");
  if (formData.HbA1c_level >= 6.5) factors.push("Elevated HbA1c");
  if (formData.blood_glucose_level >= 140) factors.push("High blood glucose");
  if (formData.hypertension === 1) factors.push("Hypertension");
  if (formData.heart_disease === 1) factors.push("Heart disease history");
  if (formData.smoking_history !== "never" && formData.smoking_history !== "No Info") factors.push("Smoking history");

  return factors.length ? factors.slice(0, 5) : ["Stable glycemic profile"];
}

function RiskDashboard({ disease, result, formData }) {
  const score = Math.round((Number(result?.probability ?? 0) || 0) * 100);
  const level = result?.risk_level || (score >= 70 ? "High" : score >= 40 ? "Moderate" : "Low");
  const factors = disease === "heart" ? getHeartRiskFactors(formData) : getDiabetesRiskFactors(formData);

  return (
    <div className="risk-dashboard">
      <div className="risk-header-row">
        <div>
          <p className="risk-label">{disease === "heart" ? "Heart Disease" : "Diabetes"} Risk</p>
          <h3>{level}</h3>
        </div>
        <span className={`risk-badge ${String(level).toLowerCase()}`}>{level}</span>
      </div>

      <div className="risk-metrics">
        <div className="metric-box">
          <span>Risk Score</span>
          <strong>{score}%</strong>
        </div>
      </div>

      <div className="risk-factors">
        <p>Main Risk Factors</p>
        <ul>
          {factors.map((factor) => (
            <li key={factor}>✓ {factor}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function DiabetesForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    age: 33,
    gender: "Female",
    hypertension: 0,
    heart_disease: 0,
    smoking_history: "No Info",
    bmi: 25.0,
    HbA1c_level: 5.5,
    blood_glucose_level: 120,
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [patientName, setPatientName] = useState("");
  const [inputMode, setInputMode] = useState("manual");
  const [reportStatus, setReportStatus] = useState("");
  const [autofilledFields, setAutofilledFields] = useState([]);
  const [uploadedFileName, setUploadedFileName] = useState("");

  const generateReport = () => {
    if (!result) return;

    const doc = new jsPDF();
    const score = ((result.probability || 0) * 100).toFixed(1);
    const safeLevel = result.risk_level || "Moderate";
    const reportName = patientName.trim() || "Not provided";

    doc.setFillColor(15, 23, 42);
    doc.rect(0, 0, 210, 30, "F");
    doc.setTextColor(255, 255, 255);
    doc.setFontSize(22);
    doc.text("Medicare Report", 14, 20);

    doc.setTextColor(15, 23, 42);
    doc.setFontSize(14);
    doc.text("Diabetes Risk Assessment", 14, 42);
    doc.setFontSize(11);
    doc.text(`Patient Name: ${reportName}`, 14, 58);
    doc.text(`Risk Score: ${score}%`, 14, 68);
    doc.text(`Risk Level: ${safeLevel}`, 14, 78);
    doc.text(`Health Score: ${result.health_score ?? "N/A"} / 100`, 14, 88);
    doc.text(`Risk Level: ${result.risk_level || "Unknown"}`, 14, 98);

    const factors = getDiabetesRiskFactors(formData);
    doc.text("Main Risk Factors:", 14, 118);
    factors.forEach((factor, index) => {
      doc.text(`• ${factor}`, 18, 128 + index * 10);
    });

    doc.text("Disclaimer: This report is for educational use only and not a clinical diagnosis.", 14, 180);
    doc.save(`medicare-diabetes-risk-report-${reportName.replace(/\s+/g, "-") || "patient"}.pdf`);
  };

  const handleChange = (e) => {
  const { name, value, type } = e.target;
  setAutofilledFields((fields) => fields.filter((field) => field !== name));
  if (type === "number") {
    // Strip leading zeros while typing (but allow "0" and decimals like "0.5")
    const cleaned = value.replace(/^0+(?=\d)/, "");
    setFormData({ ...formData, [name]: cleaned === "" ? "" : Number(cleaned) });
  } else {
    setFormData({ ...formData, [name]: value });
  }
};

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/predict/diabetes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errText = await response.text();
        if (response.status === 401) {
          navigate("/login", { replace: true, state: { message: "Please log in before making a prediction." } });
          return;
        }
        throw new Error(`Server error: ${response.status} - ${errText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReportUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setReportStatus("Reading diabetes report...");
    setError(null);
    try {
      const upload = new FormData();
      upload.append("file", file);
      upload.append("disease", "diabetes");
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 20000);
      let response = null;
      try {
        response = await fetch(`${API_BASE}/extract-report`, {
          method: "POST", body: upload, signal: controller.signal,
          credentials: "include",
        });
      } catch {
        // Fall through to local OCR.
      } finally {
        window.clearTimeout(timeoutId);
      }
      if (response?.ok) {
        const extracted = await response.json();
        const nextData = { ...formData };
        const populatedFields = [];
        Object.entries(extracted).forEach(([key, value]) => {
          if (key !== "patientName" && value !== null && value !== undefined) {
            nextData[key] = value;
            populatedFields.push(key);
          }
        });
        setFormData(nextData);
        if (extracted.patientName) setPatientName(extracted.patientName);
        setAutofilledFields(populatedFields);
        setReportStatus(`${populatedFields.length} fields extracted from the report. Please review before prediction.`);
        return;
      }

      setReportStatus("Backend extraction unavailable. Scanning locally...");
      let worker;
      try {
        worker = await Promise.race([
          createWorker("eng"),
          new Promise((_, reject) => window.setTimeout(() => reject(new Error("OCR timed out")), 30000)),
        ]);
        const ocr = await Promise.race([
          worker.recognize(file),
          new Promise((_, reject) => window.setTimeout(() => reject(new Error("OCR timed out")), 30000)),
        ]);
        const parsed = extractDiabetesFromText(ocr.data.text, formData);
        setFormData(parsed.nextData);
        if (parsed.patientName) setPatientName(parsed.patientName);
        const modelFields = ["age", "gender", "hypertension", "heart_disease", "smoking_history", "bmi", "HbA1c_level", "blood_glucose_level"];
        const extractedModelFields = parsed.fields.filter((field) => modelFields.includes(field));
        setAutofilledFields(extractedModelFields);
        setReportStatus(extractedModelFields.length
          ? `${extractedModelFields.length} diabetes inputs extracted locally. Please review before prediction.`
          : "No diabetes inputs were found. Please enter the values manually.");
      } finally {
        if (worker) await worker.terminate().catch(() => {});
      }
    } catch (err) {
      setReportStatus("");
      setError(err.name === "AbortError"
        ? "Report extraction timed out. Please enter the values manually."
        : `Could not read the report: ${err.message}. Please enter the values manually.`);
    } finally {
      e.target.value = "";
    }
  };

  const loadDemo = (tier) => {
    setFormData(DIABETES_DEMO_PRESETS[tier]);
    setResult(null);
    setError(null);
  };

  const autofillClass = (field) => autofilledFields.includes(field) ? "autofilled-field" : "";

  return (
    <div className="card">
      <h2>🩸 Diabetes Risk Prediction</h2>
      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button type="button" onClick={() => loadDemo("low")} style={{ padding: "0.4rem 0.9rem", borderRadius: "6px", border: "1px solid #16a34a", background: "#f0fdf4", color: "#16a34a", cursor: "pointer", fontWeight: 600 }}>
          Demo: Low Risk
        </button>
        <button type="button" onClick={() => loadDemo("moderate")} style={{ padding: "0.4rem 0.9rem", borderRadius: "6px", border: "1px solid #d97706", background: "#fffbeb", color: "#b45309", cursor: "pointer", fontWeight: 600 }}>
          Demo: Moderate Risk
        </button>
        <button type="button" onClick={() => loadDemo("high")} style={{ padding: "0.4rem 0.9rem", borderRadius: "6px", border: "1px solid #dc2626", background: "#fef2f2", color: "#dc2626", cursor: "pointer", fontWeight: 600 }}>
          Demo: High Risk
        </button>
      </div>
      <div role="tablist" aria-label="Prediction input method" style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button type="button" role="tab" aria-selected={inputMode === "manual"} onClick={() => { setInputMode("manual"); setReportStatus(""); setAutofilledFields([]); }} style={{ padding: "0.5rem 1rem", borderRadius: "6px", border: "1px solid #2563eb", background: inputMode === "manual" ? "#2563eb" : "#fff", color: inputMode === "manual" ? "#fff" : "#2563eb", cursor: "pointer", fontWeight: 600 }}>Enter Manually</button>
        <button type="button" role="tab" aria-selected={inputMode === "report"} onClick={() => { setInputMode("report"); setError(null); }} style={{ padding: "0.5rem 1rem", borderRadius: "6px", border: "1px solid #2563eb", background: inputMode === "report" ? "#2563eb" : "#fff", color: inputMode === "report" ? "#fff" : "#2563eb", cursor: "pointer", fontWeight: 600 }}>Upload Medical Report</button>
      </div>
      <form onSubmit={handleSubmit}>
        {inputMode === "report" && (
          <div className="form-group" style={{ marginBottom: "1rem" }}>
            <label htmlFor="diabetes-medical-report-upload">Upload diabetes medical report</label>
            <input id="diabetes-medical-report-upload" type="file" accept="image/png,image/jpeg,image/jpg,image/webp" onChange={(event) => { setUploadedFileName(event.target.files?.[0]?.name || ""); handleReportUpload(event); }} />
            {uploadedFileName && <small style={{ display: "block", marginTop: "0.5rem" }}>Selected report: {uploadedFileName}</small>}
            {reportStatus && <small style={{ display: "block", marginTop: "0.5rem", color: "#2563eb" }}>{reportStatus}</small>}
          </div>
        )}
        <div className="form-grid">
          <div className="form-group">
            <label>Patient Name</label>
            <input type="text" value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="Enter patient name" />
          </div>

          <div className="form-group">
            <label>Age</label>
            <input className={autofillClass("age")} type="number" name="age" value={formData.age} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Gender</label>
            <select className={autofillClass("gender")} name="gender" value={formData.gender} onChange={handleChange}>
              {GENDER_OPTIONS.map((g) => (
                <option key={g} value={g}>{g}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Hypertension</label>
            <select className={autofillClass("hypertension")} name="hypertension" value={formData.hypertension} onChange={handleChange}>
              <option value={0}>No</option>
              <option value={1}>Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Heart Disease</label>
            <select className={autofillClass("heart_disease")} name="heart_disease" value={formData.heart_disease} onChange={handleChange}>
              <option value={0}>No</option>
              <option value={1}>Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Smoking History</label>
            <select className={autofillClass("smoking_history")} name="smoking_history" value={formData.smoking_history} onChange={handleChange}>
              {SMOKING_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>BMI</label>
            <input className={autofillClass("bmi")} type="number" step="0.1" name="bmi" value={formData.bmi} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>HbA1c Level</label>
            <input className={autofillClass("HbA1c_level")} type="number" step="0.1" name="HbA1c_level" value={formData.HbA1c_level} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Blood Glucose Level</label>
            <input className={autofillClass("blood_glucose_level")} type="number" name="blood_glucose_level" value={formData.blood_glucose_level} onChange={handleChange} />
          </div>
        </div>

        <div className="action-row">
          <button type="submit" disabled={loading}>
            {loading ? "Predicting..." : "Predict Diabetes"}
          </button>
          {result && (
            <button type="button" className="secondary-btn" onClick={generateReport}>
              Export PDF
            </button>
          )}
        </div>
      </form>

      {error && <p style={{ color: "red" }}>Error: {error}</p>}

      {result && (
        <>
          <RiskDashboard disease="diabetes" result={result} formData={formData} />

          <div className={`result ${String(result.risk_level || "unknown").toLowerCase()}`}>
            <h3>{result.risk_level === "High" ? "⚠️ High Risk" : result.risk_level === "Moderate" ? "⚠️ Moderate Risk" : "✅ Low Risk"}</h3>

            <p
              style={{
                fontWeight: 600,
                color: RISK_COLORS[result.risk_level] || "#333",
              }}
            >
              Risk Level: {result.risk_level}
            </p>

            <p>Probability: {(result.probability * 100).toFixed(1)}%</p>

            <p>Health Score: {result.health_score} / 100</p>

            {result.message && <p>{result.message}</p>}
          </div>

          <HealthCoachChat
            disease="diabetes"
            riskLevel={result.risk_level}
            inputData={formData}
          />
        </>
      )}
    </div>
  );
}

export default DiabetesForm;