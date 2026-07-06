# College Assistant - Auto Setup Script for Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "College Assistant - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check if Python is installed
Write-Host "Checking for Python installation..." -ForegroundColor Yellow

$pythonInstalled = $false
try {
    $version = python --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Python found: $version" -ForegroundColor Green
        $pythonInstalled = $true
    }
}
catch {
    # Try python3
    try {
        $version = python3 --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python3 found: $version" -ForegroundColor Green
            $pythonInstalled = $true
        }
    }
    catch {
        Write-Host ""
    }
}

if (-not $pythonInstalled) {
    Write-Host "❌ Python is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python from:" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Yellow
    Write-Host "  1. Download Python 3.9 or later" -ForegroundColor White
    Write-Host "  2. Run the installer" -ForegroundColor White
    Write-Host "  3. CHECK: 'Add Python to PATH'" -ForegroundColor Green
    Write-Host "  4. Complete installation" -ForegroundColor White
    Write-Host "  5. Re-run this script" -ForegroundColor White
    Write-Host ""
    Read-Host "Press Enter to open Python download page"
    Start-Process "https://www.python.org/downloads/"
    exit 1
}

Write-Host ""
Write-Host "✓ Python is installed" -ForegroundColor Green
Write-Host ""

# Step 2: Install dependencies
Write-Host "Installing required packages..." -ForegroundColor Yellow
Write-Host "This may take 2-3 minutes..." -ForegroundColor Cyan
Write-Host ""

$packages = @(
    "flask",
    "openai",
    "chardet",
    "faiss-cpu",
    "sentence-transformers",
    "numpy",
    "torch"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Gray
    python -m pip install $package -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $package installed" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠ Warning: Failed to install $package" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 3: Start the server
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting College Assistant..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server is running at:" -ForegroundColor Green
Write-Host "  http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening browser..." -ForegroundColor Yellow
Write-Host ""

# Open browser
Start-Sleep -Seconds 2
Start-Process "http://localhost:5000"

# Start the app
Write-Host "Starting Flask server..." -ForegroundColor Cyan
python app.py
