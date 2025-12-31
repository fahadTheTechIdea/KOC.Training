@echo off
REM Reset database script for KOC A.I. Digital Campus
REM This will delete the database and setup state

echo.
echo ============================================================
echo Database Reset Script
echo ============================================================
echo.
echo WARNING: This will delete the database and all data!
echo Make sure the Flask application is STOPPED before running this.
echo.
pause

python-embedded\python.exe reset_database.py

echo.
pause