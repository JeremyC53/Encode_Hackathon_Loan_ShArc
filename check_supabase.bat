@echo off
echo ============================================================
echo Checking Supabase Database
echo ============================================================
echo.
cd backend
python -m scripts.check_supabase
echo.
pause

