import React, { useState } from "react";
import { useWallet } from "../contexts/WalletContext";

// Google connect hook with localStorage persistence
const useGoogleConnect = () => {
  const [googleConnected, setGoogleConnected] = useState<boolean>(() => {
    return localStorage.getItem("googleConnected") === "true";
  });

  const [googleStatus, setGoogleStatus] = useState<string>("");

  const handleGoogleConnect = async () => {
    try {
      setGoogleStatus("Running Gmail flow...");

      const gmailRes = await fetch("http://localhost:8000/run-google-mail", {
        method: "POST",
      });

      if (!gmailRes.ok) {
        setGoogleStatus("Failed to run Gmail flow.");
        return;
      }

      const csvRes = await fetch("http://localhost:8000/uber-earnings");
      if (!csvRes.ok) {
        setGoogleStatus("Failed to fetch earnings file.");
        return;
      }

      const csvText = await csvRes.text();
      setGoogleStatus(csvText);

      // 🔥 Permanently hide button
      setGoogleConnected(true);
      localStorage.setItem("googleConnected", "true");
    } catch (err: any) {
      setGoogleStatus("ERROR: " + String(err));
    }
  };

  return { googleStatus, googleConnected, handleGoogleConnect };
};

const DashboardScreen: React.FC = () => {
  const {
    walletAddress,
    balance,
    isConnecting,
    isFetchingBalance,
    connectWallet,
    disconnectWallet,
    refreshBalance,
  } = useWallet();

  const { googleStatus, googleConnected, handleGoogleConnect } =
    useGoogleConnect();

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ fontSize: 24, marginBottom: 8 }}>Dashboard</h1>
          <p style={{ color: "#9ca3af", margin: 0 }}>
            Quick overview of your hackathon bank app.
          </p>
        </div>

        {/* RIGHT SIDE BUTTON GROUP */}
        <div style={{ display: "flex", gap: 12, textAlign: "right" }}>
          {/* GOOGLE CONNECT — permanently hidden after first press */}
          {!googleConnected && (
            <button
              onClick={handleGoogleConnect}
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                border: "none",
                fontSize: 14,
                fontWeight: 600,
                background: "linear-gradient(135deg, #22c55e, #16a34a)",
                color: "#f9fafb",
                cursor: "pointer",
              }}
            >
              📧 Connect Google
            </button>
          )}

          {/* WALLET BUTTONS */}
          {!walletAddress ? (
            <button
              onClick={connectWallet}
              disabled={isConnecting}
              style={{
                padding: "10px 20px",
                fontSize: 14,
                fontWeight: 600,
                background:
                  "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(79,70,229,0.95))",
                color: "white",
                border: "none",
                borderRadius: 8,
                cursor: isConnecting ? "not-allowed" : "pointer",
                opacity: isConnecting ? 0.6 : 1,
              }}
            >
              {isConnecting ? "Connecting..." : "🦊 Connect Wallet"}
            </button>
          ) : (
            <div
              style={{
                backgroundColor: "#020617",
                border: "1px solid rgba(34, 197, 94, 0.5)",
                borderRadius: 12,
                padding: "12px 16px",
                minWidth: 220,
              }}
            >
              <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 4 }}>
                Connected to Arc Testnet
              </div>
              <div
                style={{
                  fontSize: 13,
                  color: "#22c55e",
                  fontWeight: 600,
                  marginBottom: 8,
                }}
              >
                {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
              </div>
              <div
                style={{
                  borderTop: "1px solid rgba(148,163,184,0.2)",
                  paddingTop: 8,
                  marginBottom: 8,
                }}
              >
                <div
                  style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}
                >
                  Balance
                </div>
                <div
                  style={{ fontSize: 18, fontWeight: 700, color: "#22c55e" }}
                >
                  {isFetchingBalance ? "Loading..." : `${balance} USDC`}
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={refreshBalance}
                  disabled={isFetchingBalance}
                  style={{
                    flex: 1,
                    padding: "6px 10px",
                    fontSize: 11,
                    backgroundColor: "rgba(59,130,246,0.2)",
                    color: "#60a5fa",
                    border: "1px solid rgba(59,130,246,0.3)",
                    borderRadius: 6,
                    cursor: isFetchingBalance ? "not-allowed" : "pointer",
                    opacity: isFetchingBalance ? 0.6 : 1,
                  }}
                >
                  🔄 Refresh
                </button>
                <button
                  onClick={disconnectWallet}
                  style={{
                    flex: 1,
                    padding: "6px 10px",
                    fontSize: 11,
                    backgroundColor: "rgba(239, 68, 68, 0.2)",
                    color: "#f87171",
                    border: "1px solid rgba(239, 68, 68, 0.3)",
                    borderRadius: 6,
                    cursor: "pointer",
                  }}
                >
                  Disconnect
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 16,
        }}
      >
        <div style={cardStyle}>
          <div style={cardTitle}>Total Balance</div>
          <div style={cardBig}>£12,340.50</div>
        </div>
        <div style={cardStyle}>
          <div style={cardTitle}>Active Loans</div>
          <div style={cardBig}>3</div>
        </div>
        <div style={cardStyle}>
          <div style={cardTitle}>Next Payment</div>
          <div style={cardBig}>£420.00</div>
        </div>
      </div>

      {/* Google debug output */}
      {googleStatus && (
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
          {googleStatus}
        </pre>
      )}
    </div>
  );
};

const cardStyle: React.CSSProperties = {
  backgroundColor: "#020617",
  borderRadius: 16,
  padding: 16,
  border: "1px solid rgba(148,163,184,0.3)",
};

const cardTitle: React.CSSProperties = {
  fontSize: 13,
  color: "#9ca3af",
  marginBottom: 6,
};

const cardBig: React.CSSProperties = {
  fontSize: 20,
  fontWeight: 600,
};

export default DashboardScreen;
