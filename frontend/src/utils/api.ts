/**
 * API utility functions for communicating with the backend.
 * Handles recording transfers and transactions to Supabase via the backend API.
 */

// Use relative path for Vite proxy, or fall back to direct URL if VITE_API_URL is set
const API_BASE_URL = import.meta.env.VITE_API_URL || "";

export interface TransactionCreate {
  user_address: string;
  transaction_type: string; // 'transfer', 'borrow', 'repay', 'loan_issued', etc.
  amount: number;
  currency?: string;
  loan_id?: number | null;
  tx_hash?: string | null;
  block_number?: number | null;
  transaction_timestamp: string; // ISO format datetime
  status?: string;
  extra_metadata?: string | null;
}

export interface TransactionResponse {
  id: number;
  user_address: string;
  transaction_type: string;
  amount: number;
  currency: string;
  loan_id: number | null;
  tx_hash: string | null;
  block_number: number | null;
  created_at: string;
  transaction_timestamp: string;
  status: string;
  extra_metadata: string | null;
}

/**
 * Records a transfer/transaction to Supabase via the backend API.
 * 
 * @param transferData - The transfer/transaction data to record
 * @returns Promise<TransactionResponse> - The created transaction record
 * @throws Error if the API call fails
 * 
 * @example
 * ```ts
 * const transaction = await recordTransfer({
 *   user_address: "0x1234...",
 *   transaction_type: "transfer",
 *   amount: 100.50,
 *   currency: "USDC",
 *   transaction_timestamp: new Date().toISOString(),
 *   status: "pending"
 * });
 * ```
 */
export async function recordTransfer(
  transferData: TransactionCreate
): Promise<TransactionResponse> {
  try {
    const url = API_BASE_URL ? `${API_BASE_URL}/api/transactions` : "/api/transactions";
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...transferData,
        // Ensure currency defaults to USDC
        currency: transferData.currency || "USDC",
        // Ensure status defaults to pending
        status: transferData.status || "pending",
        // Ensure transaction_timestamp is in ISO format
        transaction_timestamp: transferData.transaction_timestamp || new Date().toISOString(),
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to record transfer: ${response.status} ${response.statusText}. ${errorText}`
      );
    }

    const data: TransactionResponse = await response.json();
    return data;
  } catch (error) {
    console.error("Error recording transfer:", error);
    throw error;
  }
}

/**
 * Gets transactions for a specific user.
 * 
 * @param userAddress - The user's Ethereum address
 * @param transactionType - Optional filter by transaction type
 * @param page - Page number (default: 1)
 * @param pageSize - Items per page (default: 50)
 * @returns Promise with transaction list
 */
export async function getUserTransactions(
  userAddress: string,
  transactionType?: string,
  page: number = 1,
  pageSize: number = 50
): Promise<{ transactions: TransactionResponse[]; total: number; page: number; page_size: number }> {
  try {
    const params = new URLSearchParams({
      user_address: userAddress,
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (transactionType) {
      params.append("transaction_type", transactionType);
    }

    const url = API_BASE_URL 
      ? `${API_BASE_URL}/api/users/${encodeURIComponent(userAddress)}/transactions?${params}`
      : `/api/users/${encodeURIComponent(userAddress)}/transactions?${params}`;
    const response = await fetch(url);

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(
        `Failed to fetch transactions: ${response.status} ${response.statusText}. ${errorText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching user transactions:", error);
    throw error;
  }
}

/**
 * Helper function to create a transfer transaction record.
 * Use this when a user makes a transfer in the UI.
 * 
 * @param fromAddress - Sender's Ethereum address
 * @param amount - Transfer amount
 * @param toAddress - Recipient's Ethereum address (optional, stored in metadata)
 * @param currency - Currency code (default: "USDC")
 * @param metadata - Additional metadata (optional)
 * @returns Promise<TransactionResponse>
 */
export async function createTransferTransaction(
  fromAddress: string,
  amount: number,
  toAddress?: string,
  currency: string = "USDC",
  metadata?: Record<string, any>
): Promise<TransactionResponse> {
  const extraMetadata = {
    to_address: toAddress,
    ...metadata,
  };

  return recordTransfer({
    user_address: fromAddress,
    transaction_type: "transfer",
    amount,
    currency,
    transaction_timestamp: new Date().toISOString(),
    status: "pending",
    extra_metadata: JSON.stringify(extraMetadata),
  });
}
