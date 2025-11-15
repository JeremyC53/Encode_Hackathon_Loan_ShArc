@echo off
echo ============================================================
echo Database Fix and Setup
echo ============================================================
echo.
echo This script will:
echo 1. Fix the metadata column issue
echo 2. Create sample data
echo.
echo Make sure you're in your conda (base) environment!
echo.
pause

python fix_and_setup.py

pause

