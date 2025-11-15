# Switch from SQLite to Supabase

## Current Issue
You're using SQLite (local file) instead of Supabase. That's why you see data in localhost but not in Supabase dashboard.

## Quick Fix

### Step 1: Set up .env file

Run this script:
```bash
python setup_supabase_env.py
```

It will:
- Ask for your Supabase connection string
- Create/update the `.env` file
- Set up the correct DATABASE_URL

**OR manually create `.env` file:**

1. Create a file named `.env` in the `backend` folder
2. Add this content (replace `[YOUR-PASSWORD]` with your actual password):

```env
DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

**To get your password:**
1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Settings** → **Database**
3. Click **Reset database password** (if you don't know it)
4. Copy the password

### Step 2: Restart Your Server

**IMPORTANT:** You must restart your server for the `.env` file to be loaded!

```bash
# Stop your current server (Ctrl+C)
# Then restart:
uvicorn app.main:app --reload
```

### Step 3: Verify Connection

```bash
python check_database_connection.py
```

You should now see:
```
✅ Using PostgreSQL (Supabase)
✅ Database connected!
```

### Step 4: Initialize Tables in Supabase

Since you were using SQLite before, you need to create tables in Supabase:

```bash
python -m app.init_db
```

### Step 5: Add Data to Supabase

Now add a transaction to Supabase:

```bash
python scripts/simulate_transaction.py
```

### Step 6: Verify in Supabase Dashboard

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Table Editor**
3. Click **transactions** table
4. You should see your data!

## Troubleshooting

### "Connection refused" or "Authentication failed"
- Check your password in `.env` file
- Make sure you replaced `[YOUR-PASSWORD]` with actual password
- Verify password in Supabase dashboard

### Still showing SQLite
- Make sure `.env` file is in the `backend` folder
- Restart your server (environment variables are loaded at startup)
- Check `.env` file has correct format (no extra spaces)

### "Table does not exist"
- Run: `python -m app.init_db`
- This creates tables in Supabase

## Summary

1. ✅ Create `.env` file with Supabase connection string
2. ✅ Restart server
3. ✅ Initialize tables: `python -m app.init_db`
4. ✅ Add data: `python scripts/simulate_transaction.py`
5. ✅ Check Supabase dashboard

After this, all new data will go to Supabase!

