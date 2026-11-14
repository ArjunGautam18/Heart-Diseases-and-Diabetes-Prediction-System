import { useState } from "react";
import { useNavigate } from "react-router-dom";
import jsPDF from "jspdf";
import { createWorker } from "tesseract.js";
import HealthCoachChat from "./HealthCoachChat";
import { API_BASE } from "../utils/api";

const CP_OPTIONS = [
  { label: "Chest pain during activity", value: "typical angina" },
  { label: "Chest pain with unusual symptoms", value: "atypical angina" },
  { label: "Chest discomfort not related to the heart", value: "non-anginal" },
  { label: "No chest pain", value: "asymptomatic" },
];

const RESTECG_OPTIONS = [
  { label: "Normal", value: "normal" },
  { label: "Some changes detected", value: "st-t abnormality" },
  { label: "Thickened heart muscle", value: "lv hypertrophy" },
];

const SLOPE_OPTIONS = [
  { label: "Heart rate rises normally", value: "upsloping" },
  { label: "Heart rate stays about the same", value: "flat" },
  { label: "Heart rate falls during the test", value: "downsloping" },
];

const THAL_OPTIONS = [
  { label: "Normal blood flow", value: "normal" },
  { label: "Reduced blood flow that stays the same", value: "fixed defect" },
  { label: "Reduced blood flow during activity", value: "reversable defect" },
];

const HEART_DEMO_PRESETS = {
  low: {
    age: 28, sex: "Female", cp: "typical angina",
    trestbps: 105, chol: 160, fbs: 0,
    restecg: "normal", thalch: 185, exang: 0,
    oldpeak: 0, slope: "upsloping", ca: 0, thal: "normal",
    hypertension: "No", heightCm: 170, weightKg: 60, bmi: 20.8,
    diabetes: "No", smoking: "No", alcohol: "No", exercise: "Yes",
    familyHistory: "No", diet: "Yes", stress: "No",
  },
  moderate: {
    age: 55, sex: "Male", cp: "non-anginal",
    trestbps: 138, chol: 235, fbs: 0,
    restecg: "normal", thalch: 120, exang: 1,
    oldpeak: 1.2, slope: "flat", ca: 0, thal: "normal",
    hypertension: "Yes", heightCm: 172, weightKg: 83, bmi: 28.1,
    diabetes: "No", smoking: "Yes", alcohol: "No", exercise: "No",
    familyHistory: "Yes", diet: "No", stress: "Yes",
  },
  high: {
    age: 68, sex: "Male", cp: "asymptomatic",
    trestbps: 170, chol: 300, fbs: 1,
    restecg: "st-t abnormality", thalch: 100, exang: 1,
    oldpeak: 3.5, slope: "flat", ca: 3, thal: "reversable defect",
    hypertension: "Yes", heightCm: 168, weightKg: 98, bmi: 34.7,
    diabetes: "Yes", smoking: "Yes", alcohol: "Yes", exercise: "No",
    familyHistory: "Yes", diet: "No", stress: "Yes",
  },
};

const RISK_COLORS = {
  Low: "#16a34a",
  Moderate: "#d97706",
  High: "#dc2626",
};

function firstNumber(text, pattern) {
  const match = text.match(pattern);
  return match ? Number(match[1]) : null;
}

function valueFromLines(lines, pattern, minimum, maximum) {
  for (const line of lines || []) {
    const match = line.text.toLowerCase().match(pattern);
    if (!match) continue;
    const value = Number(match[1].replace(/,/g, ""));
    if (Number.isFinite(value) && value >= minimum && value <= maximum) return value;
  }
  return null;
}

function booleanFromLines(lines, pattern) {
  for (const line of lines || []) {
    const match = line.text.toLowerCase().match(pattern);
    if (match) return match[1] === "yes" ? "Yes" : "No";
  }
  return null;
}

function numberNearLabel(words, labels, minimum, maximum) {
  if (!words?.length) return null;
  const anchors = words.filter((word) => labels.some((label) => label.test(word.text.toLowerCase())));
  const numbers = words
    .map((word) => ({ word, value: Number(word.text.replace(/,/g, "")) }))
    .filter(({ word, value }) => Number.isFinite(value) && value >= minimum && value <= maximum);
  let best = null;
  for (const anchor of anchors) {
    const anchorX = (anchor.bbox.x0 + anchor.bbox.x1) / 2;
    const anchorBottom = anchor.bbox.y1;
    for (const candidate of numbers) {
      const candidateX = (candidate.word.bbox.x0 + candidate.word.bbox.x1) / 2;
      const verticalDistance = candidate.word.bbox.y0 - anchorBottom;
      const horizontalDistance = Math.abs(candidateX - anchorX);
      if (verticalDistance >= -4 && verticalDistance <= 110 && horizontalDistance <= 115) {
        const score = Math.max(verticalDistance, 0) + horizontalDistance * 0.25;
        if (!best || score < best.score) best = { value: candidate.value, score };
      }
    }
  }
  return best?.value ?? null;
}

function wordNearLabel(words, labels, values) {
  if (!words?.length) return null;
  const anchors = words.filter((word) => labels.some((label) => label.test(word.text.toLowerCase())));
  const candidates = words.filter((word) => values.includes(word.text.trim().toLowerCase()));
  let best = null;
  for (const anchor of anchors) {
    const anchorX = (anchor.bbox.x0 + anchor.bbox.x1) / 2;
    for (const candidate of candidates) {
      const candidateX = (candidate.bbox.x0 + candidate.bbox.x1) / 2;
      const verticalDistance = candidate.bbox.y0 - anchor.bbox.y1;
      const horizontalDistance = Math.abs(candidateX - anchorX);
      if (verticalDistance >= -4 && verticalDistance <= 110 && horizontalDistance <= 115) {
        const score = Math.max(verticalDistance, 0) + horizontalDistance * 0.25;
        if (!best || score < best.score) best = { value: candidate.text.trim(), score };
      }
    }
  }
  return best?.value ?? null;
}

function parseReportText(text, currentData, words = [], lines = []) {
  const normalized = text.replace(/[|:]/g, " ").replace(/\s+/g, " ").toLowerCase();
  const nextData = { ...currentData };
  const extracted = [];
  let patientName = "";
  const setNumber = (field, value, label) => {
    if (value !== null && Number.isFinite(value)) {
      nextData[field] = value;
      extracted.push(label);
    }
  };

  const patientNameMatch = normalized.match(/patient\s+name\s+([a-z]+(?:\s+[a-z]+){1,3})\s+age\b/);
  if (patientNameMatch) {
    patientName = patientNameMatch[1]
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
    extracted.push("patient name");
  }

  const reportGender = wordNearLabel(words, [/^gender$/], ["male", "female"]);
  if (reportGender) {
    nextData.sex = reportGender === "female" ? "Female" : "Male";
    extracted.push("gender");
  } else {
    const genderMatch = normalized.match(/gender\D{0,18}(male|female)/);
    if (genderMatch) {
      nextData.sex = genderMatch[1] === "female" ? "Female" : "Male";
      extracted.push("gender");
    }
  }

  // Report values may contain units, parentheses, or several words between a label and value.
  setNumber("age", valueFromLines(lines, /age\D{0,20}(\d{1,3})/, 1, 120) ?? numberNearLabel(words, [/^age$/], 1, 120) ?? firstNumber(normalized, /(?:age|years? old)\D{0,30}(\d{1,3})/), "age");
  setNumber("chol", valueFromLines(lines, /(?:total\s+cholesterol|cholesterol)\D{0,20}(\d{3,4})/, 100, 600) ?? numberNearLabel(words, [/cholesterol/], 100, 600) ?? firstNumber(normalized, /(?:total\s+cholesterol|cholesterol|chol)\D{0,30}(\d{3,4})/), "cholesterol");
  setNumber("trestbps", valueFromLines(lines, /(?:blood pressure|systolic)\D{0,20}(\d{2,3})/, 80, 250) ?? numberNearLabel(words, [/systolic/, /blood/], 80, 250) ?? firstNumber(normalized, /(?:blood pressure|bp|systolic)\D{0,30}(\d{2,3})/), "blood pressure");
  setNumber("thalch", valueFromLines(lines, /(?:maximum heart rate|max heart rate|peak heart rate)\D{0,20}(\d{2,3})/, 40, 240) ?? numberNearLabel(words, [/maximum heart rate/, /max heart rate/, /peak heart rate/], 40, 240) ?? firstNumber(normalized, /(?:maximum heart rate|max heart rate|peak heart rate)\D{0,30}(\d{2,3})/), "maximum heart rate");
  setNumber("bmi", valueFromLines(lines, /bmi\D{0,20}(\d{2}(?:\.\d)?)/, 10, 80) ?? numberNearLabel(words, [/^bmi$/], 10, 80) ?? firstNumber(normalized, /bmi\D{0,30}(\d{2}(?:\.\d)?)/), "BMI");
  setNumber("heightCm", valueFromLines(lines, /height\D{0,20}(\d{2,3})/, 50, 250) ?? numberNearLabel(words, [/height/], 50, 250) ?? firstNumber(normalized, /height\D{0,30}(\d{2,3})\s*(?:cm)?/), "height");
  setNumber("weightKg", valueFromLines(lines, /weight\D{0,20}(\d{2,3}(?:\.\d)?)/, 2, 300) ?? numberNearLabel(words, [/weight/], 2, 300) ?? firstNumber(normalized, /weight\D{0,30}(\d{2,3}(?:\.\d)?)\s*(?:kg)?/), "weight");
  setNumber("oldpeak", firstNumber(normalized, /(?:oldpeak|st depression|st-depression)\D{0,30}(\d+(?:\.\d)?)/), "stress-test reading");
  const fastingSugar = firstNumber(normalized, /(?:fasting blood sugar|fasting glucose)\D{0,30}(\d{2,3})/);
  if (fastingSugar !== null) {
    nextData.fbs = fastingSugar > 120 ? 1 : 0;
    extracted.push("fasting blood sugar");
  }

  const yes = (label) => new RegExp(`${label}\\D{0,18}(yes|positive|present)`).test(normalized);
  const no = (label) => new RegExp(`${label}\\D{0,18}(no|negative|absent)`).test(normalized);
  [["hypertension", "hypertension"], ["diabetes", "diabetes"], ["smoking", "smok(?:ing|er)"], ["familyHistory", "family history(?: of cvd)?"], ["exercise", "regular exercise"], ["diet", "healthy diet"], ["stress", "high stress(?: level)?"], ["alcohol", "alcohol consumption"]].forEach(([field, label]) => {
    const lineValue = booleanFromLines(lines, new RegExp(`${label}\\D{0,35}(yes|no|positive|negative|present|absent)`));
    if (lineValue) { nextData[field] = lineValue; extracted.push(field); }
    else if (yes(label)) { nextData[field] = "Yes"; extracted.push(field); }
    else if (no(label)) { nextData[field] = "No"; extracted.push(field); }
  });

  if (/chest pain\s*(?:\/\s*)?discomfort\D{0,40}(during activity|with activity|yes|positive)/.test(normalized)) {
    nextData.cp = "typical angina";
    nextData.exang = 1;
    extracted.push("chest pain");
  }

  if (nextData.heightCm && nextData.weightKg) {
    nextData.bmi = Number((nextData.weightKg / ((nextData.heightCm / 100) ** 2)).toFixed(1));
  }
  return { nextData, patientName, extracted: [...new Set(extracted)] };
}

function getHeartRiskFactors(formData) {
  const factors = [];

  if (formData.age >= 50) factors.push("Age 50+");
  if (formData.chol > 200) factors.push("High cholesterol");
  if (formData.trestbps >= 140) factors.push("High blood pressure");
  if (formData.hypertension === "Yes") factors.push("Hypertension history");
  if (formData.smoking === "Yes") factors.push("Smoking history");
  if (formData.familyHistory === "Yes") factors.push("Family history of heart disease");
  if (formData.stress === "Yes") factors.push("Reported stress");
  if (formData.oldpeak > 1.0) factors.push("ST depression");
  if (formData.exang === 1) factors.push("Exercise-induced angina");
  if (formData.ca > 1) factors.push("Multiple vessel involvement");
  if (formData.thalch < 150) factors.push("Lower max heart rate");

  return factors.length ? factors.slice(0, 5) : ["Stable cardiovascular profile"];
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

function HeartForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    age: 54,
    sex: "Male",
    cp: "typical angina",
    trestbps: 140,
    chol: 250,
    fbs: 0,
    restecg: "normal",
    thalch: 150,
    exang: 0,
    oldpeak: 1.0,
    slope: "flat",
    ca: 0,
    thal: "normal",
    hypertension: "No",
    heightCm: 170,
    weightKg: 70,
    bmi: 24.2,
    diabetes: "No",
    smoking: "No",
    alcohol: "No",
    exercise: "Yes",
    familyHistory: "No",
    diet: "Yes",
    stress: "No",
  });

  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [patientName, setPatientName] = useState("");
  const [reportStatus, setReportStatus] = useState("");
  const [inputMode, setInputMode] = useState("manual");
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
    doc.text("Heart Disease Risk Assessment", 14, 42);
    doc.setFontSize(11);
    doc.text(`Patient Name: ${reportName}`, 14, 58);
    doc.text(`Risk Score: ${score}%`, 14, 68);
    doc.text(`Risk Level: ${safeLevel}`, 14, 78);
    doc.text(`Health Score: ${result.health_score ?? "N/A"} / 100`, 14, 88);
    doc.text(`Risk Level: ${result.risk_level || "Unknown"}`, 14, 98);

    const factors = getHeartRiskFactors(formData);
    doc.text("Main Risk Factors:", 14, 118);
    factors.forEach((factor, index) => {
      doc.text(`• ${factor}`, 18, 128 + index * 10);
    });

    doc.text("Disclaimer: This report is for educational use only and not a clinical diagnosis.", 14, 180);
    doc.save(`medicare-heart-risk-report-${reportName.replace(/\s+/g, "-") || "patient"}.pdf`);
  };

  const handleChange = (e) => {
  const { name, value, type } = e.target;
  setAutofilledFields((fields) => fields.filter((field) => field !== name));
  if (type === "number") {
    // Strip leading zeros while typing (but allow "0" and decimals like "0.5")
    const cleaned = value.replace(/^0+(?=\d)/, "");
    const numericValue = cleaned === "" ? "" : Number(cleaned);
    const nextData = { ...formData, [name]: numericValue };
    if (name === "heightCm" || name === "weightKg") {
      const height = Number(name === "heightCm" ? numericValue : formData.heightCm) / 100;
      const weight = Number(name === "weightKg" ? numericValue : formData.weightKg);
      nextData.bmi = height > 0 && weight > 0 ? Number((weight / (height * height)).toFixed(1)) : "";
    }
    setFormData(nextData);
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
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 15000);
      const response = await fetch(`${API_BASE}/predict/heart`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(formData),
        signal: controller.signal,
      });
      window.clearTimeout(timeoutId);

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
      setError(err.name === "AbortError"
        ? "Prediction timed out. Restart the backend with start.bat and try again."
        : `Prediction failed: ${err.message}. Check that the FastAPI backend is running.`);
    } finally {
      setLoading(false);
    }
  };

  const handleReportUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setReportStatus("Reading report...");
    setError(null);
    try {
      const upload = new FormData();
      upload.append("file", file);
      upload.append("disease", "heart");
      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 20000);
      let visionResponse = null;
      try {
        visionResponse = await fetch(`${API_BASE}/extract-report`, {
          method: "POST",
          credentials: "include",
          body: upload,
          signal: controller.signal,
        });
      } catch {
        // Use browser OCR if the backend vision service is unavailable.
      } finally {
        window.clearTimeout(timeoutId);
      }
      if (visionResponse?.ok) {
        const extracted = await visionResponse.json();
        const nextData = { ...formData };
        const populatedFields = [];
        Object.entries(extracted).forEach(([key, value]) => {
          if (key !== "patientName" && value !== null && value !== undefined) {
            nextData[key] = value;
            populatedFields.push(key);
          }
        });
        if (nextData.heightCm && nextData.weightKg) {
          nextData.bmi = Number((nextData.weightKg / ((nextData.heightCm / 100) ** 2)).toFixed(1));
          if (!populatedFields.includes("bmi")) populatedFields.push("bmi");
        }
        setFormData(nextData);
        if (extracted.patientName) setPatientName(extracted.patientName);
        setAutofilledFields(populatedFields);
        setReportStatus(`${populatedFields.length} fields extracted from the report. Please review before prediction.`);
        return;
      }

      // Browser OCR remains the offline fallback.
      setReportStatus("Backend unavailable. Scanning report locally...");
      let worker;
      let result;
      try {
        worker = await Promise.race([
          createWorker("eng"),
          new Promise((_, reject) => window.setTimeout(() => reject(new Error("OCR timed out")), 30000)),
        ]);
        result = await Promise.race([
          worker.recognize(file),
          new Promise((_, reject) => window.setTimeout(() => reject(new Error("OCR timed out")), 30000)),
        ]);
      } finally {
        if (worker) await worker.terminate().catch(() => {});
      }
      const parsed = parseReportText(result.data.text, formData, result.data.words, result.data.lines);
      setFormData(parsed.nextData);
      if (parsed.patientName) setPatientName(parsed.patientName);
      setAutofilledFields(parsed.extracted.map((field) => ({
        "blood pressure": "trestbps",
        cholesterol: "chol",
        "fasting blood sugar": "fbs",
        "chest pain": "cp",
        gender: "sex",
        height: "heightCm",
        weight: "weightKg",
        age: "age",
      }[field] || field)).filter((field, index, fields) => fields.indexOf(field) === index));
      setReportStatus(parsed.extracted.length
        ? `${parsed.extracted.length} fields extracted from the report. Please review before prediction.`
        : "No supported values were found. Please enter the values manually.");
    } catch (err) {
      setReportStatus("");
      const message = err.name === "AbortError" ? "AI extraction timed out" : err.message;
      setError(`Could not read the report: ${message}. Please enter the values manually.`);
    } finally {
      e.target.value = "";
    }
  };

  const loadDemo = (tier) => {
    setFormData((current) => ({ ...current, ...HEART_DEMO_PRESETS[tier] }));
    setResult(null);
    setError(null);
  };

  const autofillClass = (field) => autofilledFields.includes(field) ? "autofilled-field" : "";

  return (
    <div className="card">
      <h2>❤️ Heart Disease Risk Prediction</h2>
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
        <button
          type="button"
          role="tab"
          aria-selected={inputMode === "manual"}
          onClick={() => { setInputMode("manual"); setReportStatus(""); setAutofilledFields([]); }}
          style={{ padding: "0.5rem 1rem", borderRadius: "6px", border: "1px solid #2563eb", background: inputMode === "manual" ? "#2563eb" : "#fff", color: inputMode === "manual" ? "#fff" : "#2563eb", cursor: "pointer", fontWeight: 600 }}
        >
          Enter Manually
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={inputMode === "report"}
          onClick={() => { setInputMode("report"); setError(null); }}
          style={{ padding: "0.5rem 1rem", borderRadius: "6px", border: "1px solid #2563eb", background: inputMode === "report" ? "#2563eb" : "#fff", color: inputMode === "report" ? "#fff" : "#2563eb", cursor: "pointer", fontWeight: 600 }}
        >
          Upload Medical Report
        </button>
      </div>
      <form onSubmit={handleSubmit}>
        {inputMode === "report" && (
          <div className="form-group" style={{ marginBottom: "1rem" }}>
            <label htmlFor="medical-report-upload">Upload medical report image</label>
            <input id="medical-report-upload" type="file" accept="image/png,image/jpeg,image/jpg,image/webp" onChange={(event) => { setUploadedFileName(event.target.files?.[0]?.name || ""); handleReportUpload(event); }} />
            {uploadedFileName && <small>Selected report: {uploadedFileName}</small>}
            {reportStatus && <small>{reportStatus}</small>}
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
            <select className={autofillClass("sex")} name="sex" value={formData.sex} onChange={handleChange}>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
            </select>
          </div>

          <div className="form-group">
            <label>Hypertension</label>
            <select className={autofillClass("hypertension")} name="hypertension" value={formData.hypertension} onChange={handleChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Height (cm)</label>
            <input className={autofillClass("heightCm")} type="number" name="heightCm" min="50" max="250" value={formData.heightCm} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Weight (kg)</label>
            <input className={autofillClass("weightKg")} type="number" name="weightKg" min="2" max="300" value={formData.weightKg} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>BMI (calculated)</label>
            <input className={autofillClass("bmi")} type="number" name="bmi" value={formData.bmi} readOnly />
          </div>

          <div className="form-group">
            <label>Chest pain or discomfort</label>
            <select className={autofillClass("cp")} name="cp" value={formData.cp} onChange={handleChange}>
              {CP_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Blood pressure (top number)</label>
            <input className={autofillClass("trestbps")} type="number" name="trestbps" min="70" max="250" value={formData.trestbps} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Cholesterol level</label>
            <input className={autofillClass("chol")} type="number" name="chol" min="80" max="600" value={formData.chol} onChange={handleChange} />
          </div>

          <div className="form-group">
            <label>Blood sugar above 120</label>
            <select className={autofillClass("fbs")} name="fbs" value={formData.fbs} onChange={handleChange}>
              <option value={0}>No</option>
              <option value={1}>Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Diabetes</label>
            <select className={autofillClass("diabetes")} name="diabetes" value={formData.diabetes} onChange={handleChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Smoking</label>
            <select className={autofillClass("smoking")} name="smoking" value={formData.smoking} onChange={handleChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Alcohol Consumption</label>
            <select className={autofillClass("alcohol")} name="alcohol" value={formData.alcohol} onChange={handleChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Regular Exercise</label>
            <select className={autofillClass("exercise")} name="exercise" value={formData.exercise} onChange={handleChange}>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
          </div>

          <div className="form-group">
            <label>Family History</label>
            <select className={autofillClass("familyHistory")} name="familyHistory" value={formData.familyHistory} onChange={handleChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Healthy Diet</label>
            <select className={autofillClass("diet")} name="diet" value={formData.diet} onChange={handleChange}>
              <option value="Yes">Yes</option>
              <option value="No">No</option>
            </select>
          </div>

          <div className="form-group">
            <label>High Stress</label>
            <select className={autofillClass("stress")} name="stress" value={formData.stress} onChange={handleChange}>
              <option value="No">No</option>
              <option value="Yes">Yes</option>
            </select>
          </div>
        </div>

        <div className="action-row">
          <button type="submit" disabled={loading}>
            {loading ? "Predicting..." : "Predict Heart Disease"}
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
          <RiskDashboard disease="heart" result={result} formData={formData} />

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
            disease="heart"
            riskLevel={result.risk_level}
            inputData={formData}
          />
        </>
      )}
    </div>
  );
}

export default HeartForm;