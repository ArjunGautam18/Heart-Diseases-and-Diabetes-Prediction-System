/* ============================================================
   MediSense — Frontend Logic
   Connects the dashboard UI to the Flask API (127.0.0.1:5000)
   ============================================================ */

const API_BASE = "http://127.0.0.1:5000";

/* ---------- Toast notifications ---------- */
function ensureToastContainer() {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    return container;
}

function showToast(message, type = "info") {
    const container = ensureToastContainer();
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

/* ---------- API health check ---------- */
async function checkApiHealth() {
    const statusText = document.getElementById("apiStatusText");
    const dot = document.getElementById("apiDot");
    try {
        const res = await fetch(`${API_BASE}/health`);
        if (!res.ok) throw new Error("Bad response");
        if (statusText) statusText.textContent = "API Online";
        if (dot) { dot.classList.remove("offline"); dot.classList.add("online"); }
    } catch (err) {
        if (statusText) statusText.textContent = "API Offline";
        if (dot) { dot.classList.remove("online"); dot.classList.add("offline"); }
        console.error("API health check failed:", err);
    }
}

/* ---------- Helpers ---------- */
function getNum(id, fallback = 0) {
    const el = document.getElementById(id);
    if (!el) return fallback;
    const val = parseFloat(el.value);
    return isNaN(val) ? fallback : val;
}

function clearInvalidInputs() {
    document.querySelectorAll('.inp-invalid').forEach((el) => el.classList.remove('inp-invalid'));
}

function markInvalidInput(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add('inp-invalid');
}

function validateCriticalFields() {
    clearInvalidInputs();
    const invalid = [];
    const glu = getNum('d_glucose', 0);
    const bmi = getNum('d_bmi', 0);
    const bp  = getNum('d_bp', 0);
    if (glu === 0) invalid.push('d_glucose');
    if (bmi === 0) invalid.push('d_bmi');
    if (bp === 0) invalid.push('d_bp');
    if (invalid.length) {
        invalid.forEach(markInvalidInput);
        const first = document.getElementById(invalid[0]);
        if (first) first.focus();
    }
    return invalid;
}

function riskColor(level) {
    const l = (level || "").toLowerCase();
    if (l === "high") return "#e74c3c";
    if (l === "moderate") return "#f39c12";
    if (l === "low") return "#1d9e75";
    return "#8b9ab5"; // unknown
}

function riskLevelFromProbability(pct) {
    if (pct >= 50) return "High";
    if (pct >= 20) return "Moderate";
    return "Low";
}

/* ---------- Shared request helpers ---------- */
async function withButtonLoading(buttonId, loadingLabel, action) {
    const btn = document.getElementById(buttonId);
    const original = btn ? btn.innerHTML : "";
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<span class="loading-spinner"></span> ${loadingLabel}`;
    }
    try {
        return await action();
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = original;
        }
    }
}

async function postJson(endpoint, payload) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    let data;
    try {
        data = await res.json();
    } catch {
        data = { error: `Server returned status ${res.status} with no valid JSON` };
    }
    return { ok: res.ok, data };
}

/* ---------- Data collection ---------- */
function collectHeartData() {
    return {
        age:      getNum("f_age"),
        sex:      getNum("f_sex"),
        cp:       getNum("f_cp"),
        trestbps: getNum("f_trestbps"),
        chol:     getNum("f_chol"),
        fbs:      getNum("f_fbs"),
        restecg:  getNum("f_restecg"),
        thalach:  getNum("f_thalach"),
        exang:    getNum("f_exang"),
        oldpeak:  0,
        slope:    0,
        ca:       0,
        thal:     0,
    };
}

function collectDiabetesData() {
    return {
        Pregnancies:              getNum("d_preg"),
        Glucose:                  getNum("d_glucose"),
        BloodPressure:            getNum("d_bp"),
        SkinThickness:            getNum("d_skin"),     // now a real form field, no longer silently 0
        Insulin:                  getNum("d_insulin"),  // now a real form field, no longer silently 0
        BMI:                      getNum("d_bmi"),
        DiabetesPedigreeFunction: getNum("d_ped"),
        Age:                      getNum("d_age"),
    };
}

/* ---------- Response shape handling ---------- */
// Backend response shapes vary — normalize whatever comes back and fill in
// sensible client-side fallbacks so the UI never gets stuck on "Unknown"/"—".
function extractHealthScore(analysis, heart, diabetes) {
    const hs = analysis.health_score;
    let score = null, status = null;
    if (typeof hs === "number") score = hs;
    else if (hs && typeof hs === "object") {
        score = hs.score ?? hs.value ?? hs.total ?? null;
        status = hs.status ?? hs.label ?? hs.category ?? null;
    }
    if (score == null) {
        // Fallback: simple composite from both risk probabilities
        const hp = Number(heart.probability) || 0;
        const dp = Number(diabetes.probability) || 0;
        score = Math.round(Math.max(0, 100 - (hp * 0.5 + dp * 0.5)));
    }
    if (!status) {
        status = score >= 80 ? "Excellent" : score >= 60 ? "Good" : score >= 40 ? "Fair" : "Poor";
    }
    return { score, status };
}

function extractRiskAssessment(analysis, heart, diabetes) {
    const ra = analysis.risk_assessment;
    let level = null, factors = [];
    if (typeof ra === "string") level = ra;
    else if (ra && typeof ra === "object") {
        level = ra.level ?? ra.overall_risk ?? ra.risk_level ?? null;
        factors = ra.factors ?? ra.risk_factors ?? [];
    }
    if (!level) {
        // Fallback: derive overall risk from the worse of the two probabilities
        const hp = Number(heart.probability) || 0;
        const dp = Number(diabetes.probability) || 0;
        level = riskLevelFromProbability(Math.max(hp, dp));
    }
    return { level, factors };
}

/* ---------- Rendering ---------- */
function renderHealthScoreRing(scoreObj) {
    const score = Math.round(scoreObj.score ?? 0);
    const status = scoreObj.status ?? "Unknown";
    const color = status.toLowerCase().includes("excellent") ? "#1d9e75"
                : status.toLowerCase().includes("good") ? "#3498db"
                : status.toLowerCase().includes("fair") ? "#f39c12"
                : "#e74c3c";

    const radius = 62;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (Math.max(0, Math.min(100, score)) / 100) * circumference;

    const ringArc = document.getElementById("ringArc");
    if (ringArc) {
        ringArc.style.strokeDashoffset = `${offset}`;
        ringArc.style.stroke = color;
    }
    const ringNum = document.getElementById("ringNum");
    if (ringNum) ringNum.textContent = `${score}`;
    const ringLbl = document.getElementById("ringLbl");
    if (ringLbl) ringLbl.textContent = `${status}`;
}

function renderRiskGauge(riskObj) {
    const level = riskObj.level || "Unknown";
    const color = riskColor(level);
    const levelClass = level.toLowerCase().includes("high") ? "high"
                     : level.toLowerCase().includes("moderate") ? "moderate"
                     : "low";

    const pct = levelClass === "high" ? 0.85 : levelClass === "moderate" ? 0.5 : 0.15;
    const radius = 80;
    const circumference = Math.PI * radius;
    const offset = circumference - pct * circumference;

    const gaugeFill = document.getElementById("gaugeFill");
    const gaugeNeedle = document.getElementById("gaugeNeedle");
    const gaugeVal = document.getElementById("gaugeVal");

    if (gaugeFill) {
        gaugeFill.style.strokeDashoffset = `${offset}`;
        gaugeFill.style.stroke = color;
    }
    if (gaugeNeedle) {
        gaugeNeedle.style.transform = `rotate(${pct * 180 - 90}deg)`;
    }
    if (gaugeVal) {
        gaugeVal.textContent = `${level}`;
        gaugeVal.style.fill = color;
    }
}

function renderRecommendations(recommendations) {
    const el = document.getElementById("recArea");
    if (!el) return;

    if (!Array.isArray(recommendations) || recommendations.length === 0) {
        el.innerHTML = `<div class="empty-state"><span class="empty-icon">📋</span>No specific recommendations — keep up the good work!</div>`;
        return;
    }

    el.innerHTML = `<div class="rec-list">` + recommendations.map((rec) => {
        const text = typeof rec === "string" ? rec : (rec.text ?? rec.message ?? JSON.stringify(rec));
        const priority = (typeof rec === "object" && rec.priority) ? String(rec.priority).toLowerCase() : "medium";
        return `
            <div class="rec-item">
                <span class="rec-prio ${priority}">${priority}</span>
                <span class="rec-text">${text}</span>
            </div>
        `;
    }).join("") + `</div>`;
}

function renderVitals() {
    const bp = getNum("f_trestbps");
    const glu = getNum("d_glucose");
    const bmi = getNum("d_bmi");
    const chol = getNum("f_chol");

    const setVital = (valId, tagId, value, unit, okMax, warnMax) => {
        const valEl = document.getElementById(valId);
        const tagEl = document.getElementById(tagId);
        if (valEl) valEl.textContent = `${value}${unit}`;
        if (tagEl) {
            let cls = "vt-ok", label = "Normal";
            if (value > warnMax) { cls = "vt-high"; label = "High"; }
            else if (value > okMax) { cls = "vt-warn"; label = "Elevated"; }
            tagEl.className = `vital-tag ${cls}`;
            tagEl.textContent = label;
        }
    };

    setVital("v_bp", "v_bp_tag", bp, "", 120, 140);
    setVital("v_glu", "v_glu_tag", glu, "", 100, 126);
    setVital("v_bmi", "v_bmi_tag", bmi, "", 25, 30);
    setVital("v_chol", "v_chol_tag", chol, "", 200, 240);
}

function renderQuickStats(predictions, scoreObj, riskObj) {
    const heart = predictions.heart ?? {};
    const diabetes = predictions.diabetes ?? {};
    const score = scoreObj.score != null ? Math.round(scoreObj.score) : "—";

    const setText = (id, value, color) => {
        const el = document.getElementById(id);
        if (!el) return;
        el.textContent = value;
        if (color) el.style.color = color;
    };

    setText("hsVal", score, "#00c9a7");
    setText("hsSub", scoreObj.status ?? "Unknown", "#8b9ab5");
    setText("riskVal", riskObj.level ?? "Unknown", riskColor(riskObj.level));
    setText("riskSub", "Overall Assessment", "#8b9ab5");
    setText("heartVal", `${heart.probability ?? "—"}%`, riskColor(heart.risk_level));
    setText("heartSub", `${heart.risk_level ?? "Unknown"} Risk`, "#8b9ab5");
    setText("diabetesVal", `${diabetes.probability ?? "—"}%`, riskColor(diabetes.risk_level));
    setText("diabetesSub", `${diabetes.risk_level ?? "Unknown"} Risk`, "#8b9ab5");

    const badge = document.getElementById("riskBadge");
    if (badge) badge.textContent = riskObj.level ? `${riskObj.level} Risk` : "Pending";

    const predResults = document.getElementById("predResults");
    if (predResults) {
        predResults.innerHTML = `
            <div class="pred-card">
                <div class="pred-name">Heart Disease</div>
                <div class="pred-pct" style="color:${riskColor(heart.risk_level)}">${heart.probability != null ? `${heart.probability}%` : "—"}</div>
                <div class="pred-result">${heart.risk_level ?? "Unknown"} Risk</div>
            </div>
            <div class="pred-card">
                <div class="pred-name">Diabetes</div>
                <div class="pred-pct" style="color:${riskColor(diabetes.risk_level)}">${diabetes.probability != null ? `${diabetes.probability}%` : "—"}</div>
                <div class="pred-result">${diabetes.risk_level ?? "Unknown"} Risk</div>
            </div>
        `;
    }

    const updateFactor = (index, percent, color) => {
        const fill = document.getElementById(`rf${index}`);
        const pct = document.getElementById(`rf${index}v`);
        const normalized = Math.max(0, Math.min(100, Number(percent) || 0));
        if (fill) {
            fill.style.width = `${normalized}%`;
            fill.style.background = color;
        }
        if (pct) pct.textContent = `${Math.round(normalized)}%`;
    };

    if (Array.isArray(riskObj.factors) && riskObj.factors.length > 0) {
        riskObj.factors.slice(0, 4).forEach((factor, idx) => {
            const value = Number(factor.value ?? factor.impact ?? 0);
            const level = factor.level ?? factor.risk_level ?? factor.name ?? "";
            updateFactor(idx + 1, value, riskColor(level));
        });
    } else {
        updateFactor(1, heart.probability ?? 0, riskColor(heart.risk_level));
        updateFactor(2, diabetes.probability ?? 0, riskColor(diabetes.risk_level));
        updateFactor(3, Math.min(100, (getNum("f_age") / 80) * 100), "#4f90f7");
        updateFactor(4, Math.min(100, getNum("d_bmi") * 2.2), "#9b87f5");
    }

    renderVitals();
}

/* ---------- Full Analysis ---------- */
async function runFullAnalysis() {
    if (validateCriticalFields().length) {
        showToast("Glucose, BMI and Blood Pressure must be non-zero before analysis.", "error");
        return;
    }

    const payload = {
        heart: collectHeartData(),
        diabetes: collectDiabetesData(),
        patient_info: {
            age: getNum("f_age"),
            bmi: getNum("d_bmi"),
            glucose: getNum("d_glucose"),
            bp: getNum("f_trestbps"),
        },
    };

    await withButtonLoading("runFullAnalysis", "Analyzing...", async () => {
        try {
            const { ok, data } = await postJson("/predict/full", payload);
            if (!ok) {
                showToast(data.error || "Analysis failed", "error");
                return;
            }

            const predictions = data.predictions ?? {};
            const heart = predictions.heart ?? {};
            const diabetes = predictions.diabetes ?? {};

            const scoreObj = extractHealthScore(data, heart, diabetes);
            const riskObj = extractRiskAssessment(data, heart, diabetes);

            renderQuickStats(predictions, scoreObj, riskObj);
            renderHealthScoreRing(scoreObj);
            renderRiskGauge(riskObj);
            renderRecommendations(data.recommendations);

            showToast("Analysis complete", "success");
        } catch (err) {
            console.error(err);
            showToast("Could not reach the API. Is the backend running on port 5000?", "error");
        }
    });
}

/* ---------- Demo scenarios ---------- */
function runDemo(scenario) {
    if (scenario === 'low') {
        document.getElementById("f_age").value = 35;
        document.getElementById("f_sex").value = 1;
        document.getElementById("f_cp").value = 0;
        document.getElementById("f_trestbps").value = 120;
        document.getElementById("f_chol").value = 200;
        document.getElementById("f_fbs").value = 0;
        document.getElementById("f_restecg").value = 0;
        document.getElementById("f_thalach").value = 160;
        document.getElementById("f_exang").value = 0;

        document.getElementById("d_preg").value = 1;
        document.getElementById("d_glucose").value = 95;
        document.getElementById("d_bp").value = 70;
        document.getElementById("d_skin").value = 18;
        document.getElementById("d_insulin").value = 60;
        document.getElementById("d_bmi").value = 22;
        document.getElementById("d_age").value = 35;
        document.getElementById("d_ped").value = 0.25;
    } else if (scenario === 'high') {
        document.getElementById("f_age").value = 65;
        document.getElementById("f_sex").value = 1;
        document.getElementById("f_cp").value = 3;
        document.getElementById("f_trestbps").value = 160;
        document.getElementById("f_chol").value = 280;
        document.getElementById("f_fbs").value = 1;
        document.getElementById("f_restecg").value = 2;
        document.getElementById("f_thalach").value = 110;
        document.getElementById("f_exang").value = 1;

        document.getElementById("d_preg").value = 3;
        document.getElementById("d_glucose").value = 180;
        document.getElementById("d_bp").value = 95;
        document.getElementById("d_skin").value = 35;
        document.getElementById("d_insulin").value = 210;
        document.getElementById("d_bmi").value = 35;
        document.getElementById("d_age").value = 65;
        document.getElementById("d_ped").value = 1.2;
    }

    setTimeout(() => runFullAnalysis(), 100);
}

/* ---------- Init ---------- */
document.addEventListener("DOMContentLoaded", () => {
    checkApiHealth();
    setInterval(checkApiHealth, 15000);
    document.getElementById("runFullAnalysis")?.addEventListener("click", runFullAnalysis);
});