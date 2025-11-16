// screens/LoansScreen.tsx
import React, { useState } from "react";
import { useWallet } from "../contexts/WalletContext";
import { repayLoan } from "../contracts/contractUtils";

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const sliderStyles = `
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 3px solid white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }

  input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 3px solid white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
`;

type Loan = {
  id: number;
  name: string;
  amount: string;
  status: string;
  next: string;
};

const LoansScreen: React.FC = () => {
  const [loanAmount, setLoanAmount] = useState(1500);
  const [selectedPlan, setSelectedPlan] = useState<1 | 3 | 6>(3);
  const availableLimit = 5000;

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<Loan | null>(null);
  const [repayAmount, setRepayAmount] = useState("");
  const [isRepaying, setIsRepaying] = useState(false);
  const [isIssuingLoan, setIsIssuingLoan] = useState(false);

  const {
    walletAddress,
    balance,
    isConnecting,
    isFetchingBalance,
    connectWallet,
    disconnectWallet,
    refreshBalance,
  } = useWallet();

  const loans: Loan[] = [
    { id: 0, name: "Freelancer Gear", amount: "3500", status: "Active", next: "1 Apr" },
    { id: 1, name: "Laptop Upgrade", amount: "1200", status: "Active", next: "15 Mar" },
    { id: 2, name: "Travel Float", amount: "800", status: "Paid off", next: "-" },
  ];

  const repaymentPlans = [
    { months: 1, label: "1 Month", payment: loanAmount, dueDate: "Jun 15, 2024" },
    { months: 3, label: "3 Months", payment: Math.round((loanAmount / 3) * 100) / 100, payments: 3 },
    { months: 6, label: "6 Months", payment: Math.round((loanAmount / 6) * 100) / 100, payments: 6 },
  ];

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setLoanAmount(Number(e.target.value));
  };

  const handleRepayClick = (loan: Loan) => {
    setSelectedLoan(loan);
    setRepayAmount("");
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedLoan(null);
    setRepayAmount("");
  };

  const handleSubmitRepayment = async () => {
    if (!repayAmount || parseFloat(repayAmount) <= 0) {
      alert("Please enter a valid amount");
      return;
    }

    if (!selectedLoan) {
      alert("No loan selected");
      return;
    }

    try {
      setIsRepaying(true);
      const txHash = await repayLoan(selectedLoan.id, parseFloat(repayAmount));

      alert(
        `Successfully repaid ${repayAmount} USDC for ${selectedLoan.name}!\n\n` +
          `Transaction Hash: ${txHash}\n\n` +
          `View on Arc Testnet Explorer:\n` +
          `https://testnet.arcscan.app/tx/${txHash}`,
      );

      handleCloseModal();
    } catch (error: any) {
      console.error("Repayment error:", error);
      alert(
        `Failed to repay loan:\n\n${error.message}\n\n` +
          `Make sure you:\n` +
          `1. Are connected to Arc Testnet\n` +
          `2. Have sufficient USDC balance\n` +
          `3. Have approved the contract`,
      );
    } finally {
      setIsRepaying(false);
    }
  };

  const handleIssueLoan = async () => {
    if (!walletAddress) {
      alert("Please connect your wallet first to receive the loan");
      return;
    }

    if (!loanAmount || loanAmount <= 0) {
      alert("Please enter a valid loan amount");
      return;
    }

    try {
      setIsIssuingLoan(true);

      const response = await fetch(`${API_BASE_URL}/api/loans/issue`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          borrower_address: walletAddress,
          principal: loanAmount,
          wait_for_confirmation: false,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to issue loan");
      }

      const result = await response.json();

      alert(
        `✅ Loan Issued Successfully!\n\n` +
          `Amount: ${loanAmount} USDC\n` +
          `Borrower: ${walletAddress}\n` +
          `Transaction Hash: ${result.tx_hash}\n` +
          `Loan ID: ${result.loan_id ?? "Pending"}\n\n` +
          `View on Arc Testnet Explorer:\n` +
          `https://testnet.arcscan.app/tx/${result.tx_hash}`,
      );

      await refreshBalance();
    } catch (error: any) {
      console.error("Loan issuance error:", error);
      alert(
        `❌ Failed to issue loan:\n\n${error.message}\n\n` +
          `Please check:\n` +
          `1. Backend server is running (${API_BASE_URL})\n` +
          `2. Backend wallet has sufficient USDC balance\n` +
          `3. Contract is properly configured`,
      );
    } finally {
      setIsIssuingLoan(false);
    }
  };

  return (
    <div>
      <style>{sliderStyles}</style>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          marginBottom: 24,
        }}
      >
        <div>
          <h1 style={{ fontSize: 24, marginBottom: 8 }}>Loans</h1>
          <p style={{ color: "#9ca3af", margin: 0 }}>
            Apply for a new loan or manage your existing loans.
          </p>
        </div>

        <div style={{ textAlign: "right" }}>
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
                <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>
                  Balance
                </div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 700,
                    color: "#22c55e",
                  }}
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
          backgroundColor: "#ffffff",
          borderRadius: 16,
          padding: 32,
          marginBottom: 32,
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
        }}
      >
        <div style={{ marginBottom: 32 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <h2 style={{ fontSize: 18, color: "#0f172a", margin: 0 }}>
              How much do you need?
            </h2>
            <span style={{ fontSize: 24, fontWeight: 700, color: "#0f172a" }}>
              ${loanAmount.toLocaleString()}
            </span>
          </div>

          <input
            type="range"
            min="100"
            max={availableLimit}
            step="50"
            value={loanAmount}
            onChange={handleSliderChange}
            style={{
              width: "100%",
              height: 8,
              borderRadius: 4,
              outline: "none",
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${
                (loanAmount / availableLimit) * 100
              }%, #e5e7eb ${(loanAmount / availableLimit) * 100}%, #e5e7eb 100%)`,
              WebkitAppearance: "none",
              appearance: "none",
              cursor: "pointer",
            }}
          />

          <p style={{ color: "#6b7280", fontSize: 14, marginTop: 8 }}>
            Your available limit: ${availableLimit.toLocaleString()}
          </p>
        </div>

        <div style={{ marginBottom: 32 }}>
          <h3 style={{ fontSize: 18, color: "#0f172a", marginBottom: 16 }}>
            Choose your repayment plan
          </h3>

          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 16,
            }}
          >
            {repaymentPlans.map((plan) => (
              <button
                key={plan.months}
                onClick={() => setSelectedPlan(plan.months as 1 | 3 | 6)}
                style={{
                  backgroundColor: "#ffffff",
                  border:
                    selectedPlan === plan.months
                      ? "2px solid #3b82f6"
                      : "1px solid #e5e7eb",
                  borderRadius: 12,
                  padding: 20,
                  cursor: "pointer",
                  textAlign: "left",
                  transition: "all 0.2s",
                }}
              >
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 600,
                    color: "#0f172a",
                    marginBottom: 8,
                  }}
                >
                  {plan.label}
                </div>
                <div style={{ fontSize: 14, color: "#6b7280" }}>
                  {plan.months === 1
                    ? `Pay by ${plan.dueDate}`
                    : `${plan.payments} payments of $${plan.payment}`}
                </div>
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleIssueLoan}
          disabled={isIssuingLoan || !walletAddress}
          style={{
            width: "100%",
            padding: "16px 24px",
            fontSize: 16,
            fontWeight: 600,
            color: "#ffffff",
            backgroundColor:
              isIssuingLoan || !walletAddress ? "#9ca3af" : "#3b82f6",
            border: "none",
            borderRadius: 12,
            cursor: isIssuingLoan || !walletAddress ? "not-allowed" : "pointer",
            transition: "background-color 0.2s",
            opacity: isIssuingLoan || !walletAddress ? 0.7 : 1,
          }}
          onMouseOver={(e) => {
            if (!isIssuingLoan && walletAddress) {
              e.currentTarget.style.backgroundColor = "#2563eb";
            }
          }}
          onMouseOut={(e) => {
            if (!isIssuingLoan && walletAddress) {
              e.currentTarget.style.backgroundColor = "#3b82f6";
            }
          }}
        >
          {isIssuingLoan
            ? "Processing Loan..."
            : !walletAddress
            ? "Connect Wallet First"
            : "Review My Advance"}
        </button>
      </div>

      <h2 style={{ fontSize: 20, marginBottom: 16, color: "#e5e7eb" }}>
        Your Existing Loans
      </h2>

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
            <th style={thStyle}>Action</th>
          </tr>
        </thead>
        <tbody>
          {loans.map((loan, idx) => (
            <tr
              key={loan.name}
              style={{
                backgroundColor: idx % 2 === 0 ? "#020617" : "#020617",
              }}
            >
              <td style={tdStyle}>{loan.name}</td>
              <td style={tdStyle}>{loan.amount} USDC</td>
              <td style={tdStyle}>{loan.status}</td>
              <td style={tdStyle}>{loan.next}</td>
              <td style={tdStyle}>
                {loan.status === "Active" && (
                  <button
                    onClick={() => handleRepayClick(loan)}
                    style={{
                      padding: "6px 16px",
                      fontSize: 13,
                      fontWeight: 600,
                      backgroundColor: "#3b82f6",
                      color: "white",
                      border: "none",
                      borderRadius: 6,
                      cursor: "pointer",
                    }}
                  >
                    Repay
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {isModalOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000,
          }}
          onClick={handleCloseModal}
        >
          <div
            style={{
              backgroundColor: "#ffffff",
              borderRadius: 16,
              padding: 32,
              maxWidth: 500,
              width: "90%",
              boxShadow: "0 10px 25px rgba(0, 0, 0, 0.3)",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 24,
              }}
            >
              <h2
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: "#0f172a",
                  margin: 0,
                }}
              >
                Repay Loan
              </h2>
              <button
                onClick={handleCloseModal}
                style={{
                  background: "transparent",
                  border: "none",
                  fontSize: 28,
                  color: "#6b7280",
                  cursor: "pointer",
                  lineHeight: 1,
                }}
              >
                ×
              </button>
            </div>

            <div style={{ marginBottom: 24 }}>
              <p style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
                <strong>Loan ID:</strong>{" "}
                <span style={{ color: "#0f172a" }}>{selectedLoan?.id}</span>
              </p>
              <p style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
                <strong>Loan Name:</strong>{" "}
                <span style={{ color: "#0f172a" }}>{selectedLoan?.name}</span>
              </p>
              <p style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
                <strong>Outstanding Amount:</strong>{" "}
                <span style={{ color: "#0f172a", fontWeight: "bold" }}>
                  {selectedLoan?.amount} USDC
                </span>
              </p>

              <label
                style={{
                  display: "block",
                  fontSize: 14,
                  fontWeight: 600,
                  color: "#0f172a",
                  marginBottom: 8,
                }}
              >
                Repayment Amount
              </label>
              <input
                type="number"
                placeholder="Enter amount"
                value={repayAmount}
                onChange={(e) => setRepayAmount(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  fontSize: 16,
                  border: "2px solid #e5e7eb",
                  borderRadius: 8,
                  outline: "none",
                  boxSizing: "border-box",
                  color: "#0f172a",
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = "#3b82f6")}
                onBlur={(e) => (e.currentTarget.style.borderColor = "#e5e7eb")}
              />
            </div>

            <div style={{ display: "flex", gap: 12 }}>
              <button
                onClick={handleCloseModal}
                style={{
                  flex: 1,
                  padding: "12px 24px",
                  fontSize: 16,
                  fontWeight: 600,
                  color: "#6b7280",
                  backgroundColor: "#f3f4f6",
                  border: "none",
                  borderRadius: 8,
                  cursor: "pointer",
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitRepayment}
                disabled={isRepaying}
                style={{
                  flex: 1,
                  padding: "12px 24px",
                  fontSize: 16,
                  fontWeight: 600,
                  color: "#ffffff",
                  backgroundColor: isRepaying ? "#9ca3af" : "#3b82f6",
                  border: "none",
                  borderRadius: 8,
                  cursor: isRepaying ? "not-allowed" : "pointer",
                  opacity: isRepaying ? 0.7 : 1,
                }}
                onMouseOver={(e) => {
                  if (!isRepaying) {
                    e.currentTarget.style.backgroundColor = "#2563eb";
                  }
                }}
                onMouseOut={(e) => {
                  if (!isRepaying) {
                    e.currentTarget.style.backgroundColor = "#3b82f6";
                  }
                }}
              >
                {isRepaying ? "Processing..." : "Submit"}
              </button>
            </div>
          </div>
        </div>
      )}
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
