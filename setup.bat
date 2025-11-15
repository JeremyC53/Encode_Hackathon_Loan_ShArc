@echo off
echo ============================================================
echo Loan ShArc Setup
echo ============================================================
echo.

echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python first.
    pause
    exit /b 1
)
echo OK: Python found

echo.
echo [2/4] Installing Backend Dependencies...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)
cd ..
echo OK: Backend dependencies installed

echo.
echo [3/4] Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js not found! Please install Node.js first.
    pause
    exit /b 1
)
echo OK: Node.js found

echo.
echo [4/4] Installing Frontend Dependencies...
cd frontend
if not exist node_modules (
    npm install
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
    echo OK: Frontend dependencies installed
) else (
    echo OK: Frontend dependencies already installed
)
cd ..

echo.
echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Create backend/.env file with your Supabase connection string
echo 2. Run: python -m app.init_db (in backend folder)
echo 3. Run: start_all.bat (to start both servers)
echo.
pause

