// screens/BorrowRepayScreen.tsx
import React, { useState } from "react";
import { recordTransfer } from "../utils/api";

type Tab = "borrow" | "repay";

const BorrowRepayScreen: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("borrow");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Borrow form state
  const [borrowAmount, setBorrowAmount] = useState("");
  const [borrowAddress, setBorrowAddress] = useState("");

  // Repay form state
  const [repayAmount, setRepayAmount] = useState("");
  const [repayLoanId, setRepayLoanId] = useState("");
  const [repayAddress, setRepayAddress] = useState("");

  // Demo user address (in real app, get from user context/wallet)
  const DEMO_USER_ADDRESS = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0a";

  const handleBorrow = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const amount = parseFloat(borrowAmount);
      if (isNaN(amount) || amount <= 0) {
        throw new Error("Please enter a valid amount");
      }

      const userAddress = borrowAddress.trim() || DEMO_USER_ADDRESS;
      if (!userAddress.startsWith("0x")) {
        throw new Error("Please enter a valid Ethereum address (0x...)");
      }

      // Record borrow transaction to Supabase
      const transaction = await recordTransfer({
        user_address: userAddress.toLowerCase(),
        transaction_type: "borrow",
        amount: amount,
        currency: "USDC",
        transaction_timestamp: new Date().toISOString(),
        status: "pending",
        extra_metadata: JSON.stringify({
          description: "Loan borrow request",
          requested_amount: amount,
        }),
      });

      setMessage({
        type: "success",
        text: `Borrow request recorded! Transaction ID: ${transaction.id}. Amount: $${amount.toFixed(2)} USDC`,
      });

      // Reset form
      setBorrowAmount("");
      setBorrowAddress("");

      console.log("Borrow transaction recorded:", transaction);
    } catch (error: any) {
      console.error("Borrow error:", error);
      setMessage({
        type: "error",
        text: error.message || "Failed to record borrow request. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRepay = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const amount = parseFloat(repayAmount);
      if (isNaN(amount) || amount <= 0) {
        throw new Error("Please enter a valid amount");
      }

      const userAddress = repayAddress.trim() || DEMO_USER_ADDRESS;
      if (!userAddress.startsWith("0x")) {
        throw new Error("Please enter a valid Ethereum address (0x...)");
      }

      const loanId = repayLoanId.trim() ? parseInt(repayLoanId) : null;

      // Record repayment transaction to Supabase
      const transaction = await recordTransfer({
        user_address: userAddress.toLowerCase(),
        transaction_type: "repay",
        amount: amount,
        currency: "USDC",
        loan_id: loanId,
        transaction_timestamp: new Date().toISOString(),
        status: "pending",
        extra_metadata: JSON.stringify({
          description: "Loan repayment",
          repayment_amount: amount,
          loan_id: loanId,
        }),
      });

      setMessage({
        type: "success",
        text: `Repayment recorded! Transaction ID: ${transaction.id}. Amount: $${amount.toFixed(2)} USDC`,
      });

      // Reset form
      setRepayAmount("");
      setRepayLoanId("");
      setRepayAddress("");

      console.log("Repay transaction recorded:", transaction);
    } catch (error: any) {
      console.error("Repay error:", error);
      setMessage({
        type: "error",
        text: error.message || "Failed to record repayment. Please try again.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>Borrow & Repay</h1>
      <p style={{ color: "#9ca3af", marginBottom: 24 }}>
        Borrow money or make repayments. All transactions are recorded to Supabase.
      </p>

      {/* Tabs */}
      <div style={tabsContainer}>
        <button
          type="button"
          onClick={() => {
            setActiveTab("borrow");
            setMessage(null);
          }}
          style={{
            ...tabStyle,
            ...(activeTab === "borrow" ? activeTabStyle : {}),
          }}
        >
          Borrow Money
        </button>
        <button
          type="button"
          onClick={() => {
            setActiveTab("repay");
            setMessage(null);
          }}
          style={{
            ...tabStyle,
            ...(activeTab === "repay" ? activeTabStyle : {}),
          }}
        >
          Repay Loan
        </button>
      </div>

      {/* Message Display */}
      {message && (
        <div
          style={{
            ...messageStyle,
            backgroundColor: message.type === "success" ? "#10b981" : "#ef4444",
            color: "#ffffff",
          }}
        >
          {message.text}
        </div>
      )}

      {/* Borrow Form */}
      {activeTab === "borrow" && (
        <div style={formContainer}>
          <form onSubmit={handleBorrow} style={formStyle}>
            <div style={formGroup}>
              <label style={labelStyle}>
                User Address (Ethereum)
                <input
                  type="text"
                  value={borrowAddress}
                  onChange={(e) => setBorrowAddress(e.target.value)}
                  placeholder={DEMO_USER_ADDRESS}
                  style={inputStyle}
                />
                <small style={hintStyle}>
                  Leave empty to use demo address: {DEMO_USER_ADDRESS}
                </small>
              </label>
            </div>

            <div style={formGroup}>
              <label style={labelStyle}>
                Borrow Amount (USDC)
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={borrowAmount}
                  onChange={(e) => setBorrowAmount(e.target.value)}
                  placeholder="1000.00"
                  style={inputStyle}
                  required
                />
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                ...submitButtonStyle,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Processing..." : "Submit Borrow Request"}
            </button>
          </form>
        </div>
      )}

      {/* Repay Form */}
      {activeTab === "repay" && (
        <div style={formContainer}>
          <form onSubmit={handleRepay} style={formStyle}>
            <div style={formGroup}>
              <label style={labelStyle}>
                User Address (Ethereum)
                <input
                  type="text"
                  value={repayAddress}
                  onChange={(e) => setRepayAddress(e.target.value)}
                  placeholder={DEMO_USER_ADDRESS}
                  style={inputStyle}
                />
                <small style={hintStyle}>
                  Leave empty to use demo address: {DEMO_USER_ADDRESS}
                </small>
              </label>
            </div>

            <div style={formGroup}>
              <label style={labelStyle}>
                Loan ID (Optional)
                <input
                  type="number"
                  value={repayLoanId}
                  onChange={(e) => setRepayLoanId(e.target.value)}
                  placeholder="123"
                  style={inputStyle}
                />
                <small style={hintStyle}>
                  Leave empty if repaying without a specific loan ID
                </small>
              </label>
            </div>

            <div style={formGroup}>
              <label style={labelStyle}>
                Repayment Amount (USDC)
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={repayAmount}
                  onChange={(e) => setRepayAmount(e.target.value)}
                  placeholder="500.00"
                  style={inputStyle}
                  required
                />
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                ...submitButtonStyle,
                opacity: loading ? 0.6 : 1,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Processing..." : "Submit Repayment"}
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

// Styles
const tabsContainer: React.CSSProperties = {
  display: "flex",
  gap: 8,
  marginBottom: 24,
};

const tabStyle: React.CSSProperties = {
  padding: "10px 20px",
  borderRadius: 8,
  border: "1px solid rgba(148,163,184,0.3)",
  backgroundColor: "#020617",
  color: "#9ca3af",
  fontSize: 14,
  fontWeight: 500,
  cursor: "pointer",
  transition: "all 0.2s",
};

const activeTabStyle: React.CSSProperties = {
  backgroundColor: "rgba(59,130,246,0.2)",
  borderColor: "rgba(59,130,246,0.5)",
  color: "#60a5fa",
};

const formContainer: React.CSSProperties = {
  backgroundColor: "#020617",
  borderRadius: 16,
  padding: 24,
  border: "1px solid rgba(148,163,184,0.3)",
  maxWidth: 500,
};

const formStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 20,
};

const formGroup: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: 8,
};

const labelStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 500,
  color: "#e5e7eb",
  display: "flex",
  flexDirection: "column",
  gap: 6,
};

const inputStyle: React.CSSProperties = {
  padding: "10px 14px",
  borderRadius: 8,
  border: "1px solid rgba(148,163,184,0.3)",
  backgroundColor: "#0b1120",
  color: "#e5e7eb",
  fontSize: 14,
  outline: "none",
  transition: "border-color 0.2s",
};

const hintStyle: React.CSSProperties = {
  fontSize: 12,
  color: "#6b7280",
  marginTop: 4,
};

const submitButtonStyle: React.CSSProperties = {
  padding: "12px 24px",
  borderRadius: 8,
  border: "none",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
  background: "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(79,70,229,0.95))",
  color: "#ffffff",
  transition: "opacity 0.2s",
  marginTop: 8,
};

const messageStyle: React.CSSProperties = {
  padding: "12px 16px",
  borderRadius: 8,
  marginBottom: 20,
  fontSize: 14,
  maxWidth: 500,
};

export default BorrowRepayScreen;
