# Setup Instructions - Step by Step

## Prerequisites

1. **Python 3.8+** installed
   - Download from: https://www.python.org/downloads/
   - Make sure to check "Add Python to PATH" during installation

2. **Your Supabase Database Password**
   - Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
   - Settings → Database → Reset database password (if you don't know it)

## Quick Setup (Automated)

### Option 1: PowerShell Script (Windows)

```powershell
cd backend
.\setup.ps1
```

### Option 2: Manual Steps

#### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

#### Step 2: Create .env File

Create a file named `.env` in the `backend` folder with this content:

```env
DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

**Important**: Replace `[YOUR-PASSWORD]` with your actual Supabase database password!

#### Step 3: Initialize Database

```bash
python -m app.init_db
```

You should see: `✅ Database initialized successfully!`

#### Step 4: Create Sample Data (Optional)

```bash
python scripts/create_sample_data.py
```

This creates sample transactions and loans for testing.

#### Step 5: Start the Server

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs to see your API!

## Verify Setup

### Check Database Connection

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Table Editor** in the sidebar
3. You should see these tables:
   - `transactions`
   - `loan_history`
   - `credit_score_history`

### Test API

```bash
# Get all transactions
curl http://localhost:8000/api/transactions

# Or visit in browser
http://localhost:8000/api/transactions
```

## Troubleshooting

### "Python not found"
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH" during installation
- Restart your terminal after installation

### "Connection refused" or "Authentication failed"
- Check your `.env` file has the correct password
- Make sure you replaced `[YOUR-PASSWORD]` with your actual password
- Verify your password in Supabase Dashboard → Settings → Database

### "Module not found"
- Run: `pip install -r requirements.txt`
- Make sure you're in the `backend` directory

### "Table does not exist"
- Run: `python -m app.init_db`
- Check that your database connection is working

## Using SQLite Instead (For Testing)

If you want to test locally without Supabase, edit `.env`:

```env
DATABASE_URL=sqlite:///./loan_sharc.db
```

This creates a local SQLite database file. You can switch back to Supabase later by changing the `DATABASE_URL` back.

## Next Steps

Once setup is complete:

1. ✅ Database is connected
2. ✅ Tables are created
3. ✅ API is ready to use

You can now:
- Store transactions via API: `POST /api/transactions`
- Query transactions: `GET /api/transactions`
- View data in Supabase dashboard
- Integrate with your frontend

See `SUPABASE_WORKFLOW.md` for complete workflow documentation.

