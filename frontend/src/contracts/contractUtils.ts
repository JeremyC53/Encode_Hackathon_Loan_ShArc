// Utility functions for blockchain interactions
import { BrowserProvider, Contract, parseUnits, formatUnits } from "ethers";
import {
  CREDIT_LOAN_ABI,
  ERC20_ABI,
  CREDIT_LOAN_ADDRESS,
  USDC_ADDRESS,
} from "../contexts/CreditLoanABI";

// Extend Window interface for ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}

/**
 * Get the signer from MetaMask
 */
export const getSigner = async () => {
  if (!window.ethereum) {
    throw new Error("MetaMask is not installed");
  }

  const provider = new BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  return signer;
};

/**
 * Get CreditLoan contract instance
 */
export const getCreditLoanContract = async () => {
  const signer = await getSigner();
  return new Contract(CREDIT_LOAN_ADDRESS, CREDIT_LOAN_ABI, signer);
};

/**
 * Get USDC contract instance
 */
export const getUSDCContract = async () => {
  const signer = await getSigner();
  return new Contract(USDC_ADDRESS, ERC20_ABI, signer);
};

/**
 * Repay a loan
 * @param loanId - The ID of the loan to repay
 * @param amount - The amount to repay in USDC (as a number, will be converted to proper units)
 */
export const repayLoan = async (
  loanId: number,
  amount: number
): Promise<string> => {
  try {
    const signer = await getSigner();
    const signerAddress = await signer.getAddress();
    console.log(signerAddress, "signerAddress");
    // Convert amount to USDC units (18 decimals on Arc Testnet)
    const amountInWei = parseUnits(amount.toString(), 6);

    // Step 1: Check current allowance
    const usdcContract = await getUSDCContract();
    const currentAllowance = await usdcContract.allowance(
      signerAddress,
      CREDIT_LOAN_ADDRESS
    );
    console.log(currentAllowance, "cuu");
    // Step 2: Approve USDC if needed
    if (currentAllowance < amountInWei) {
      console.log("Approving USDC...");
      const approveTx = await usdcContract.approve(
        CREDIT_LOAN_ADDRESS,
        amountInWei
      );
      await approveTx.wait();
      console.log("USDC approved");
    }

    // Step 3: Call repay function
    console.log("Calling repay function...");
    const creditLoanContract = await getCreditLoanContract();
    const feeData = await signer.provider?.getFeeData();
console.log("Current gas fees:", feeData);

const repayTx = await creditLoanContract.repay(loanId, amountInWei, {
  gasLimit: 400000,
  maxFeePerGas: feeData?.maxFeePerGas,              // dynamically fetched
  maxPriorityFeePerGas: feeData?.maxPriorityFeePerGas // dynamically fetched
});

    // Wait for transaction confirmation
    const receipt = await repayTx.wait();
    console.log("Repayment successful:", receipt);

    return receipt.hash;
  } catch (error: any) {
    console.error("Error repaying loan:", error);
    throw new Error(error.message || "Failed to repay loan");
  }
};

/**
 * Get remaining balance for a loan
 * @param loanId - The ID of the loan
 */
export const getRemainingBalance = async (loanId: number): Promise<string> => {
  try {
    const creditLoanContract = await getCreditLoanContract();
    const balance = await creditLoanContract.getRemainingBalance(loanId);

    // Convert from wei to USDC
    return formatUnits(balance, 18);
  } catch (error: any) {
    console.error("Error getting remaining balance:", error);
    throw new Error(error.message || "Failed to get remaining balance");
  }
};

/**
 * Get all loans for a borrower
 * @param borrowerAddress - The address of the borrower
 */
export const getBorrowerLoans = async (
  borrowerAddress: string
): Promise<number[]> => {
  try {
    const creditLoanContract = await getCreditLoanContract();
    const loanIds = await creditLoanContract.getBorrowerLoans(borrowerAddress);

    return loanIds.map((id: bigint) => Number(id));
  } catch (error: any) {
    console.error("Error getting borrower loans:", error);
    throw new Error(error.message || "Failed to get borrower loans");
  }
};

/**
 * Get credit score for a user address
 * @param userAddress - The wallet address of the user
 * @returns Object with score and last_updated timestamp, or null if no score exists
 */
export const getCreditScore = async (
  userAddress: string
): Promise<{ user: string; score: number; last_updated: number } | null> => {
  try {
    const response = await fetch(
      `http://localhost:8000/api/credit-score/${userAddress}`,
      {
        method: "GET",
      }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return null; // No credit score exists
      }
      throw new Error(`Failed to fetch credit score: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error: any) {
    console.error("Error getting credit score:", error);
    // Return null if score doesn't exist or error occurred
    return null;
  }
};

/**
 * Set credit score for a user address
 * @param userAddress - The wallet address of the user
 * @param score - The credit score to set (must be > 0)
 * @param waitForConfirmation - Whether to wait for blockchain confirmation
 * @returns Transaction details
 */
export const setCreditScore = async (
  userAddress: string,
  score: number,
  waitForConfirmation: boolean = false
): Promise<any> => {
  try {
    const response = await fetch(
      "http://localhost:8000/api/credit-score/set",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_address: userAddress,
          score: Math.round(score), // Ensure it's an integer
          wait_for_confirmation: waitForConfirmation,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to set credit score");
    }

    const data = await response.json();
    console.log("Credit score set successfully:", data);
    return data;
  } catch (error: any) {
    console.error("Error setting credit score:", error);
    throw new Error(error.message || "Failed to set credit score");
  }
};

/**
 * Check if user has a credit score, and update it if it's different from the calculated score
 * @param userAddress - The wallet address of the user
 * @param score - The credit score to set/update
 * @returns Object with hasScore boolean, existingScore, updated boolean, and transaction details
 */
export const checkAndSetCreditScore = async (
  userAddress: string,
  score: number
): Promise<{
  hasScore: boolean;
  existingScore?: number;
  updated: boolean;
  transaction?: any;
}> => {
  try {
    // Step 1: Check if user already has a credit score
    const existingScore = await getCreditScore(userAddress);

    // If user has a score
    if (existingScore && existingScore.score > 0) {
      // Compare with the new calculated score
      if (existingScore.score === Math.round(score)) {
        console.log(
          `User credit score is up to date: ${existingScore.score}. No update needed.`
        );
        return {
          hasScore: true,
          existingScore: existingScore.score,
          updated: false,
        };
      }

      // Scores are different, update the credit score
      console.log(
        `Credit score changed from ${existingScore.score} to ${Math.round(score)}. Updating...`
      );
      const transaction = await setCreditScore(userAddress, score, false);

      return {
        hasScore: true,
        existingScore: existingScore.score,
        updated: true,
        transaction,
      };
    }

    // Step 2: User doesn't have a score, so set it for the first time
    console.log(`Setting credit score for ${userAddress}: ${score}`);
    const transaction = await setCreditScore(userAddress, score, false);

    return {
      hasScore: false,
      updated: true,
      transaction,
    };
  } catch (error: any) {
    console.error("Error in checkAndSetCreditScore:", error);
    throw new Error(error.message || "Failed to check and set credit score");
  }
};
