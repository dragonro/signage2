# Digital Signage Startup Script for Windows PowerShell

Write-Host "Digital Signage Server - Starting..." -ForegroundColor Green

# Check if Python 3 is installed
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $majorVersion = [int]$matches[1]
        $minorVersion = [int]$matches[2]
        
        if ($majorVersion -lt 3 -or ($majorVersion -eq 3 -and $minorVersion -lt 8)) {
            Write-Host "Error: Python 3.8 or higher is required. Found: $pythonVersion" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "Error: Python 3 is not installed. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install/update dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
if (!(Test-Path "static\uploads")) {
    New-Item -ItemType Directory -Path "static\uploads" -Force | Out-Null
}
if (!(Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
}

# Set environment variables
$env:FLASK_APP = "app.py"

# Check if running in development or production
if ($args[0] -eq "prod" -or $args[0] -eq "production") {
    $env:FLASK_ENV = "production"
    Write-Host "Starting in production mode..." -ForegroundColor Green
} else {
    $env:FLASK_ENV = "development"
    Write-Host "Starting in development mode..." -ForegroundColor Green
    Write-Host "Use '.\start.ps1 prod' for production mode" -ForegroundColor Cyan
}

# Start the application
Write-Host "Starting Digital Signage Server..." -ForegroundColor Green
Write-Host "Access the application at: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow

python app.py
