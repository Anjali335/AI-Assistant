#!/bin/bash
# College Assistant - Quick Start Script for Linux/Mac

echo "========================================"
echo "College Assistant - Quick Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/"
    exit 1
fi

echo "[1/4] Checking Python installation..."
python3 --version
echo ""

echo "[2/4] Installing dependencies..."
cd Scripts
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

echo "[3/4] Running setup checks..."
python3 setup.py
if [ $? -ne 0 ]; then
    echo "ERROR: Setup check failed"
    exit 1
fi
echo ""

echo "[4/4] Starting College Assistant..."
echo ""
echo "========================================"
echo "Server is starting..."
echo "========================================"
echo ""
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
