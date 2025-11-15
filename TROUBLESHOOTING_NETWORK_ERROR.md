# Troubleshooting NetworkError

## ✅ Fixed: API URL Configuration

The issue was that the API utility was using absolute URLs (`http://localhost:8000`) which bypassed the Vite proxy. 

**Fixed:** Now uses relative paths (`/api/transactions`) that go through the Vite proxy configuration.

---

## If You Still See NetworkError

### 1. Make Sure Backend is Running

Check if backend is running on port 8000:
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Or manually test the backend
curl http://localhost:8000/api/health
```

**If backend is not running:**
```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the batch file
start_backend.bat
```

---

### 2. Make Sure Frontend Dev Server is Running

The frontend must be running for the proxy to work:
```bash
cd frontend
npm run dev
```

**Or use:**
```bash
start_frontend.bat
```

**Or start both:**
```bash
start_all.bat
```

---

### 3. Check Browser Console

Open Developer Tools (F12) → Console tab and look for:
- CORS errors
- Connection refused errors
- 404 errors

Common errors:
- **"Failed to fetch"** - Backend not running or wrong URL
- **"CORS error"** - Backend CORS settings or proxy not working
- **"404 Not Found"** - Wrong API endpoint or backend route not registered

---

### 4. Verify Vite Proxy is Working

The `frontend/vite.config.ts` should have:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

**To test the proxy:**
1. Open browser: http://localhost:5173
2. Open Developer Tools (F12) → Network tab
3. Try making a borrow/repay request
4. Check if the request goes to `/api/transactions` (relative path)
5. The proxy should forward it to `http://localhost:8000/api/transactions`

---

### 5. Restart Dev Servers

Sometimes the proxy needs a restart:

1. **Stop both servers** (Ctrl+C in their windows)
2. **Start backend first:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```
3. **Wait a few seconds**, then **start frontend:**
   ```bash
   cd frontend
   npm run dev
   ```

---

### 6. Check Backend CORS Settings

Make sure `backend/app/main.py` has CORS enabled:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 7. Test API Directly

Test if the backend API works directly:

**Borrow Request:**
```bash
curl -X POST http://localhost:8000/api/transactions \
  -H "Content-Type: application/json" \
  -d "{\"user_address\":\"0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0a\",\"transaction_type\":\"borrow\",\"amount\":1000,\"currency\":\"USDC\",\"transaction_timestamp\":\"2024-01-01T00:00:00Z\",\"status\":\"pending\"}"
```

**Health Check:**
```bash
curl http://localhost:8000/api/health
```

---

### 8. Check Firewall/Antivirus

Sometimes firewall or antivirus blocks localhost connections:
- Check Windows Firewall settings
- Temporarily disable antivirus to test
- Make sure `localhost` is not blocked

---

### 9. Use Browser Network Tab

1. Open Developer Tools (F12)
2. Go to **Network** tab
3. Try making a borrow/repay request
4. Look for the `/api/transactions` request
5. Click on it to see:
   - **Request URL** - Should be `/api/transactions` (relative)
   - **Status** - Should be 200 or 201 if successful
   - **Response** - Should show the transaction data or error message

---

## Quick Fix Checklist

✅ Backend is running on port 8000  
✅ Frontend is running on port 5173  
✅ Vite proxy is configured in `vite.config.ts`  
✅ API utility uses relative paths (`/api/...`)  
✅ Backend CORS is enabled  
✅ No firewall blocking localhost  
✅ Browser console shows detailed error messages  

---

## If Still Not Working

1. **Clear browser cache** (Ctrl+Shift+Delete)
2. **Try a different browser** (Chrome, Firefox, Edge)
3. **Check backend logs** for error messages
4. **Check frontend console** for detailed error messages
5. **Restart your computer** (sometimes helps with port conflicts)

---

## Current Status

✅ **Fixed:** API utility now uses relative paths  
✅ **Backend is running:** Port 8000 is active  
✅ **Proxy configured:** Vite proxy is set up correctly  

The NetworkError should be resolved. Try using the Borrow & Repay functionality again!

