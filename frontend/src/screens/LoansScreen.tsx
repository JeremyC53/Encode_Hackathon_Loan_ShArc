// screens/LoansScreen.tsx
import React from "react";

const LoansScreen: React.FC = () => {
  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Loans</h1>
      <p style={{ color: "#9ca3af", marginBottom: 24 }}>
        List of demo loans (static for now).
      </p>

      <table
        style={{
          width: "100%",
          borderCollapse: "collapse",
          backgroundColor: "#020617",
          borderRadius: 16,
          overflow: "hidden",
        }}
      >
        <thead>
          <tr style={{ backgroundColor: "#020617" }}>
            <th style={thStyle}>Loan</th>
            <th style={thStyle}>Amount</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Next Payment</th>
          </tr>
        </thead>
        <tbody>
          {[
            ["Freelancer Gear", "£3,500", "Active", "1 Apr"],
            ["Laptop Upgrade", "£1,200", "Active", "15 Mar"],
            ["Travel Float", "£800", "Paid off", "-"],
          ].map(([name, amount, status, next], idx) => (
            <tr
              key={name}
              style={{
                backgroundColor: idx % 2 === 0 ? "#020617" : "#020617",
              }}
            >
              <td style={tdStyle}>{name}</td>
              <td style={tdStyle}>{amount}</td>
              <td style={tdStyle}>{status}</td>
              <td style={tdStyle}>{next}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const thStyle: React.CSSProperties = {
  textAlign: "left",
  padding: "10px 14px",
  fontSize: 13,
  color: "#9ca3af",
  borderBottom: "1px solid rgba(148,163,184,0.3)",
};

const tdStyle: React.CSSProperties = {
  padding: "10px 14px",
  fontSize: 14,
  borderBottom: "1px solid rgba(15,23,42,0.9)",
};

export default LoansScreen;
