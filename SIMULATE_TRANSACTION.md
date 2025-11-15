# How to Simulate a Transaction and Check in Supabase

## Quick Method (Recommended)

### Step 1: Simulate Transaction

Run this command:

```bash
cd backend
python -m scripts.simulate_transaction
```

This will:
- ✅ Create a loan transaction (7,500 USDC)
- ✅ Create a repayment transaction (2,750 USDC)
- ✅ Store both in Supabase
- ✅ Show you the transaction IDs

### Step 2: Verify in Supabase

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Table Editor** in the sidebar
3. Click **transactions** table
4. You should see the new transactions!

**Tip**: Sort by `created_at` DESC to see newest first.

### Step 3: Check via Script

You can also check what's in the database:

```bash
python -m scripts.check_supabase
```

This shows:
- Total transaction count
- Latest 5 transactions
- Active loans
- Database statistics

## Alternative: Via API (Server Must Be Running)

If your backend server is running, you can use the API method:

```bash
# Make sure server is running first:
# uvicorn app.main:app --reload

# Then simulate via API:
python -m scripts.simulate_transaction --api
```

## What Gets Created

When you run the simulation, it creates:

1. **Loan Transaction**
   - Type: `loan_issued`
   - Amount: 7,500 USDC
   - User: `0x9876543210fedcba9876543210fedcba98765432`
   - Loan ID: Next available ID

2. **Repayment Transaction**
   - Type: `repay`
   - Amount: 2,750 USDC
   - Same user and loan ID

3. **Loan Record**
   - Stored in `loan_history` table
   - Shows principal, fees, repayment status

## Verify in Supabase Dashboard

### View Transactions

1. Go to Supabase dashboard
2. **Table Editor** → **transactions**
3. Look for:
   - `transaction_type`: `loan_issued` or `repay`
   - `user_address`: `0x9876543210fedcba9876543210fedcba98765432`
   - `amount`: `7500.00` or `2750.00`
   - `status`: `confirmed`

### View Loans

1. **Table Editor** → **loan_history**
2. Look for:
   - `loan_id`: The ID created
   - `principal`: `7500.00`
   - `is_active`: `true`
   - `amount_repaid`: `2750.00`

## Query via API

You can also check via the API:

```bash
# Get all transactions
curl http://localhost:8000/api/transactions

# Get transactions for specific user
curl http://localhost:8000/api/users/0x9876543210fedcba9876543210fedcba98765432/transactions

# Get all loans
curl http://localhost:8000/api/loans
```

Or visit: http://localhost:8000/docs for interactive API documentation.

## Troubleshooting

### "No transactions found"
- Make sure you ran the simulation script
- Check database connection in `backend/.env`
- Verify Supabase connection: `python -m scripts.check_supabase`

### "Can't see data in Supabase"
- Refresh the Supabase dashboard
- Check you're looking at the right project
- Sort by `created_at` DESC to see newest first
- Check the `transactions` table (not `loan_history`)

### "Database connection error"
- Check your `.env` file has correct Supabase password
- Verify connection: `python -m scripts.check_supabase`

## Summary

1. ✅ Run: `python -m scripts.simulate_transaction`
2. ✅ Check Supabase dashboard → Table Editor → transactions
3. ✅ See your new transactions!

That's it! 🎉

