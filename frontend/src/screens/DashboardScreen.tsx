// screens/DashboardScreen.tsx
import React from "react";

const DashboardScreen: React.FC = () => {
  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Dashboard</h1>
      <p style={{ color: "#9ca3af", marginBottom: 24 }}>
        Quick overview of your hackathon bank app.
      </p>

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
