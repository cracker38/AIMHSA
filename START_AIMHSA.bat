@echo off
cd /d "%~dp0"
echo Make sure no other AIMHSA server is running (Ctrl+C in that window first).
echo.
echo Starting AIMHSA from: %CD%
python run_aimhsa.py
pause
