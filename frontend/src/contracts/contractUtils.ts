// Utility helpers for blockchain interactions (Arc Testnet)
import { BrowserProvider, Contract, formatUnits, parseUnits } from "ethers";
import {
  CREDIT_LOAN_ABI,
  CREDIT_LOAN_ADDRESS,
  ERC20_ABI,
  USDC_ADDRESS,
} from "../contexts/CreditLoanABI";

declare global {
  interface Window {
    ethereum?: any;
  }
}

const USDC_DECIMALS = 6;

const getSigner = async () => {
  if (!window.ethereum) {
    throw new Error("MetaMask is not installed");
  }
  const provider = new BrowserProvider(window.ethereum);
  return provider.getSigner();
};

const getCreditLoanContract = async () => {
  const signer = await getSigner();
  return new Contract(CREDIT_LOAN_ADDRESS, CREDIT_LOAN_ABI, signer);
};

const getUsdcContract = async () => {
  const signer = await getSigner();
  return new Contract(USDC_ADDRESS, ERC20_ABI, signer);
};

export const repayLoan = async (loanId: number, amount: number): Promise<string> => {
  try {
    const signer = await getSigner();
    const borrowerAddress = await signer.getAddress();
    const amountInUnits = parseUnits(amount.toString(), USDC_DECIMALS);

    const usdc = await getUsdcContract();
    const currentAllowance = await usdc.allowance(borrowerAddress, CREDIT_LOAN_ADDRESS);

    if (currentAllowance < amountInUnits) {
      const approveTx = await usdc.approve(CREDIT_LOAN_ADDRESS, amountInUnits);
      await approveTx.wait();
    }

    const creditLoan = await getCreditLoanContract();
    const repayTx = await creditLoan.repay(loanId, amountInUnits);
    const receipt = await repayTx.wait();
    return receipt.hash;
  } catch (error: any) {
    console.error("Error repaying loan:", error);
    throw new Error(error?.message ?? "Failed to repay loan");
  }
};

export const getRemainingBalance = async (loanId: number): Promise<string> => {
  try {
    const creditLoan = await getCreditLoanContract();
    const balance = await creditLoan.getRemainingBalance(loanId);
    return formatUnits(balance, USDC_DECIMALS);
  } catch (error: any) {
    console.error("Error reading loan balance:", error);
    throw new Error(error?.message ?? "Failed to get remaining balance");
  }
};

export const getBorrowerLoans = async (borrowerAddress: string): Promise<number[]> => {
  try {
    const creditLoan = await getCreditLoanContract();
    const loanIds = await creditLoan.getBorrowerLoans(borrowerAddress);
    return loanIds.map((id: bigint) => Number(id));
  } catch (error: any) {
    console.error("Error reading borrower loans:", error);
    throw new Error(error?.message ?? "Failed to get borrower loans");
  }
};

