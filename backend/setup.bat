@echo off
echo 🚀 Setting up Supabase Database...
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python first.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Found Python
echo.

REM Step 1: Install dependencies
echo 📦 Installing dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed
echo.

REM Step 2: Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file...
    (
        echo # Database Configuration
        echo # Replace [YOUR-PASSWORD] with your actual Supabase database password
        echo DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
    ) > .env
    echo ✅ Created .env file
    echo ⚠️  IMPORTANT: Edit .env file and replace [YOUR-PASSWORD] with your Supabase password!
    echo.
) else (
    echo ✅ .env file already exists
    echo.
)

REM Step 3: Initialize database
echo 🗄️  Initializing database...
python -m app.init_db
if %errorlevel% neq 0 (
    echo ❌ Failed to initialize database
    echo    Make sure you've updated .env with your Supabase password
    pause
    exit /b 1
)
echo ✅ Database initialized
echo.

REM Step 4: Create sample data
set /p createSample="Create sample data? (y/n): "
if /i "%createSample%"=="y" (
    echo 📊 Creating sample data...
    python scripts/create_sample_data.py
    if %errorlevel% equ 0 (
        echo ✅ Sample data created
    ) else (
        echo ⚠️  Sample data creation had issues (this is okay if database already has data)
    )
) else (
    echo ⏭️  Skipping sample data creation
)
echo.

REM Done!
echo ============================================================
echo ✅ Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. If you haven't already, update .env with your Supabase password
echo 2. Start the API server: uvicorn app.main:app --reload
echo 3. Visit http://localhost:8000/docs to see the API documentation
echo.
pause

