@echo off
title Atlas Obscura Offline Explorer & Region Selector
cls
echo =======================================================================
echo               Atlas Obscura Offline Explorer
echo =======================================================================
echo.
echo Starting local Web Server and Region Selector Map...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.8+ and try again.
    pause
    exit /b
)

:: Wait 1 second and open default browser to localhost:8000
start "" "http://localhost:8000"

echo [SUCCESS] Web App launched in your browser: http://localhost:8000
echo.
echo Press Ctrl+C in this window to stop the server when done.
echo =======================================================================
echo.

python server.py
pause
