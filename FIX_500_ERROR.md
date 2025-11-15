# Fixed: 500 Internal Server Error

## ✅ Changes Made

### 1. Better Error Handling in Backend
- Added comprehensive try-except blocks
- Added database rollback on errors
- Better error messages with details
- Made `transaction_timestamp` optional (defaults to current time)

### 2. Validation Improvements
- User address format validation
- Better timestamp parsing with fallbacks
- Default values for optional fields

---

## How to Test

1. **Restart the Backend Server**
   ```bash
   # Stop the backend (Ctrl+C)
   # Then restart it
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Try the Borrow/Repay Again**
   - Refresh your browser
   - Try making a borrow or repay request
   - Check the error message - it should now be more descriptive

---

## Check Backend Logs

When you get a 500 error, **check the backend console** for detailed error messages. The backend now prints:
- Full traceback of errors
- What went wrong (database connection, validation, etc.)

**Look for lines like:**
```
Error creating transaction: [traceback details]
```

---

## Common 500 Error Causes

### 1. Database Not Initialized
**Solution:**
```bash
cd backend
python -m app.init_db
```

### 2. Database Connection Issue
**Check your `.env` file:**
```bash
cd backend
# Make sure DATABASE_URL is set correctly
cat .env
```

**For Supabase:**
```env
DATABASE_URL=postgresql://postgres.xxx:[PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

**For SQLite (local testing):**
```env
DATABASE_URL=sqlite:///./loan_sharc.db
```

### 3. Missing Tables
**Initialize the database:**
```bash
cd backend
python -m app.init_db
```

### 4. Invalid Data Format
The backend now validates:
- User address must start with "0x" and be at least 10 characters
- Amount must be a number
- Timestamp is optional (defaults to current time)

---

## Debug Steps

### Step 1: Check Backend Console
When you make a request, watch the backend console window. You should see:
- The request being received
- Any error messages
- Full traceback if something fails

### Step 2: Test API Directly
Test the API with curl to see the exact error:

```bash
curl -X POST http://localhost:8000/api/transactions ^
  -H "Content-Type: application/json" ^
  -d "{\"user_address\":\"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0a\",\"transaction_type\":\"borrow\",\"amount\":1000,\"currency\":\"USDC\",\"transaction_timestamp\":\"2024-01-01T00:00:00Z\",\"status\":\"pending\"}"
```

### Step 3: Check Database Connection
```bash
cd backend
python -c "from app.database import engine; print('Testing connection...'); engine.connect(); print('Connection OK!')"
```

### Step 4: Verify Tables Exist
```bash
cd backend
python -c "from app.models import Transaction; from app.database import engine; from sqlalchemy import inspect; inspector = inspect(engine); tables = inspector.get_table_names(); print('Tables:', tables); print('transactions table exists:', 'transactions' in tables)"
```

---

## What Should Happen Now

With the improved error handling:

1. **If there's a validation error** (e.g., invalid address):
   - You'll get a 400 error with a clear message
   - Example: "Invalid user address format: 0x123"

2. **If there's a database error**:
   - Backend will print the full error in the console
   - You'll get a 500 error with a descriptive message
   - Database transaction will be rolled back

3. **If everything works**:
   - You'll get a 201 Created response
   - Transaction ID will be returned
   - Data will be saved to Supabase

---

## Next Steps

1. ✅ **Restart your backend server** to load the new error handling
2. ✅ **Try the borrow/repay request again**
3. ✅ **Check the backend console** for any error details
4. ✅ **If you still get errors**, the console will show exactly what went wrong

The improved error messages should help identify the exact issue!

