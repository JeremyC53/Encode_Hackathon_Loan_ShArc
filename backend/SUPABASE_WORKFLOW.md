# Supabase Integration Workflow

Complete guide for connecting to Supabase and storing transaction data automatically.

## 🚀 Quick Start

### Step 1: Connect to Supabase

Run the setup script to connect to your Supabase database:

```bash
cd backend
python setup_supabase.py
```

This will:
1. Guide you to get your connection string from Supabase
2. Test the connection
3. Save it to `.env` file

**To get your connection string:**
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Find **Connection string** → **URI**
5. Copy the connection string (format: `postgresql://postgres:[PASSWORD]@db.xxxxx.supabase.co:5432/postgres`)

### Step 2: Initialize Database

Create all tables in your Supabase database:

```bash
python -m app.init_db
```

You should see: `✅ Database initialized successfully!`

### Step 3: Create Sample Data (Optional)

Populate the database with sample transactions and loans:

```bash
python scripts/create_sample_data.py
```

This creates:
- 3 sample users with credit scores
- 3 loans (2 active, 1 fully repaid)
- 10 transactions (loan issuances and repayments)

### Step 4: Start the API Server

```bash
uvicorn app.main:app --reload
```

The API will automatically use your Supabase database!

---

## 📊 Querying Data

### Using the API

Once your server is running, you can query data:

#### Get all transactions
```bash
curl http://localhost:8000/api/transactions
```

#### Get user's transactions
```bash
curl http://localhost:8000/api/users/0x1234567890abcdef1234567890abcdef12345678/transactions
```

#### Get loan transactions
```bash
curl http://localhost:8000/api/loans/1/transactions
```

#### Get user's loans
```bash
curl http://localhost:8000/api/users/0x1234567890abcdef1234567890abcdef12345678/loans
```

#### Create a new transaction
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x1234567890abcdef1234567890abcdef12345678",
    "transaction_type": "borrow",
    "amount": 1000.50,
    "currency": "USDC",
    "loan_id": 1,
    "tx_hash": "0xabc...",
    "transaction_timestamp": "2025-01-15T10:30:00Z",
    "status": "confirmed"
  }'
```

### Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Click on **Table Editor** in the sidebar
3. You'll see your tables:
   - `transactions` - All transaction records
   - `loan_history` - Loan records
   - `credit_score_history` - Credit score history

You can browse, filter, and query data directly in the dashboard!

---

## 🔄 Automatic Transaction Storage Workflow

### Option 1: Blockchain Event Listener (Recommended)

Automatically sync blockchain events to your database:

#### Setup

1. **Set environment variables** in `.env`:
```bash
CREDIT_LOAN_CONTRACT=0xYourContractAddress
RPC_URL=https://your-rpc-url
```

2. **Run the sync script**:
```bash
python scripts/blockchain_sync.py
```

This will:
- Connect to your blockchain
- Listen for `LoanIssued`, `RepaymentMade`, and `LoanFullyRepaid` events
- Automatically store transactions in the database

#### Sync specific transaction
```bash
python scripts/blockchain_sync.py --tx-hash 0xYourTransactionHash
```

#### Sync from specific block
```bash
python scripts/blockchain_sync.py --start-block 1000000
```

### Option 2: Manual API Calls

When a loan is issued or repayment is made, call the API:

#### When Loan is Issued

```python
import requests
from datetime import datetime, timezone

# After calling issueLoan() on your smart contract
tx_hash = "0x..."  # Transaction hash from blockchain
loan_id = 1  # Loan ID from contract
borrower = "0x1234..."  # Borrower address
principal = 5000.0  # Amount in USDC

response = requests.post("http://localhost:8000/api/transactions", json={
    "user_address": borrower,
    "transaction_type": "loan_issued",
    "amount": principal,
    "currency": "USDC",
    "loan_id": loan_id,
    "tx_hash": tx_hash,
    "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "confirmed"
})
```

#### When Repayment is Made

```python
# After calling repay() on your smart contract
tx_hash = "0x..."  # Transaction hash
loan_id = 1
borrower = "0x1234..."
repayment_amount = 1000.0

response = requests.post("http://localhost:8000/api/transactions", json={
    "user_address": borrower,
    "transaction_type": "repay",
    "amount": repayment_amount,
    "currency": "USDC",
    "loan_id": loan_id,
    "tx_hash": tx_hash,
    "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "confirmed"
})
```

### Option 3: Command Line Script

Use the helper script to manually add transactions:

```bash
# Add a loan issuance
python scripts/add_transaction.py \
  --user 0x1234567890abcdef1234567890abcdef12345678 \
  --type loan_issued \
  --amount 5000.0 \
  --loan-id 1 \
  --tx-hash 0xabc... \
  --block 12345

# Add a repayment
python scripts/add_transaction.py \
  --user 0x1234567890abcdef1234567890abcdef12345678 \
  --type repay \
  --amount 1000.0 \
  --loan-id 1 \
  --tx-hash 0xdef...
```

---

## 🔧 Integration with Smart Contracts

### Complete Workflow Example

Here's how to integrate with your `CreditLoan` contract:

```python
from web3 import Web3
import requests
from datetime import datetime, timezone

# Initialize Web3
w3 = Web3(Web3.HTTPProvider("https://your-rpc-url"))
contract_address = "0xYourContractAddress"
contract_abi = [...]  # Your contract ABI

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# 1. Issue a loan
def issue_loan_and_store(borrower: str, principal: int):
    # Call smart contract
    tx_hash = contract.functions.issueLoan(borrower, principal).transact({
        "from": w3.eth.accounts[0],
        "gas": 200000
    })
    
    # Wait for confirmation
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Get loan ID from event
    event = contract.events.LoanIssued().process_receipt(receipt)[0]
    loan_id = event["args"]["loanId"]
    
    # Store in database
    requests.post("http://localhost:8000/api/transactions", json={
        "user_address": borrower,
        "transaction_type": "loan_issued",
        "amount": principal / 1e6,  # Convert from 6 decimals
        "currency": "USDC",
        "loan_id": loan_id,
        "tx_hash": tx_hash.hex(),
        "block_number": receipt["blockNumber"],
        "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed"
    })
    
    return loan_id

# 2. Make repayment and store
def repay_and_store(loan_id: int, amount: int):
    # Call smart contract
    tx_hash = contract.functions.repay(loan_id, amount).transact({
        "from": w3.eth.accounts[0],
        "gas": 200000
    })
    
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    # Get borrower from event
    event = contract.events.RepaymentMade().process_receipt(receipt)[0]
    borrower = event["args"]["borrower"]
    
    # Store in database
    requests.post("http://localhost:8000/api/transactions", json={
        "user_address": borrower,
        "transaction_type": "repay",
        "amount": amount / 1e6,  # Convert from 6 decimals
        "currency": "USDC",
        "loan_id": loan_id,
        "tx_hash": tx_hash.hex(),
        "block_number": receipt["blockNumber"],
        "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "confirmed"
    })
```

---

## 📈 Monitoring & Queries

### View All Transactions in Supabase

1. Go to **Table Editor** → `transactions`
2. Use filters to find specific transactions
3. Export data as CSV if needed

### Common Queries

#### Total borrowed per user
```sql
SELECT 
    user_address,
    SUM(amount) as total_borrowed
FROM transactions
WHERE transaction_type = 'loan_issued'
GROUP BY user_address;
```

#### Repayment history for a loan
```sql
SELECT *
FROM transactions
WHERE loan_id = 1
  AND transaction_type = 'repay'
ORDER BY transaction_timestamp;
```

#### Active loans
```sql
SELECT *
FROM loan_history
WHERE is_active = true;
```

---

## 🛠️ Troubleshooting

### Connection Issues

**Error: "Connection refused"**
- Check your connection string is correct
- Verify your IP is allowed in Supabase (Settings → Database → Connection Pooling)
- Make sure you're using the correct password

**Error: "Database does not exist"**
- Run `python -m app.init_db` to create tables

### Transaction Not Appearing

1. Check the API response for errors
2. Verify the transaction was committed: `db.commit()`
3. Check Supabase dashboard to see if data exists
4. Verify user_address is lowercase (it's normalized automatically)

### Blockchain Sync Issues

1. Verify contract address is correct
2. Check RPC URL is accessible
3. Ensure contract ABI matches your deployed contract
4. Check event filters are correct

---

## 📚 Next Steps

1. **Set up automatic syncing**: Run `blockchain_sync.py` as a background service
2. **Add monitoring**: Set up alerts for failed transactions
3. **Create dashboards**: Use Supabase's built-in dashboard or connect to BI tools
4. **Add indexes**: Monitor query performance and add indexes if needed

---

## 🎯 Summary

✅ **Connected to Supabase** - Your database is ready  
✅ **Tables created** - All models are set up  
✅ **Sample data** - Test data available  
✅ **API endpoints** - Ready to store and query transactions  
✅ **Blockchain sync** - Automatic event listening available  

Your transaction history is now being stored in Supabase and can be queried via API or directly in the Supabase dashboard!

