# Transfer Integration Guide

This guide explains how to integrate the transfer functionality from your teammate's UI updates with Supabase database recording.

## What's Ready

✅ **API Utility Created**: `frontend/src/utils/api.ts`
- `recordTransfer()` - Records any transaction to Supabase
- `createTransferTransaction()` - Helper specifically for transfer transactions
- `getUserTransactions()` - Retrieves user's transaction history

✅ **Backend API Endpoint**: `POST /api/transactions`
- Already configured to save to Supabase
- Accepts transaction data and stores it in the database

## Finding the Transfer Functionality

Since the transfer functionality might be in a different branch or not yet visible, here are steps to locate it:

1. **Check all branches**:
   ```bash
   git branch -a
   git checkout <branch-name>
   ```

2. **Look for transfer-related code**:
   - Search for buttons/forms with "transfer", "send", "payment" keywords
   - Check if there's a new screen or component
   - Look for Web3 wallet interactions (Metamask, WalletConnect)

3. **Common locations**:
   - `frontend/src/screens/DashboardScreen.tsx` - Transfer button on dashboard
   - `frontend/src/screens/LoansScreen.tsx` - Repayment/transfer in loans
   - `frontend/src/components/` - New transfer component

## How to Integrate Transfer Recording

Once you find the transfer functionality, follow these steps:

### Step 1: Import the API Utility

In the file where the transfer happens (e.g., where the transfer button/form is):

```typescript
import { createTransferTransaction, recordTransfer } from "../utils/api";
```

### Step 2: Call the API After Transfer

When a transfer is successful, record it:

```typescript
// Example: After user initiates a transfer
const handleTransfer = async (fromAddress: string, amount: number, toAddress?: string) => {
  try {
    // ... existing transfer logic (e.g., blockchain transaction) ...
    
    // Record to Supabase after successful transfer
    const transaction = await createTransferTransaction(
      fromAddress,      // Sender's Ethereum address
      amount,           // Transfer amount
      toAddress,        // Optional: Recipient address
      "USDC",           // Currency (default: USDC)
      {                 // Optional: Additional metadata
        description: "Transfer to user",
        // Add any other relevant data
      }
    );
    
    console.log("Transfer recorded:", transaction);
    // Show success message to user
    
  } catch (error) {
    console.error("Failed to record transfer:", error);
    // Show error message to user
  }
};
```

### Step 3: Handle Different Transfer Scenarios

#### Scenario A: Simple Transfer (without blockchain)
```typescript
// For UI-only transfers (no blockchain transaction)
await createTransferTransaction(
  userAddress,
  amount,
  recipientAddress,
  "USDC"
);
```

#### Scenario B: Blockchain Transfer (with tx hash)
```typescript
// For blockchain transfers, include tx_hash and block_number
await recordTransfer({
  user_address: userAddress,
  transaction_type: "transfer",
  amount: amount,
  currency: "USDC",
  tx_hash: txHash,           // From blockchain transaction
  block_number: blockNumber,  // From blockchain transaction
  transaction_timestamp: new Date().toISOString(),
  status: "confirmed",        // or "pending" initially
  extra_metadata: JSON.stringify({
    to_address: recipientAddress,
  }),
});
```

#### Scenario C: Repayment Transfer
```typescript
// For loan repayments
await recordTransfer({
  user_address: userAddress,
  transaction_type: "repay",
  amount: amount,
  currency: "USDC",
  loan_id: loanId,           // Reference to the loan
  transaction_timestamp: new Date().toISOString(),
  status: "pending",
});
```

## Example Integration

Here's a complete example showing how to add transfer recording to a component:

```typescript
import React, { useState } from "react";
import { createTransferTransaction } from "../utils/api";

const TransferScreen: React.FC = () => {
  const [amount, setAmount] = useState("");
  const [recipient, setRecipient] = useState("");
  const [loading, setLoading] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Get user address (from login/user context)
      const userAddress = "0x..."; // Replace with actual user address
      
      // ... Perform actual transfer (blockchain or internal) ...
      
      // Record to Supabase
      const transaction = await createTransferTransaction(
        userAddress,
        parseFloat(amount),
        recipient
      );
      
      alert(`Transfer recorded! Transaction ID: ${transaction.id}`);
      
      // Reset form
      setAmount("");
      setRecipient("");
      
    } catch (error) {
      console.error("Transfer failed:", error);
      alert("Failed to record transfer: " + error.message);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={loading}>
        {loading ? "Processing..." : "Send Transfer"}
      </button>
    </form>
  );
};
```

## Testing

1. **Start the backend**:
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Make a test transfer**:
   - Use the transfer UI
   - Check browser console for any errors
   - Verify in Supabase that the transaction was recorded

4. **Check Supabase**:
   - Go to your Supabase dashboard
   - Navigate to Table Editor → `transactions` table
   - Verify the new transaction record

## Troubleshooting

### Transfer not recording?
- Check browser console for API errors
- Verify backend is running on `http://localhost:8000`
- Check CORS settings (should already be configured)
- Verify user address format (should start with `0x`)

### Version conflicts?
If you encounter merge conflicts:
```bash
# Stash your changes
git stash

# Pull latest changes
git pull origin main

# Apply your stashed changes
git stash pop

# Resolve conflicts manually if needed
```

### API errors?
- Check backend logs for errors
- Verify Supabase connection in `backend/.env`
- Ensure database tables are initialized (`python -m app.init_db`)

## Next Steps

1. Locate the transfer functionality in your teammate's code
2. Add the import: `import { createTransferTransaction } from "../utils/api"`
3. Call the function after successful transfers
4. Test with a real transfer
5. Verify in Supabase dashboard

## Need Help?

- Check `backend/app/routes.py` for available API endpoints
- See `backend/app/schemas.py` for expected data formats
- Review `frontend/src/utils/api.ts` for utility functions

