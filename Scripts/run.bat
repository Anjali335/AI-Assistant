@echo off
REM College Assistant - Quick Start Script for Windows

echo ========================================
echo College Assistant - Quick Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Checking Python installation...
python --version
echo.

echo [2/4] Installing dependencies...
cd Scripts
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [3/4] Running setup checks...
python setup.py
if errorlevel 1 (
    echo ERROR: Setup check failed
    pause
    exit /b 1
)
echo.

echo [4/4] Starting College Assistant...
echo.
echo ========================================
echo Server is starting...
echo ========================================
echo.
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
pause
