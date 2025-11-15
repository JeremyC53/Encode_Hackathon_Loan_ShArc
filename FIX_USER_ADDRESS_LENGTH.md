# Fixed: User Address Length Error

## ✅ Problem
The error was: `value too long for type character varying(42)`

Ethereum addresses are exactly 42 characters, but PostgreSQL was rejecting them. This might be due to how the column was created or encoding issues.

## ✅ Solution
Updated the model to use `String(66)` instead of `String(42)` for all `user_address` columns. This matches the `tx_hash` length and provides extra room.

---

## How to Fix the Database

You have two options depending on your setup:

### Option 1: Update Existing Tables (Supabase/PostgreSQL) ⭐ Recommended

Run the migration script:
```bash
cd backend
python scripts/update_user_address_column.py
```

This will update the existing column without losing data.

---

### Option 2: Recreate Tables (Development Only)

If you're okay with losing existing data (for development):

```bash
cd backend

# Drop and recreate all tables
python -m app.init_db --drop
python -m app.init_db
```

**Warning:** This will delete all existing transactions, loans, and other data!

---

### Option 3: Manual SQL (Supabase)

If you have access to Supabase SQL editor:

```sql
ALTER TABLE transactions 
ALTER COLUMN user_address TYPE VARCHAR(66);

ALTER TABLE loan_history 
ALTER COLUMN user_address TYPE VARCHAR(66);

ALTER TABLE credit_score_history 
ALTER COLUMN user_address TYPE VARCHAR(66);
```

---

## After Fixing

1. **Restart your backend server** to ensure it picks up the model changes
2. **Try the borrow/repay request again**
3. The error should be resolved!

---

## Verify the Fix

After running the migration, verify it worked:

```bash
cd backend
python -c "from app.database import engine; from sqlalchemy import inspect, text; conn = engine.connect(); result = conn.execute(text(\"SELECT character_maximum_length FROM information_schema.columns WHERE table_name='transactions' AND column_name='user_address'\")); print('user_address length:', result.fetchone()[0])"
```

You should see: `user_address length: 66`

---

## Quick Fix (Copy & Paste)

**For Supabase/PostgreSQL:**
```bash
cd backend
python scripts/update_user_address_column.py
```

**For SQLite (will recreate tables):**
```bash
cd backend
python -m app.init_db --drop
python -m app.init_db
```

Then restart your backend and try again!

