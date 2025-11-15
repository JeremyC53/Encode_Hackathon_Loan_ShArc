# How to Add a Transaction to Supabase

## Quick Check: Are you connected to Supabase?

First, verify you're using Supabase (not SQLite):

```bash
python check_database_connection.py
```

If it says "Using SQLite", you need to:
1. Update your `.env` file with the Supabase connection string
2. Restart your server

## Method 1: Direct Database Script (Recommended)

This adds the transaction directly to the database:

```bash
python scripts/simulate_transaction.py
```

This will:
- Create a new loan transaction
- Create a repayment transaction
- Store both in Supabase
- Show you the transaction IDs

## Method 2: Via API (Server Must Be Running)

If your server is running, use the API:

```bash
# In one terminal, make sure server is running:
uvicorn app.main:app --reload

# In another terminal:
python scripts/add_transaction_via_api.py
```

## Method 3: Manual API Call

You can also use curl or Postman:

```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "0x9876543210fedcba9876543210fedcba98765432",
    "transaction_type": "loan_issued",
    "amount": 7500.0,
    "currency": "USDC",
    "loan_id": 4,
    "tx_hash": "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    "block_number": 5000,
    "transaction_timestamp": "2025-01-15T10:30:00Z",
    "status": "confirmed"
  }'
```

## Verify in Supabase

After adding a transaction:

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Table Editor** in the sidebar
3. Click on **transactions** table
4. You should see your new transaction!

## Troubleshooting

### "No data in Supabase"
- Check you're using Supabase connection string (not SQLite)
- Run `python check_database_connection.py` to verify
- Make sure `.env` file has correct password

### "Connection refused"
- Check your Supabase password in `.env` file
- Verify connection string format
- Check Supabase dashboard for connection issues

### "Table does not exist"
- Run: `python -m app.init_db`
- This creates all tables in Supabase

