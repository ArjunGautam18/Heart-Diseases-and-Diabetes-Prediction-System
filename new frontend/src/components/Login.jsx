import React, { useState } from 'react';

export default function Login({ onLogin }) {
  const [page, setPage] = useState('login');

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // =========================
  // CREATE ACCOUNT
  // =========================
  const handleCreateAccount = (e) => {
    e.preventDefault();

    setError('');
    setSuccess('');

    if (!name || !email || !password || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password must contain at least 6 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    const gmail = email.trim().toLowerCase();

    // Check if account already exists
    const existingAccount = localStorage.getItem(
      `heartcare_${gmail}`
    );

    if (existingAccount) {
      setError(
        'An account with this Gmail already exists. Please login.'
      );
      return;
    }

    // Create account
    const account = {
      name: name.trim(),
      email: gmail,
      password: password,
    };

    localStorage.setItem(
      `heartcare_${gmail}`,
      JSON.stringify(account)
    );

    setSuccess(
      'Account created successfully! Please login with your Gmail and password.'
    );

    // Clear fields
    setName('');
    setPassword('');
    setConfirmPassword('');

    // Move to login
    setTimeout(() => {
      setPage('login');
      setEmail(gmail);
      setSuccess('');
    }, 1500);
  };

  // =========================
  // LOGIN
  // =========================
  const handleLogin = (e) => {
    e.preventDefault();

    setError('');
    setSuccess('');

    if (!email || !password) {
      setError('Please enter your Gmail and password.');
      return;
    }

    const gmail = email.trim().toLowerCase();

    // Find account
    const storedAccount = localStorage.getItem(
      `heartcare_${gmail}`
    );

    // Account doesn't exist
    if (!storedAccount) {
      setError(
        'Account not found. Please create an account first.'
      );
      return;
    }

    const account = JSON.parse(storedAccount);

    // Check password
    if (account.password !== password) {
      setError('Incorrect password. Please try again.');
      return;
    }

    // Login successful
    onLogin({
      email: account.email,
      name: account.name,
      loginTime: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    });
  };

  // =========================
  // CREATE ACCOUNT PAGE
  // =========================
  if (page === 'register') {
    return (
      <div className="login-wrapper">
        <div className="login-card">

          <div className="login-brand">
            <div className="brand-icon">❤️</div>

            <h1 className="login-title">
             Medicare ❤️
            </h1>
          </div>

          <p className="card-subtitle">
            Create your account
          </p>

          <form onSubmit={handleCreateAccount}>

            {/* Name */}
            <div className="form-group">
              <label className="form-label">
                Full Name
              </label>

              <input
                type="text"
                className="input-field"
                placeholder="Enter your full name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>

            {/* Gmail */}
            <div className="form-group">
              <label className="form-label">
                Gmail Address
              </label>

              <input
                type="email"
                className="input-field"
                placeholder="example@gmail.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />

              <p className="input-help">
                This Gmail will be used to login to Medicare .
              </p>
            </div>

            {/* Password */}
            <div className="form-group">
              <label className="form-label">
                Password
              </label>

              <div className="password-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input-field password-input"
                  placeholder="Create a password"
                  value={password}
                  onChange={(e) =>
                    setPassword(e.target.value)
                  }
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {/* Confirm Password */}
            <div className="form-group">
              <label className="form-label">
                Confirm Password
              </label>

              <div className="password-wrapper">
                <input
                  type={
                    showConfirmPassword
                      ? 'text'
                      : 'password'
                  }
                  className="input-field password-input"
                  placeholder="Confirm your password"
                  value={confirmPassword}
                  onChange={(e) =>
                    setConfirmPassword(e.target.value)
                  }
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() =>
                    setShowConfirmPassword(
                      !showConfirmPassword
                    )
                  }
                >
                  {showConfirmPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {error && (
              <div className="error-message">
                {error}
              </div>
            )}

            {success && (
              <div className="success-message">
                {success}
              </div>
            )}

            <button
              type="submit"
              className="login-btn"
            >
              Create Account
            </button>
          </form>

          <div className="account-switch">
            <span>Already have an account?</span>

            <button
              type="button"
              className="switch-btn"
              onClick={() => {
                setPage('login');
                setError('');
                setSuccess('');
              }}
            >
              Login
            </button>
          </div>

          <div className="divider">
            <span>Secure Access</span>
          </div>

          <div className="security-message">
             Your account information is protected.
          </div>

        </div>
      </div>
    );
  }

  // =========================
  // LOGIN PAGE
  // =========================
  return (
    <div className="login-wrapper">
      <div className="login-card">

        <div className="login-brand">
          <div className="brand-icon"></div>

          <h1 className="login-title">
              MediCare ❤️‍🩹
          </h1>
        </div>

        <p className="card-subtitle">
          Heart Disease & Diabetes
          <br />
          prediction system using AI/ML Techniques.
        </p>

        <form onSubmit={handleLogin}>

          {/* Gmail */}
          <div className="form-group">
            <label className="form-label">
              Gmail Address
            </label>

            <input
              type="email"
              className="input-field"
              placeholder="example@gmail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>

          {/* Password */}
          <div className="form-group">
            <label className="form-label">
              Password
            </label>

            <div className="password-wrapper">
              <input
                type={showPassword ? 'text' : 'password'}
                className="input-field password-input"
                placeholder="Enter your password"
                value={password}
                onChange={(e) =>
                  setPassword(e.target.value)
                }
                autoComplete="current-password"
                required
              />

              <button
                type="button"
                className="password-toggle"
                onClick={() =>
                  setShowPassword(!showPassword)
                }
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
          </div>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
          >
            Login
          </button>

        </form>

        {/* Create Account */}
        <div className="account-switch">
          <span>Don't have an account?</span>

          <button
            type="button"
            className="switch-btn"
            onClick={() => {
              setPage('register');
              setError('');
              setSuccess('');
            }}
          >
            Create Account
          </button>
        </div>

        <div className="divider">
          <span>Prediction system</span>
        </div>

        <div className="security-message">
         This is only for disease prediction but medical professionals can not be replaced by it.
        </div>

      </div>
    </div>
  );
}