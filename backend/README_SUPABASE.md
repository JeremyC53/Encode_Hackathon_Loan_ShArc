# Supabase Integration - Complete Guide

## 📋 What You Have Now

✅ **Database Setup Script** (`setup_supabase.py`) - Connect to your Supabase project  
✅ **Database Models** - Transactions, Loans, Credit Scores  
✅ **API Endpoints** - Store and query transaction data  
✅ **Sample Data Script** - Create test data  
✅ **Blockchain Sync** - Automatically store transactions from blockchain events  
✅ **Helper Scripts** - Manual transaction entry  

---

## 🎯 Your Supabase Project

**URL**: https://jmwhsuqhzdurrbynxuwd.supabase.co

---

## 📁 Files Created

### Setup & Configuration
- `setup_supabase.py` - Interactive setup script
- `.env` - Stores your database connection (created automatically)

### Scripts
- `scripts/create_sample_data.py` - Generate test data
- `scripts/blockchain_sync.py` - Listen to blockchain events
- `scripts/add_transaction.py` - Manually add transactions

### Documentation
- `QUICK_START_SUPABASE.md` - 5-minute setup guide
- `SUPABASE_WORKFLOW.md` - Complete workflow documentation
- `DATABASE_SETUP.md` - General database setup guide

---

## 🚀 Quick Start (3 Steps)

### 1. Connect to Supabase
```bash
cd backend
python setup_supabase.py
```
Paste your connection string when prompted.

### 2. Initialize Database
```bash
python -m app.init_db
```

### 3. Start Server
```bash
uvicorn app.main:app --reload
```

Done! Your API is now connected to Supabase.

---

## 📊 Database Schema

### `transactions` Table
Stores all loan-related transactions:
- Borrows (`loan_issued`)
- Repayments (`repay`)
- Other transaction types

**Key Fields:**
- `user_address` - Wallet address
- `transaction_type` - Type of transaction
- `amount` - Amount in USDC
- `loan_id` - Associated loan
- `tx_hash` - Blockchain transaction hash
- `transaction_timestamp` - When it occurred

### `loan_history` Table
Stores loan records synced from blockchain:
- Loan terms (principal, fees, APR)
- Repayment status
- Active/inactive status

### `credit_score_history` Table
Tracks credit score changes over time.

---

## 🔄 Complete Workflow

### Scenario: User Borrows Money

1. **Smart Contract**: Call `issueLoan(borrower, amount)`
2. **Get Transaction Hash**: From blockchain receipt
3. **Store in Database**: 
   ```python
   POST /api/transactions
   {
     "user_address": "0x...",
     "transaction_type": "loan_issued",
     "amount": 5000.0,
     "loan_id": 1,
     "tx_hash": "0x...",
     "transaction_timestamp": "2025-01-15T10:30:00Z",
     "status": "confirmed"
   }
   ```

### Scenario: User Pays Back

1. **Smart Contract**: Call `repay(loanId, amount)`
2. **Get Transaction Hash**: From blockchain receipt
3. **Store in Database**:
   ```python
   POST /api/transactions
   {
     "user_address": "0x...",
     "transaction_type": "repay",
     "amount": 1000.0,
     "loan_id": 1,
     "tx_hash": "0x...",
     "transaction_timestamp": "2025-01-15T10:30:00Z",
     "status": "confirmed"
   }
   ```

### Automatic Option: Blockchain Event Listener

Instead of manual API calls, use the event listener:

```bash
# Set environment variables
export CREDIT_LOAN_CONTRACT=0xYourContractAddress
export RPC_URL=https://your-rpc-url

# Run sync script
python scripts/blockchain_sync.py
```

This automatically listens for blockchain events and stores them in the database.

---

## 📡 API Endpoints

### Create Transaction
```bash
POST /api/transactions
```

### Get Transactions
```bash
GET /api/transactions?user_address=0x...&transaction_type=repay
GET /api/users/{address}/transactions
GET /api/loans/{loan_id}/transactions
```

### Get Loans
```bash
GET /api/loans?user_address=0x...&is_active=true
GET /api/users/{address}/loans
```

See `http://localhost:8000/docs` for interactive API documentation.

---

## 🔍 Querying Data

### Via API
```bash
curl http://localhost:8000/api/transactions
```

### Via Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click **Table Editor**
4. Browse your data

### Via SQL
In Supabase SQL Editor:
```sql
SELECT * FROM transactions 
WHERE user_address = '0x1234...' 
ORDER BY transaction_timestamp DESC;
```

---

## 🛠️ Troubleshooting

### "Connection refused"
- Check connection string is correct
- Verify password in connection string
- Check IP is allowed in Supabase settings

### "Table does not exist"
- Run `python -m app.init_db`

### "Import errors"
- Install dependencies: `pip install -r requirements.txt`

---

## 📚 Next Steps

1. **Create Sample Data**: `python scripts/create_sample_data.py`
2. **Test Queries**: Use API endpoints or Supabase dashboard
3. **Integrate Frontend**: Connect your React app to the API
4. **Set Up Auto-Sync**: Configure blockchain event listener
5. **Add Monitoring**: Set up alerts for failed transactions

---

## 📖 Documentation Files

- **QUICK_START_SUPABASE.md** - Start here! 5-minute setup
- **SUPABASE_WORKFLOW.md** - Complete workflow guide
- **DATABASE_SETUP.md** - General database information

---

## ✅ You're Ready!

Your Supabase database is set up and ready to store transaction history. Every time a user borrows or pays back money, you can store it in the database and query it later.

Happy coding! 🚀

