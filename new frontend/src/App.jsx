import { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import Navbar from "./components/Navbar";
import HeartForm from "./components/HeartForm";
import DiabetesForm from "./components/DiabetesForm";
import "./index.css";
import { API_BASE } from "./utils/api";

function getApiError(result, fallback = "Authentication failed.") {
  if (typeof result?.detail === "string") return result.detail;
  if (Array.isArray(result?.detail)) {
    return result.detail
      .map((item) => item?.msg)
      .filter(Boolean)
      .join(" ");
  }
  return fallback;
}

function Home() {
  return (
    <div className="home-shell">
      <section className="hero-panel">
        <div className="eyebrow">AI health screening</div>
        <h2>Welcome to Medicare</h2>
        <p>
          Use the prediction tools below to quickly assess risk for heart disease and
          diabetes with a fast, guided screening workflow.
        </p>

        <div className="hero-actions">
          <span className="status-pill status-pill--success">Heart prediction</span>
          <span className="status-pill">Diabetes prediction</span>
        </div>
      </section>

      <div className="insight-grid">
        <div className="mini-card">
          <span className="mini-icon">❤️</span>
          <h3>Heart Disease Prediction</h3>
          <p>Evaluate cardiac risk using key patient health indicators.</p>
        </div>
        <div className="mini-card">
          <span className="mini-icon">🩺</span>
          <h3>Diabetes Prediction</h3>
          <p>Assess diabetes risk with a practical screening-based model.</p>
        </div>
      </div>

      <div className="disclaimer-box">
        <div className="disclaimer-header">
          <span className="warning-icon">⚠</span>
          <strong>Medical Disclaimer</strong>
        </div>
        <p>
          This tool is designed for educational and preliminary screening support only. It
          does not diagnose disease, replace a licensed clinician’s evaluation, or provide
          medical treatment advice. Always consult a qualified healthcare professional for
          diagnosis, treatment decisions, or urgent concerns.
        </p>
      </div>
    </div>
  );
}

function ProtectedRoute({ user, authLoading, children }) {
  const navigate = useNavigate();

  useEffect(() => {
    if (!authLoading && !user) navigate("/login", { replace: true });
  }, [authLoading, user, navigate]);

  if (authLoading) return <div className="page-loading">Checking your session...</div>;
  return user ? children : null;
}

function AuthPage({ onLogin }) {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    setError("");
    setSuccess("");
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const email = formData.email.trim().toLowerCase();

    if (!email) {
      setError("Please enter your email.");
      return;
    }

    if (mode === "reset") {
      setError("Password reset is not enabled until an email delivery provider is configured.");
      return;
    }
    if (mode === "register" && !formData.name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!formData.password) {
      setError("Please enter your password.");
      return;
    }
    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (mode === "register" && formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    try {
      const response = await fetch(`${API_BASE}/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          ...(mode === "register" ? { name: formData.name } : {}),
          email,
          password: formData.password,
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(getApiError(result));
      if (mode === "register") {
        setSuccess("Account created successfully. You can now login.");
        setMode("login");
        return;
      }
      onLogin(result);
      navigate("/");
    } catch (requestError) {
      setError(requestError.message);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-header">
          <p className="auth-kicker">Care access</p>
          <h2>{mode === "login" ? "Login" : mode === "register" ? "Create account" : "Reset password"}</h2>
        </div>

        <div className="auth-tabs">
          <button className={mode === "login" ? "auth-tab active" : "auth-tab"} onClick={() => setMode("login")} type="button">
            Login
          </button>
          <button className={mode === "register" ? "auth-tab active" : "auth-tab"} onClick={() => setMode("register")} type="button">
            Register
          </button>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {mode === "register" && (
            <div className="field-group">
              <label>Full name</label>
              <input
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) => handleChange("name", e.target.value)}
              />
            </div>
          )}

          <div className="field-group">
            <label>Email</label>
            <input
              type="email"
              placeholder="name@example.com"
              value={formData.email}
              onChange={(e) => handleChange("email", e.target.value)}
            />
          </div>

          {mode !== "reset" && (
            <div className="field-group">
              <label>Password</label>
              <div className="password-wrap">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder={mode === "login" ? "Enter your password" : "Create a password"}
                  value={formData.password}
                  onChange={(e) => handleChange("password", e.target.value)}
                />
                <button type="button" className="inline-toggle" onClick={() => setShowPassword((prev) => !prev)}>
                  {showPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
          )}

          {(mode === "register" || mode === "reset") && (
            <div className="field-group">
              <label>{mode === "register" ? "Confirm password" : "New password"}</label>
              <div className="password-wrap">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder={mode === "register" ? "Confirm your password" : "Enter a new password"}
                  value={formData.confirmPassword}
                  onChange={(e) => handleChange("confirmPassword", e.target.value)}
                />
                <button type="button" className="inline-toggle" onClick={() => setShowConfirmPassword((prev) => !prev)}>
                  {showConfirmPassword ? "Hide" : "Show"}
                </button>
              </div>
            </div>
          )}

          {error && <div className="auth-message error">{error}</div>}
          {success && <div className="auth-message success">{success}</div>}

          <button type="submit" className="auth-submit">
            {mode === "login" ? "Login" : mode === "register" ? "Create account" : "Reset password"}
          </button>
        </form>

        <p className="auth-provider-note">Secure email sign-in</p>
      </div>
    </div>
  );
}

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("medicare-theme") || "light");
  const [authUser, setAuthUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/auth/me`, { credentials: "include" })
      .then((response) => response.ok ? response.json() : null)
      .then((user) => setAuthUser(user))
      .catch(() => setAuthUser(null))
      .finally(() => setAuthLoading(false));
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("medicare-theme", theme);
  }, [theme]);

  return (
    <BrowserRouter>
      <div className="app-shell" data-theme={theme}>
        <Navbar theme={theme} setTheme={setTheme} user={authUser} onLogout={async () => {
          await fetch(`${API_BASE}/auth/logout`, { method: "POST", credentials: "include" });
          setAuthUser(null);
        }} />
        <div className="container">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/heart" element={<ProtectedRoute user={authUser} authLoading={authLoading}><HeartForm /></ProtectedRoute>} />
            <Route path="/diabetes" element={<ProtectedRoute user={authUser} authLoading={authLoading}><DiabetesForm /></ProtectedRoute>} />
            <Route path="/login" element={<AuthPage onLogin={setAuthUser} />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;