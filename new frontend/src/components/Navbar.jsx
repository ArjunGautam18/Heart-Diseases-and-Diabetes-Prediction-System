import { Link } from "react-router-dom";

function Navbar({ theme, setTheme, user, onLogout }) {
  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <nav className="navbar">
      <h1>🏥 Medicare</h1>
      <div className="nav-links">
        <Link to="/">Home</Link>
        <Link to="/heart">Heart Disease</Link>
        <Link to="/diabetes">Diabetes</Link>
        <button type="button" className="theme-toggle" onClick={toggleTheme}>
          {theme === "light" ? "🌙 Dark" : "☀️ Light"}
        </button>

        {user ? (
          <>
            <span className="user-badge">Hi, {user.name.split(" ")[0]}</span>
            <button type="button" className="logout-btn" onClick={onLogout}>
              <span className="logout-icon">⎋</span>
              Logout
            </button>
          </>
        ) : (
          <Link to="/login" className="login-btn">Login</Link>
        )}
      </div>
    </nav>
  );
}

export default Navbar;