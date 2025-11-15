// screens/SettingsScreen.tsx
import React, { useState } from "react";

const SettingsScreen: React.FC = () => {
  const [csvText, setCsvText] = useState("");

  const handleConnect = async (provider: "google" | "fiverr" | "upwork") => {
    console.log(`Connect ${provider} clicked`);

    if (provider !== "google") {
      alert(`${provider} integration coming soon`);
      return;
    }

    try {
      setCsvText("Running Gmail flow...");

      // 1. Trigger Gmail email reading
      console.log("🚨 Running Gmail Endpoint...");
      const gmailRes = await fetch("http://localhost:8000/run-google-mail", {
        method: "POST",
      });

      console.log("🚨 AFTER GMAIL, status:", gmailRes.status);

      if (!gmailRes.ok) {
        setCsvText("Failed to run Gmail flow.");
        return;
      }

      // 2. Fetch Uber earnings CSV from backend
      console.log("🚨 Fetching CSV...");
      const response = await fetch("http://localhost:8000/uber-earnings");

      console.log("🚨 CSV RESPONSE STATUS:", response.status);

      if (!response.ok) {
        setCsvText("Failed to fetch earnings file.");
        return;
      }

      const text = await response.text();
      console.log("🚨 CSV TEXT:", text);
      setCsvText(text);
    } catch (err: any) {
      console.error("ERROR IN Google Connect:", err);
      setCsvText("ERROR: " + String(err));
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Settings</h1>
      <p style={{ color: "#9ca3af", marginBottom: 24 }}>
        Connect your accounts to power the demo.
      </p>

      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 12,
          maxWidth: 320,
        }}
      >
        {/* GOOGLE CONNECT BUTTON */}
        <button style={buttonStyle} onClick={() => handleConnect("google")}>
          Connect Google Account
        </button>

        <button style={buttonStyle} onClick={() => handleConnect("fiverr")}>
          Connect Fiverr
        </button>

        <button style={buttonStyle} onClick={() => handleConnect("upwork")}>
          Connect Upwork
        </button>
      </div>

      {/* SHOW CSV OUTPUT */}
      <pre
        style={{
          whiteSpace: "pre-wrap",
          marginTop: 30,
          background: "#111",
          color: "#00ff99",
          padding: 16,
          borderRadius: 8,
        }}
      >
        {csvText}
      </pre>
    </div>
  );
};

const buttonStyle: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 999,
  border: "none",
  fontSize: 14,
  fontWeight: 500,
  cursor: "pointer",
  background: "linear-gradient(135deg, #22c55e, #16a34a)",
  color: "#f9fafb",
  textAlign: "left",
};

export default SettingsScreen;
