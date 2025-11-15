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
    const amountInWei = parseUnits(amount.toString(), 1);

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
    const repayTx = await creditLoanContract.repay("1", "4");

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
