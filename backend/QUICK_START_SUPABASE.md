# Quick Start: Supabase Setup

## 🎯 Your Supabase Project

**Project URL**: https://jmwhsuqhzdurrbynxuwd.supabase.co

## ⚡ 5-Minute Setup

### Step 1: Get Your Connection String

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Settings** (gear icon) → **Database**
3. Scroll to **Connection string** section
4. Copy the **URI** connection string
   - It looks like: `postgresql://postgres.[ref]:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres`
   - **Important**: Replace `[YOUR-PASSWORD]` with your actual database password
   - If you don't know your password, click **Reset database password** in the same section

### Step 2: Run Setup Script

```bash
cd backend
python setup_supabase.py
```

When prompted, paste your connection string. The script will:
- ✅ Test the connection
- ✅ Save it to `.env` file
- ✅ Verify everything works

### Step 3: Initialize Database

```bash
python -m app.init_db
```

This creates all tables in your Supabase database.

### Step 4: Create Sample Data (Optional)

```bash
python scripts/create_sample_data.py
```

This adds sample transactions and loans so you can test queries.

### Step 5: Start the Server

```bash
uvicorn app.main:app --reload
```

Your API is now connected to Supabase! 🎉

---

## 📊 Verify It Works

### Check in Supabase Dashboard

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Table Editor** in the sidebar
3. You should see:
   - `transactions` table
   - `loan_history` table
   - `credit_score_history` table

### Test API Endpoints

```bash
# Get all transactions
curl http://localhost:8000/api/transactions

# Get sample data (if you created it)
curl http://localhost:8000/api/users/0x1234567890abcdef1234567890abcdef12345678/transactions
```

---

## 🔄 Store Transactions Automatically

### When a User Borrows Money

After calling `issueLoan()` on your smart contract, store the transaction:

```python
import requests
from datetime import datetime, timezone

# After blockchain transaction
response = requests.post("http://localhost:8000/api/transactions", json={
    "user_address": "0x1234...",  # Borrower address
    "transaction_type": "loan_issued",
    "amount": 5000.0,  # Amount in USDC
    "currency": "USDC",
    "loan_id": 1,  # Loan ID from contract
    "tx_hash": "0xabc...",  # Transaction hash
    "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "confirmed"
})
```

### When a User Pays Back

After calling `repay()` on your smart contract:

```python
response = requests.post("http://localhost:8000/api/transactions", json={
    "user_address": "0x1234...",
    "transaction_type": "repay",
    "amount": 1000.0,  # Repayment amount
    "currency": "USDC",
    "loan_id": 1,
    "tx_hash": "0xdef...",
    "transaction_timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "confirmed"
})
```

### Or Use the Helper Script

```bash
# Add a loan
python scripts/add_transaction.py \
  --user 0x1234567890abcdef1234567890abcdef12345678 \
  --type loan_issued \
  --amount 5000.0 \
  --loan-id 1 \
  --tx-hash 0xabc...

# Add a repayment
python scripts/add_transaction.py \
  --user 0x1234567890abcdef1234567890abcdef12345678 \
  --type repay \
  --amount 1000.0 \
  --loan-id 1 \
  --tx-hash 0xdef...
```

---

## 🔍 Query Your Data

### Via API

```bash
# All transactions
GET http://localhost:8000/api/transactions

# User's transactions
GET http://localhost:8000/api/users/0x1234.../transactions

# Loan's transactions
GET http://localhost:8000/api/loans/1/transactions

# User's loans
GET http://localhost:8000/api/users/0x1234.../loans
```

### Via Supabase Dashboard

1. Go to **Table Editor**
2. Click on `transactions` table
3. Browse, filter, and search your data
4. Export as CSV if needed

### Via SQL (in Supabase SQL Editor)

```sql
-- Total borrowed per user
SELECT 
    user_address,
    SUM(amount) as total_borrowed
FROM transactions
WHERE transaction_type = 'loan_issued'
GROUP BY user_address;

-- Repayment history
SELECT *
FROM transactions
WHERE loan_id = 1
  AND transaction_type = 'repay'
ORDER BY transaction_timestamp;
```

---

## 🚀 Next Steps

1. **Integrate with your frontend**: Call the API endpoints from your React app
2. **Set up automatic syncing**: Use `scripts/blockchain_sync.py` to listen to blockchain events
3. **Add monitoring**: Check Supabase dashboard regularly for new transactions

---

## 📚 Full Documentation

See `SUPABASE_WORKFLOW.md` for complete documentation including:
- Blockchain event listener setup
- Advanced queries
- Troubleshooting
- Integration examples

---

## ✅ Checklist

- [ ] Got connection string from Supabase
- [ ] Ran `setup_supabase.py`
- [ ] Ran `python -m app.init_db`
- [ ] Created sample data (optional)
- [ ] Started API server
- [ ] Verified tables in Supabase dashboard
- [ ] Tested API endpoints

You're all set! 🎉

