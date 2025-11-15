# Quick Start Guide

Get the Loan ShArc app running in 3 steps!

## Step 1: Setup (One-time)

Run the setup script:

```bash
setup.bat
```

This will:
- ✅ Install backend Python dependencies
- ✅ Install frontend Node.js dependencies

## Step 2: Configure Database

Create `backend/.env` file with your Supabase connection:

```env
DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
```

Get your password from: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd → Settings → Database

Then initialize the database:

```bash
cd backend
python -m app.init_db
```

## Step 3: Start the App

Run:

```bash
start_all.bat
```

This starts both:
- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173

## Access the App

Open your browser and go to:

**http://localhost:5173**

Login with:
- Email: `demo@hack.com`
- Password: `hackathon`

## Manual Start (Alternative)

If you prefer to start servers separately:

**Terminal 1 - Backend:**
```bash
cd backend
python -m uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Troubleshooting

### "Python not found"
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH"

### "Node.js not found"
- Install Node.js from https://nodejs.org/

### "Database connection failed"
- Check your `.env` file has the correct Supabase password
- Make sure you ran `python -m app.init_db`

### Frontend can't connect to backend
- Make sure backend is running on port 8000
- Check browser console for errors

## What You'll See

1. **Login Screen** - Enter demo credentials
2. **Dashboard** - Overview of loans and balance
3. **Loans** - List of all loans
4. **Settings** - Connect accounts (Google, Fiverr, Upwork)

Enjoy! 🚀

