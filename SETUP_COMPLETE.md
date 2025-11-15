# 🚀 Setup Complete - Ready to Run!

I've set up everything for you. Here's what to do:

## Quick Start (3 Commands)

### 1. Install Dependencies (One-time)

```bash
setup.bat
```

### 2. Create Database Connection

```bash
cd backend
python create_env.py
```

Enter your Supabase password when prompted.

Then initialize the database:

```bash
python -m app.init_db
```

### 3. Start the App

```bash
cd ..
start_all.bat
```

## Access the App

Open your browser to:

**http://localhost:5173**

Login with:
- **Email**: `demo@hack.com`
- **Password**: `hackathon`

## What's Running

- ✅ **Backend API**: http://localhost:8000
- ✅ **Frontend UI**: http://localhost:5173
- ✅ **API Docs**: http://localhost:8000/docs

## Files Created

- `setup.bat` - Install all dependencies
- `start_all.bat` - Start both servers
- `start_backend.bat` - Start backend only
- `start_frontend.bat` - Start frontend only
- `backend/create_env.py` - Helper to create .env file

## Troubleshooting

### If setup.bat fails:
- Make sure Python is installed: https://www.python.org/downloads/
- Make sure Node.js is installed: https://nodejs.org/

### If database connection fails:
- Check your Supabase password in `backend/.env`
- Make sure you ran `python -m app.init_db`

### If frontend doesn't load:
- Make sure backend is running on port 8000
- Check browser console for errors

## Next Steps

Once the app is running:
1. Login with demo credentials
2. Explore the Dashboard
3. Check Loans screen
4. Try Settings to connect accounts

Enjoy! 🎉

