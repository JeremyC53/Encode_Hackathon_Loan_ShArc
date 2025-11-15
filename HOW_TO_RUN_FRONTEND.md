# How to Run the Frontend

Quick guide to run and check the frontend yourself.

## Option 1: Start Everything (Easiest) ⭐

This starts both backend and frontend in separate windows:

```bash
start_all.bat
```

**What happens:**
- Backend starts on `http://localhost:8000`
- Frontend starts on `http://localhost:5173`
- Two separate command windows will open (servers keep running)

**Then:**
1. Open your browser to: **http://localhost:5173**
2. Login with:
   - Email: `demo@hack.com`
   - Password: `hackathon`

---

## Option 2: Start Frontend Only

If the backend is already running:

```bash
start_frontend.bat
```

Or manually:
```bash
cd frontend
npm run dev
```

**Access at:** http://localhost:5173

---

## Option 3: Start Backend Only

If you need to start just the backend:

```bash
start_backend.bat
```

Or manually:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Access at:** http://localhost:8000
**API Docs at:** http://localhost:8000/docs

---

## Prerequisites (One-time Setup)

If you haven't installed dependencies yet:

### 1. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 3. Setup Database (One-time)
```bash
cd backend
python -m app.init_db
```

---

## What to Check

### 1. Frontend is Running ✅
- Open: http://localhost:5173
- You should see the login screen
- Login with `demo@hack.com` / `hackathon`

### 2. Backend is Running ✅
- Open: http://localhost:8000/docs
- You should see the API documentation (Swagger UI)
- Or check: http://localhost:8000/api/health

### 3. Find Transfer Functionality
Once logged in, check:
- **Dashboard** screen - Look for transfer/send buttons
- **Loans** screen - Check for repayment/transfer options
- **Settings** screen - May have transfer options
- Check browser console (F12) for any errors

### 4. Test Transfer Recording
If you find transfer functionality:
1. Open browser Developer Tools (F12)
2. Go to Console tab
3. Make a transfer in the UI
4. Check for API calls to `/api/transactions`
5. Verify in Supabase dashboard that the transaction was recorded

---

## Troubleshooting

### Frontend won't start?
```bash
# Make sure you're in the frontend directory
cd frontend

# Check if node_modules exists
# If not, install dependencies:
npm install

# Try starting again
npm run dev
```

### Backend won't start?
```bash
# Make sure you're in the backend directory
cd backend

# Check if .env file exists
# If not, create it:
python create_env.py

# Make sure database is initialized:
python -m app.init_db

# Try starting again
python -m uvicorn app.main:app --reload
```

### Port already in use?
- Frontend port 5173: Change in `frontend/vite.config.ts`
- Backend port 8000: Change in the uvicorn command or `start_backend.bat`

### Can't connect to backend?
- Make sure backend is running on port 8000
- Check `frontend/vite.config.ts` has the proxy configuration
- Check browser console for CORS errors

---

## Useful URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## Next Steps After Running

1. ✅ Verify frontend loads correctly
2. 🔍 Look for transfer functionality in the UI
3. 📝 If you find it, check the integration guide: `TRANSFER_INTEGRATION_GUIDE.md`
4. 🧪 Test making a transfer
5. ✅ Verify it's recorded in Supabase

