@echo off
REM College Assistant - Run with correct Python version

set PYTHON_PATH=C:\Users\RAGHAV\AppData\Local\Programs\Python\Python313\python.exe

if not exist "%PYTHON_PATH%" (
    echo.
    echo ERROR: Python 3.13 not found at: %PYTHON_PATH%
    echo.
    echo Please install Python 3.13 from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM Run app.py with the correct Python
"%PYTHON_PATH%" app.py
