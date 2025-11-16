// screens/LoansScreen.tsx
import React, { useState, useEffect } from "react";
import { useWallet } from "../contexts/WalletContext";

// Add custom CSS for range slider
const sliderStyles = `
  input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 3px solid #020617;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.5);
  }

  input[type="range"]::-moz-range-thumb {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #3b82f6;
    cursor: pointer;
    border: 3px solid #020617;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.5);
  }
`;

import { repayLoan } from "../contracts/contractUtils";
import { createClient } from "@supabase/supabase-js";

type Loan = {
  id: number; // Loan ID from smart contract
  name: string;
  amount: string;
  status: string;
  next: string;
  borrower?: string;
  principal?: number;
  service_fee?: number;
  total_owed?: number;
  amount_repaid?: number;
  timestamp?: number;
  active?: boolean;
};

type RawEarning = {
  date: string;
  company: string;
  earnings: string;
};

const supabaseUrl = `https://${import.meta.env.VITE_SUPABASE_ID}.supabase.co`;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY as string;
const supabase = createClient(supabaseUrl, supabaseKey);

// Helper function to parse amount string to USD
function parseAmountToUsd(amountStr: string, gbpToUsd: number): number {
  const cleanStr = amountStr.replace(/[,$£]/g, "").trim();
  const val = Number.parseFloat(cleanStr);
  if (Number.isNaN(val)) return 0;
  // If original string had £, convert to USD
  if (amountStr.includes("£")) {
    return val * gbpToUsd;
  }
  return val;
}

// Helper to pick latest earnings file
function pickLatestEarningsFilename(names: string[]): string | null {
  const regex = /^dummy_earnings_(\d{8})_(\d+)\.json$/;
  let best: { date: string; index: number; name: string } | null = null;

  for (const name of names) {
    const match = name.match(regex);
    if (!match) continue;
    const [, dateStr, indexStr] = match;
    const index = Number.parseInt(indexStr, 10);

    if (!best || dateStr > best.date || (dateStr === best.date && index > best.index)) {
      best = { date: dateStr, index, name };
    }
  }

  return best ? best.name : null;
}

const LoansScreen: React.FC = () => {
  const [loanAmount, setLoanAmount] = useState(1500);
  const [selectedPlan, setSelectedPlan] = useState<1 | 3 | 6>(3);
  const [availableLimit, setAvailableLimit] = useState(5000); // Default limit
  const [isLoadingLimit, setIsLoadingLimit] = useState(false);

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedLoan, setSelectedLoan] = useState<Loan | null>(null);
  const [repayAmount, setRepayAmount] = useState("");
  const [isRepaying, setIsRepaying] = useState(false);
  const [isIssuingLoan, setIsIssuingLoan] = useState(false);

  // Loans state
  const [loans, setLoans] = useState<Loan[]>([]);
  const [isLoadingLoans, setIsLoadingLoans] = useState(false);

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

  // Function to refresh loans list
  const refreshLoans = async () => {
    if (!walletAddress) return;
    
    try {
      setIsLoadingLoans(true);
      
      const response = await fetch(
        `http://localhost:8000/api/loans/borrower/${walletAddress}/details`
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch loans: ${response.statusText}`);
      }

      const data = await response.json();
      
      const transformedLoans: Loan[] = data.loans.map((loan: any) => {
        const remainingBalance = loan.total_owed - loan.amount_repaid;
        const isActive = loan.active;
        
        const nextPaymentDate = new Date((loan.timestamp + 30 * 24 * 60 * 60) * 1000);
        const nextPaymentStr = isActive 
          ? nextPaymentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
          : "-";
        
        return {
          id: loan.id,
          name: `Loan #${loan.id}`,
          amount: remainingBalance.toFixed(2),
          status: isActive ? "Active" : "Paid off",
          next: nextPaymentStr,
          borrower: loan.borrower,
          principal: loan.principal,
          service_fee: loan.service_fee,
          total_owed: loan.total_owed,
          amount_repaid: loan.amount_repaid,
          timestamp: loan.timestamp,
          active: loan.active,
        };
      });

      setLoans(transformedLoans);
      console.log(`Refreshed ${transformedLoans.length} loans`);
    } catch (error) {
      console.error("Error refreshing loans:", error);
    } finally {
      setIsLoadingLoans(false);
    }
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
      
      // Call the smart contract repay function
      console.log(`Repaying ${repayAmount} USDC for Loan ID: ${selectedLoan.id}`);
      const txHash = await repayLoan(selectedLoan.id, parseFloat(repayAmount));
      
      alert(
        `Successfully repaid ${repayAmount} USDC for ${selectedLoan.name}!\n\n` +
        `Transaction Hash: ${txHash}\n\n` +
        `View on Arc Testnet Explorer:\n` +
        `https://testnet.arcscan.app/tx/${txHash}`
      );
      
      handleCloseModal();
      
      // Refresh loans list to show updated balances
      setTimeout(() => refreshLoans(), 2000); // Wait 2 seconds for blockchain to update
      
      // Refresh wallet balance
      if (refreshBalance) {
        setTimeout(() => refreshBalance(), 2000);
      }
    } catch (error: any) {
      console.error("Repayment error:", error);
      alert(
        `Failed to repay loan:\n\n${error.message}\n\n` +
        `Make sure you:\n` +
        `1. Are connected to Arc Testnet\n` +
        `2. Have sufficient USDC balance\n` +
        `3. Have approved the contract`
      );
    } finally {
      setIsRepaying(false);
    }
  };

  const handleIssueLoan = async () => {
    // Validate wallet is connected to get borrower address
    if (!walletAddress) {
      alert("Please connect your wallet first to receive the loan");
      return;
    }

    // Validate loan amount
    if (!loanAmount || loanAmount <= 0) {
      alert("Please enter a valid loan amount");
      return;
    }

    try {
      setIsIssuingLoan(true);
      
      console.log(`Requesting loan of ${loanAmount} USDC for wallet: ${walletAddress}`);
      
      // Call backend API to issue loan (backend wallet issues loan to borrower)
      const response = await fetch("http://localhost:8000/api/loans/issue", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          borrower_address: walletAddress,
          principal: loanAmount,
          wait_for_confirmation: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to issue loan");
      }

      const result = await response.json();
      
      alert(
        `✅ Loan Issued Successfully!\n\n` +
        `Amount: ${loanAmount} USDC\n` +
        `Borrower: ${walletAddress}\n` +
        `Transaction Hash: ${result.transaction_hash}\n\n` +
        `View on Arc Testnet Explorer:\n` +
        `https://testnet.arcscan.app/tx/${result.transaction_hash}`
      );
      
      // Refresh wallet balance to reflect received loan
      if (refreshBalance) {
        setTimeout(() => refreshBalance(), 2000);
      }
      
      // Refresh loans list to show the new loan
      setTimeout(() => refreshLoans(), 2000);
    } catch (error: any) {
      console.error("Loan issuance error:", error);
      alert(
        `❌ Failed to issue loan:\n\n${error.message}\n\n` +
        `Please check:\n` +
        `1. Backend server is running (http://localhost:8000)\n` +
        `2. Backend wallet has sufficient USDC balance\n` +
        `3. Contract is properly configured`
      );
    } finally {
      setIsIssuingLoan(false);
    }
  };

  const {
    walletAddress,
    balance,
    isConnecting,
    isFetchingBalance,
    connectWallet,
    disconnectWallet,
    refreshBalance,
  } = useWallet();

  // Fetch borrowing limit based on user earnings (50% of total earnings)
  useEffect(() => {
    const fetchBorrowingLimit = async () => {
      if (!walletAddress) {
        setAvailableLimit(5000); // Default limit when no wallet connected
        return;
      }

      try {
        setIsLoadingLimit(true);

        // Get current GBP to USD rate
        let gbpToUsd = 1.3172; // fallback
        try {
          const fxResp = await fetch("https://api.exchangerate.host/latest?base=GBP&symbols=USD");
          if (fxResp.ok) {
            const fxData = await fxResp.json();
            const rate = fxData?.rates?.USD;
            if (typeof rate === "number" && rate > 0) {
              gbpToUsd = rate;
            }
          }
        } catch (fxErr) {
          console.warn("FX fetch failed, using fallback", fxErr);
        }

        // List earnings files in Supabase
        const { data: files, error: listError } = await supabase.storage
          .from("earnings")
          .list("", { limit: 1000 });

        if (listError) throw listError;

        if (!files || files.length === 0) {
          console.warn("No earnings files found");
          setAvailableLimit(5000);
          return;
        }

        const latestName = pickLatestEarningsFilename(files.map((f: { name: string }) => f.name));

        if (!latestName) {
          console.warn("No matching earnings file found");
          setAvailableLimit(5000);
          return;
        }

        // Download the earnings file
        const { data: fileData, error: downloadError } = await supabase.storage
          .from("earnings")
          .download(latestName);

        if (downloadError || !fileData) throw downloadError;

        const text = await fileData.text();
        const earningsData = JSON.parse(text) as RawEarning[];

        // Calculate total earnings in USD
        let totalEarnings = 0;
        for (const earning of earningsData) {
          totalEarnings += parseAmountToUsd(earning.earnings, gbpToUsd);
        }

        // Set borrowing limit to 50% of total earnings, rounded to nearest 100
        const borrowingLimit = Math.round((totalEarnings * 0.5) / 100) * 100 * 0.1;
        const finalLimit = Math.max(100, borrowingLimit); // Minimum $100
        
        setAvailableLimit(finalLimit);
        // Adjust loan amount if it exceeds the new limit
        setLoanAmount((prevAmount) => Math.min(prevAmount, finalLimit));
        
        console.log(`Total earnings: $${totalEarnings.toFixed(2)}`);
        console.log(`Borrowing limit set to $${borrowingLimit} `);
      } catch (error) {
        console.error("Error fetching borrowing limit:", error);
        // Fall back to default limit on error
        setAvailableLimit(5000);
      } finally {
        setIsLoadingLimit(false);
      }
    };

    fetchBorrowingLimit();
  }, [walletAddress]);

  // Fetch borrower's loans from the blockchain
  useEffect(() => {
    const fetchBorrowerLoans = async () => {
      if (!walletAddress) {
        setLoans([]);
        return;
      }

      try {
        setIsLoadingLoans(true);
        
        // Call the new API endpoint to get all loans with details
        const response = await fetch(
          `http://localhost:8000/api/loans/borrower/${walletAddress}/details`
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch loans: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Transform API response to match our Loan type
        const transformedLoans: Loan[] = data.loans.map((loan: any) => {
          const remainingBalance = loan.total_owed - loan.amount_repaid;
          const isActive = loan.active;
          
          // Calculate next payment date (simple estimation - 30 days from loan timestamp)
          const nextPaymentDate = new Date((loan.timestamp + 30 * 24 * 60 * 60) * 1000);
          const nextPaymentStr = isActive 
            ? nextPaymentDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            : "-";
          
          return {
            id: loan.id,
            name: `Loan #${loan.id}`,
            amount: remainingBalance.toFixed(2),
            status: isActive ? "Active" : "Paid off",
            next: nextPaymentStr,
            borrower: loan.borrower,
            principal: loan.principal,
            service_fee: loan.service_fee,
            total_owed: loan.total_owed,
            amount_repaid: loan.amount_repaid,
            timestamp: loan.timestamp,
            active: loan.active,
          };
        });

        setLoans(transformedLoans);
        console.log(`Fetched ${transformedLoans.length} loans for ${walletAddress}`);
      } catch (error) {
        console.error("Error fetching borrower loans:", error);
        // Set empty array on error but don't show alert to avoid interrupting user
        setLoans([]);
      } finally {
        setIsLoadingLoans(false);
      }
    };

    fetchBorrowerLoans();
  }, [walletAddress]);

  return (
    <div>
      <style>{sliderStyles}</style>
      
      {/* Header with Wallet Info */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, marginBottom: 8 }}>Loans</h1>
          <p style={{ color: "#9ca3af", margin: 0 }}>
            Apply for a new loan or manage your existing loans.
          </p>
        </div>

        {/* Wallet Connection Section */}
        <div style={{ textAlign: "right" }}>
          {!walletAddress ? (
            <button
              onClick={connectWallet}
              disabled={isConnecting}
              style={{
                padding: "10px 20px",
                fontSize: 14,
                fontWeight: 600,
                background: "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(79,70,229,0.95))",
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
              <div style={{ fontSize: 13, color: "#22c55e", fontWeight: 600, marginBottom: 8 }}>
                {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
              </div>
              <div style={{ borderTop: "1px solid rgba(148,163,184,0.2)", paddingTop: 8, marginBottom: 8 }}>
                <div style={{ fontSize: 11, color: "#9ca3af", marginBottom: 2 }}>
                  Balance
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, color: "#22c55e" }}>
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

      {/* Loan Application Card */}
      <div
        style={{
          backgroundColor: "#020617",
          borderRadius: 16,
          padding: 32,
          marginBottom: 32,
          border: "1px solid rgba(148,163,184,0.3)",
        }}
      >
        {/* Amount Slider */}
        <div style={{ marginBottom: 32 }}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: 16,
            }}
          >
            <h2 style={{ fontSize: 18, color: "#f9fafb", margin: 0 }}>
              How much do you need?
            </h2>
            <span
              style={{ fontSize: 24, fontWeight: 700, color: "#f9fafb" }}
            >
              ${loanAmount.toLocaleString()}
            </span>
          </div>

          <input
            type="range"
            min="1"
            max={availableLimit}
            step="5"
            value={loanAmount}
            onChange={handleSliderChange}
            style={{
              width: "100%",
              height: 8,
              borderRadius: 4,
              outline: "none",
              background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${
                (loanAmount / availableLimit) * 100
              }%, #374151 ${(loanAmount / availableLimit) * 100}%, #374151 100%)`,
              WebkitAppearance: "none",
              appearance: "none",
              cursor: "pointer",
            }}
          />

          <p style={{ color: "#9ca3af", fontSize: 14, marginTop: 8 }}>
            {isLoadingLimit ? (
              <span>Calculating your personalized limit...</span>
            ) : (
              <span>
                Your available limit: <strong style={{ color: "#3b82f6" }}>${availableLimit.toLocaleString()}</strong>
                {walletAddress && <span style={{ fontSize: 12, marginLeft: 8 }}>(50% of total earnings)</span>}
              </span>
            )}
          </p>
        </div>

        {/* Repayment Plan */}
      

        {/* Review Button */}
        <button
          onClick={handleIssueLoan}
          disabled={isIssuingLoan || !walletAddress}
          style={{
            width: "100%",
            padding: "16px 24px",
            fontSize: 16,
            fontWeight: 600,
            color: "#ffffff",
            background: isIssuingLoan || !walletAddress 
              ? "rgba(156,163,175,0.5)" 
              : "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(79,70,229,0.95))",
            border: "none",
            borderRadius: 12,
            cursor: isIssuingLoan || !walletAddress ? "not-allowed" : "pointer",
            transition: "all 0.2s",
            opacity: isIssuingLoan || !walletAddress ? 0.6 : 1,
          }}
          onMouseOver={(e) => {
            if (!isIssuingLoan && walletAddress) {
              e.currentTarget.style.background = "linear-gradient(135deg, rgba(37,99,235,0.95), rgba(67,56,202,0.95))";
            }
          }}
          onMouseOut={(e) => {
            if (!isIssuingLoan && walletAddress) {
              e.currentTarget.style.background = "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(79,70,229,0.95))";
            }
          }}
        >
          {isIssuingLoan ? "Processing Loan..." : !walletAddress ? "Connect Wallet First" : "Review My Advance"}
        </button>
      </div>

      {/* Existing Loans Table */}
      <h2 style={{ fontSize: 20, marginBottom: 16, color: "#e5e7eb" }}>
        Your Existing Loans
      </h2>

      {isLoadingLoans ? (
        <div
          style={{
            backgroundColor: "#020617",
            borderRadius: 16,
            padding: 48,
            textAlign: "center",
            border: "1px solid rgba(148,163,184,0.3)",
          }}
        >
          <div style={{ fontSize: 16, color: "#9ca3af" }}>
            Loading your loans...
          </div>
        </div>
      ) : loans.length === 0 ? (
        <div
          style={{
            backgroundColor: "#020617",
            borderRadius: 16,
            padding: 48,
            textAlign: "center",
            border: "1px solid rgba(148,163,184,0.3)",
          }}
        >
          <div style={{ fontSize: 16, color: "#9ca3af", marginBottom: 8 }}>
            {walletAddress ? "No loans found" : "Connect your wallet to view loans"}
          </div>
          {walletAddress && (
            <div style={{ fontSize: 14, color: "#6b7280" }}>
              Apply for your first loan above to get started
            </div>
          )}
        </div>
      ) : (
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
              <th style={thStyle}>Amount Remaining</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Next Payment</th>
              <th style={thStyle}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loans.map((loan, idx) => (
              <tr
                key={loan.id}
                style={{
                  backgroundColor: idx % 2 === 0 ? "#020617" : "#020617",
                }}
              >
                <td style={tdStyle}>
                  <div>{loan.name}</div>
                  {loan.principal && (
                    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                      Principal: ${loan.principal.toFixed(2)}
                    </div>
                  )}
                </td>
                <td style={tdStyle}>
                  <div>{loan.amount} USDC</div>
                  {loan.total_owed && loan.amount_repaid !== undefined && (
                    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 2 }}>
                      Repaid: ${loan.amount_repaid.toFixed(2)} / ${loan.total_owed.toFixed(2)}
                    </div>
                  )}
                </td>
                <td style={tdStyle}>
                  <span
                    style={{
                      padding: "4px 8px",
                      borderRadius: 6,
                      fontSize: 12,
                      fontWeight: 600,
                      backgroundColor: loan.status === "Active" ? "rgba(34, 197, 94, 0.2)" : "rgba(156, 163, 175, 0.2)",
                      color: loan.status === "Active" ? "#22c55e" : "#9ca3af",
                    }}
                  >
                    {loan.status}
                  </span>
                </td>
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
      )}

      {/* Repayment Modal */}
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
                <strong>Loan ID:</strong> <span style={{ color: "#0f172a" }}>{selectedLoan?.id}</span>
              </p>
              <p style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
                <strong>Loan Name:</strong> <span style={{ color: "#0f172a" }}>{selectedLoan?.name}</span>
              </p>
              <p style={{ fontSize: 14, color: "#6b7280", marginBottom: 16 }}>
                <strong>Outstanding Amount:</strong>{" "}
                <span style={{ color: "#0f172a", fontWeight: "bold" }}>{selectedLoan?.amount} USDC</span>
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
