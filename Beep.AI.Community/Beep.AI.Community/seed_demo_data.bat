@echo off
REM Seed Demo Data Script for KOC A.I. Digital Campus
REM This will seed comprehensive demo data for the platform
REM
REM Usage:
REM   seed_demo_data.bat              - Normal seeding
REM   seed_demo_data.bat --reset      - Clear and reseed
REM   seed_demo_data.bat --users-only - Seed only users

cd /d "%~dp0"

echo.
echo ============================================================
echo   Seeding Demo Data for KOC A.I. Digital Campus
echo ============================================================
echo.

REM Check if embedded Python exists
if not exist "python-embedded\python.exe" (
    echo [ERROR] Embedded Python not found!
    echo Please run run.bat first to set up the environment.
    pause
    exit /b 1
)

REM Run the seeding script with embedded Python
python-embedded\python.exe scripts\seed_demo_data.py %*

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to seed demo data
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Demo data seeding completed!
pause

