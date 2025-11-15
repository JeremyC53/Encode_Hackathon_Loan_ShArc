// components/LoginScreen.tsx
import React, { useEffect, useRef, useState } from "react";
import { W3SSdk } from "@circle-fin/w3s-pw-web-sdk";
import type { User } from "../types";

const DEMO_USER = {
  email: "demo@hack.com",
  password: "hackathon",
} as const;

type LoginScreenProps = {
  onLogin: (user: User) => void;
};

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const CIRCLE_APP_ID = import.meta.env.VITE_CIRCLE_APP_ID;

const LoginScreen: React.FC<LoginScreenProps> = ({ onLogin }) => {
  const [email, setEmail] = useState<string>(DEMO_USER.email);
  const [password, setPassword] = useState<string>(DEMO_USER.password);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [circleSdkReady, setCircleSdkReady] = useState(false);
  const [circleNotice, setCircleNotice] = useState<string | null>(null);
  const [walletLoading, setWalletLoading] = useState(false);

  const circleClientRef = useRef<W3SSdk | null>(null);
  const lastTokenRef = useRef<{ token: string; encryptionKey?: string }>({
    token: "",
  });

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

  useEffect(() => {
    if (!CIRCLE_APP_ID) {
      setCircleNotice("Circle client not configured. Add VITE_CIRCLE_APP_ID.");
      return;
    }
    try {
      const sdk = new W3SSdk();
      sdk.setAppSettings({ appId: CIRCLE_APP_ID });
      sdk.setOnForgotPin(async () => {
        if (!lastTokenRef.current.token) return;
        try {
          const response = await fetch(`${API_BASE_URL}/api/auth/pin/restore`, {
            method: "POST",
            headers: {
              "X-User-Token": lastTokenRef.current.token,
            },
          });
          if (!response.ok) return;
          const data = (await response.json()) as { challenge_id: string };
          if (data.challenge_id) {
            sdk.execute(data.challenge_id);
          }
        } catch (restoreError) {
          console.error(restoreError);
        }
      });
      circleClientRef.current = sdk;
      setCircleSdkReady(true);
      setCircleNotice(null);
    } catch (err) {
      console.error(err);
      setCircleNotice("Failed to initialize Circle SDK");
    }
  }, []);

  const handleCircleAuth = async (mode: "signin" | "signup") => {
    setError("");
    setWalletLoading(true);
    try {
      if (!circleSdkReady || !circleClientRef.current) {
        throw new Error("Circle wallet client is not ready");
      }

      const response = await fetch(`${API_BASE_URL}/api/auth/${mode}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const detail = await response.json().catch(() => ({}));
        const message =
          typeof detail?.detail === "string"
            ? detail.detail
            : "Unable to reach wallet service";
        throw new Error(message);
      }

      const data = await response.json();
      const sdk = circleClientRef.current;
      lastTokenRef.current = {
        token: data.user_token,
        encryptionKey: data.encryption_key,
      };
      sdk.setAuthentication({
        userToken: data.user_token,
        encryptionKey: data.encryption_key,
      });

      const syncWalletMetadata = async () => {
        try {
          const syncResponse = await fetch(`${API_BASE_URL}/api/wallets/sync`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              circle_user_id: data.circle_user_id,
              user_token: data.user_token,
            }),
          });
          if (!syncResponse.ok) {
            return null;
          }
          return (await syncResponse.json()) as {
            wallet_address?: string;
          };
        } catch (syncError) {
          console.warn("Failed to sync wallet metadata", syncError);
          return null;
        }
      };

      const finalizeLogin = async () => {
        let walletAddress: string | undefined = data.wallet_address ?? undefined;
        if (!walletAddress) {
          const synced = await syncWalletMetadata();
          if (synced?.wallet_address) {
            walletAddress = synced.wallet_address;
          }
        }
        onLogin({ email, walletAddress });
      };

      if (data.challenge_id) {
        sdk.execute(data.challenge_id, (sdkError) => {
          if (sdkError) {
            setError("Circle verification was cancelled or failed.");
            return;
          }
          finalizeLogin().catch((finalizeError) => {
            console.error(finalizeError);
            setError("Unable to complete wallet login");
          });
        });
      } else {
        await finalizeLogin();
      }
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : "Wallet action failed");
    } finally {
      setWalletLoading(false);
    }
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

        <div style={styles.divider}>or</div>

        {circleNotice && <div style={styles.notice}>{circleNotice}</div>}

        <div style={styles.circleActions}>
          <button
            type="button"
            style={styles.circleButton}
            onClick={() => handleCircleAuth("signin")}
            disabled={walletLoading || !circleSdkReady}
          >
            {walletLoading ? "Signing in..." : "Circle Wallet Sign In"}
          </button>
          <button
            type="button"
            style={styles.secondaryLink}
            onClick={() => handleCircleAuth("signup")}
            disabled={walletLoading || !circleSdkReady}
          >
            Create Circle Wallet
          </button>
        </div>
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
  notice: {
    fontSize: "12px",
    color: "#0f172a",
    background: "#e0e7ff",
    borderRadius: "8px",
    padding: "6px 8px",
    marginBottom: "8px",
  },
  divider: {
    margin: "16px 0 10px",
    textAlign: "center",
    color: "#94a3b8",
    fontSize: "12px",
    textTransform: "uppercase" as const,
    letterSpacing: "0.15em",
  },
  circleActions: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  circleButton: {
    width: "100%",
    padding: "10px 12px",
    borderRadius: "10px",
    border: "1px solid #cbd5f5",
    fontSize: "14px",
    fontWeight: 600,
    cursor: "pointer",
    background: "#fff",
    color: "#0f172a",
  },
  secondaryLink: {
    width: "100%",
    padding: "8px 10px",
    borderRadius: "10px",
    border: "1px dashed #94a3b8",
    fontSize: "13px",
    fontWeight: 600,
    cursor: "pointer",
    background: "transparent",
    color: "#2563eb",
  },
};

export default LoginScreen;

