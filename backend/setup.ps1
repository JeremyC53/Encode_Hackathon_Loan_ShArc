# PowerShell setup script for Supabase database
# Run this script: .\setup.ps1

Write-Host "🚀 Setting up Supabase Database..." -ForegroundColor Green
Write-Host ""

# Check if Python is available
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} else {
    Write-Host "❌ Python not found! Please install Python first." -ForegroundColor Red
    Write-Host "   Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found Python: $pythonCmd" -ForegroundColor Green
Write-Host ""

# Step 1: Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
& $pythonCmd -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 2: Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file..." -ForegroundColor Cyan
    $envContent = @"
# Database Configuration
# Replace [YOUR-PASSWORD] with your actual Supabase database password
# To get your password: Go to Supabase Dashboard → Settings → Database → Reset database password
DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Alternative: Use SQLite for local development (uncomment the line below and comment out the line above)
# DATABASE_URL=sqlite:///./loan_sharc.db
"@
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✅ Created .env file" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Edit .env file and replace [YOUR-PASSWORD] with your Supabase password!" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "✅ .env file already exists" -ForegroundColor Green
    Write-Host ""
}

# Step 3: Initialize database
Write-Host "🗄️  Initializing database..." -ForegroundColor Cyan
& $pythonCmd -m app.init_db
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to initialize database" -ForegroundColor Red
    Write-Host "   Make sure you've updated .env with your Supabase password" -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Database initialized" -ForegroundColor Green
Write-Host ""

# Step 4: Create sample data
Write-Host "📊 Creating sample data..." -ForegroundColor Cyan
$createSample = Read-Host "Create sample data? (y/n)"
if ($createSample -eq "y" -or $createSample -eq "Y") {
    & $pythonCmd scripts/create_sample_data.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Sample data created" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Sample data creation had issues (this is okay if database already has data)" -ForegroundColor Yellow
    }
} else {
    Write-Host "⏭️  Skipping sample data creation" -ForegroundColor Yellow
}
Write-Host ""

# Done!
Write-Host "=" * 60 -ForegroundColor Green
Write-Host "✅ Setup Complete!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. If you haven't already, update .env with your Supabase password" -ForegroundColor White
Write-Host "2. Start the API server: uvicorn app.main:app --reload" -ForegroundColor White
Write-Host "3. Visit http://localhost:8000/docs to see the API documentation" -ForegroundColor White
Write-Host ""

