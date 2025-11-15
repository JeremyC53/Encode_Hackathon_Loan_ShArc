# How to Query User Transaction Logs

This guide shows you how to fetch all transaction logs for a specific user from the database.

## Quick Start

### Method 1: Using the Python Script (Recommended)

The easiest way is to use the provided script:

```bash
cd backend
python -m scripts.query_user_logs <user_address>
```

**Example:**
```bash
python -m scripts.query_user_logs 0x9876543210fedcba9876543210fedcba98765432
```

### Method 2: Using Raw SQL

If you prefer raw SQL queries:

```bash
python -m scripts.query_user_logs <user_address> --raw-sql
```

### Method 3: Export to JSON

Export the results to a JSON file:

```bash
python -m scripts.query_user_logs <user_address> --json
python -m scripts.query_user_logs <user_address> --json --output user_logs.json
```

---

## Direct SQL Queries

If you want to run SQL queries directly, here are examples for different database systems:

### PostgreSQL (Supabase)

If you're using Supabase, you can run queries in the Supabase SQL Editor:

```sql
-- Get all transactions for a specific user
SELECT 
    id,
    user_address,
    transaction_type,
    amount,
    currency,
    loan_id,
    tx_hash,
    block_number,
    created_at,
    transaction_timestamp,
    status,
    extra_metadata
FROM transactions
WHERE LOWER(user_address) = LOWER('0x9876543210fedcba9876543210fedcba98765432')
ORDER BY transaction_timestamp DESC;
```

**In Supabase Dashboard:**
1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **SQL Editor** in the sidebar
3. Paste the query above (replace the user address)
4. Click **Run**

### SQLite (Local Development)

If you're using SQLite locally, you can use the SQLite CLI:

```bash
cd backend
sqlite3 loan_sharc.db
```

Then run:

```sql
-- Get all transactions for a specific user
SELECT 
    id,
    user_address,
    transaction_type,
    amount,
    currency,
    loan_id,
    tx_hash,
    block_number,
    created_at,
    transaction_timestamp,
    status,
    extra_metadata
FROM transactions
WHERE LOWER(user_address) = LOWER('0x9876543210fedcba9876543210fedcba98765432')
ORDER BY transaction_timestamp DESC;
```

---

## Using Python with SQLAlchemy

You can also write your own Python script:

```python
from app.database import SessionLocal
from app.models import Transaction
from sqlalchemy import desc

db = SessionLocal()

# Query all transactions for a user
user_address = "0x9876543210fedcba9876543210fedcba98765432"
transactions = (
    db.query(Transaction)
    .filter(Transaction.user_address == user_address.lower())
    .order_by(desc(Transaction.transaction_timestamp))
    .all()
)

# Print results
for tx in transactions:
    print(f"ID: {tx.id}, Type: {tx.transaction_type}, Amount: {tx.amount} {tx.currency}")

db.close()
```

---

## Using Raw SQL in Python

If you prefer raw SQL in Python:

```python
from app.database import SessionLocal, engine
from sqlalchemy import text

db = SessionLocal()

user_address = "0x9876543210fedcba9876543210fedcba98765432"

sql_query = text("""
    SELECT * FROM transactions
    WHERE LOWER(user_address) = :user_address
    ORDER BY transaction_timestamp DESC
""")

result = db.execute(sql_query, {"user_address": user_address.lower()})

for row in result:
    print(f"ID: {row.id}, Type: {row.transaction_type}, Amount: {row.amount}")

db.close()
```

---

## Using the API Endpoint

If your backend server is running, you can also use the REST API:

```bash
# Get all transactions for a user
curl http://localhost:8000/api/users/0x9876543210fedcba9876543210fedcba98765432/transactions

# With pagination
curl "http://localhost:8000/api/users/0x9876543210fedcba9876543210fedcba98765432/transactions?page=1&page_size=50"

# Filter by transaction type
curl "http://localhost:8000/api/users/0x9876543210fedcba9876543210fedcba98765432/transactions?transaction_type=borrow"
```

---

## Common Query Patterns

### Get transactions by type

```sql
SELECT * FROM transactions
WHERE LOWER(user_address) = LOWER('0x...')
  AND transaction_type = 'borrow'
ORDER BY transaction_timestamp DESC;
```

### Get transactions for a specific loan

```sql
SELECT * FROM transactions
WHERE LOWER(user_address) = LOWER('0x...')
  AND loan_id = 1
ORDER BY transaction_timestamp DESC;
```

### Get total borrowed amount

```sql
SELECT 
    SUM(amount) as total_borrowed
FROM transactions
WHERE LOWER(user_address) = LOWER('0x...')
  AND transaction_type = 'borrow';
```

### Get transaction count by type

```sql
SELECT 
    transaction_type,
    COUNT(*) as count,
    SUM(amount) as total_amount
FROM transactions
WHERE LOWER(user_address) = LOWER('0x...')
GROUP BY transaction_type
ORDER BY count DESC;
```

### Get recent transactions (last 7 days)

```sql
SELECT * FROM transactions
WHERE LOWER(user_address) = LOWER('0x...')
  AND transaction_timestamp >= NOW() - INTERVAL '7 days'
ORDER BY transaction_timestamp DESC;
```

---

## Table Schema

The `transactions` table has the following columns:

- `id` (Integer) - Primary key
- `user_address` (String, 66 chars) - Ethereum address
- `transaction_type` (String, 20 chars) - 'borrow', 'repay', 'loan_issued', etc.
- `amount` (Numeric) - Amount in USDC (6 decimals)
- `currency` (String, 10 chars) - Currency code (default: 'USDC')
- `loan_id` (Integer) - Reference to loan ID (nullable)
- `tx_hash` (String, 66 chars) - On-chain transaction hash (nullable)
- `block_number` (Integer) - Block number if on-chain (nullable)
- `created_at` (DateTime) - When record was created
- `transaction_timestamp` (DateTime) - When transaction actually occurred
- `status` (String, 20 chars) - 'pending', 'confirmed', 'failed'
- `extra_metadata` (Text) - JSON string for additional data (nullable)

---

## Tips

1. **Always lowercase addresses**: User addresses are stored in lowercase, so use `LOWER()` in SQL queries
2. **Use indexes**: The table has indexes on `user_address`, `transaction_type`, and `loan_id` for fast queries
3. **Order by timestamp**: Use `ORDER BY transaction_timestamp DESC` to get newest first
4. **Check Supabase dashboard**: You can also view data visually in the Supabase Table Editor

