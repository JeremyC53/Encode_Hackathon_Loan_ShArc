// components/LoginScreen.tsx
import React, { useState } from "react";
import type { User } from "../types";

const DEMO_USER = {
  email: "demo@hack.com",
  password: "hackathon",
} as const;

type LoginScreenProps = {
  onLogin: (user: User) => void;
};

const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin }) => {
  const [email, setEmail] = useState<string>(DEMO_USER.email);
  const [password, setPassword] = useState<string>(DEMO_USER.password);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    setTimeout(() => {
      if (email === DEMO_USER.email && password === DEMO_USER.password) {
        onLogin({ email });
      } else {
        setError("Invalid demo credentials. Try demo@hack.com / hackathon");
      }
      setLoading(false);
    }, 700);
  };

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>Hackathon Demo Login</h1>
        <p style={styles.subtitle}>
          Use <b>demo@hack.com</b> / <b>hackathon</b>
        </p>

        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.label}>
            Email
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={styles.input}
              placeholder="demo@hack.com"
              required
            />
          </label>

          <label style={styles.label}>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={styles.input}
              placeholder="hackathon"
              required
            />
          </label>

          {error && <div style={styles.error}>{error}</div>}

          <button type="submit" style={styles.button} disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  page: {
    position: "fixed",
    inset: 0,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background:
      "radial-gradient(circle at top left, #e0f2fe, #eff6ff 40%, #f9fafb)",
    boxSizing: "border-box",
  },
  card: {
    width: "100%",
    maxWidth: "400px",
    background: "white",
    borderRadius: "16px",
    padding: "24px 28px",
    boxShadow: "0 18px 35px rgba(15, 23, 42, 0.12)",
    boxSizing: "border-box",
  },
  title: {
    margin: 0,
    marginBottom: "4px",
    fontSize: "24px",
    fontWeight: 700,
    color: "#0f172a",
  },
  subtitle: {
    margin: 0,
    marginBottom: "20px",
    fontSize: "14px",
    color: "#64748b",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "12px",
  },
  label: {
    fontSize: "13px",
    color: "#0f172a",
    display: "flex",
    flexDirection: "column",
    gap: "4px",
  },
  input: {
    padding: "8px 10px",
    borderRadius: "8px",
    border: "1px solid #cbd5f5",
    fontSize: "14px",
    outline: "none",
    boxSizing: "border-box",
    backgroundColor: "#ffffff",
    color: "#0f172a",
  },
  button: {
    marginTop: "8px",
    padding: "10px 12px",
    borderRadius: "999px",
    border: "none",
    fontSize: "14px",
    fontWeight: 600,
    cursor: "pointer",
    background: "linear-gradient(135deg, #2563eb, #4f46e5)",
    color: "white",
  },
  error: {
    fontSize: "12px",
    color: "#b91c1c",
    background: "#fee2e2",
    borderRadius: "8px",
    padding: "6px 8px",
  },
};

export default LoginScreen;
