# Digital Signage Quick Setup Script (PowerShell)
Write-Host "🚀 Digital Signage Application - Quick Setup" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python 3 is installed
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
    } else {
        throw "Python not found"
    }
} catch {
    Write-Host "❌ Error: Python 3 is not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher and try again." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" -Force | Out-Null
}

Write-Host ""
Write-Host "🔐 Admin Account Setup" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan

# Check if database already exists
if ((Test-Path "data\signage.db") -or (Test-Path "signage.db")) {
    Write-Host "⚠️  Database already exists. Would you like to reset admin credentials? (y/N)" -ForegroundColor Yellow
    $resetAdmin = Read-Host
    if ($resetAdmin -match "^[Yy]$") {
        Write-Host "📝 Setting new admin credentials..." -ForegroundColor Yellow
        $adminUsername = Read-Host "Enter new admin username (default: admin)"
        if ([string]::IsNullOrEmpty($adminUsername)) {
            $adminUsername = "admin"
        }
        
        $adminPassword = Read-Host "Enter new admin password" -AsSecureString
        $adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword))
        
        if ([string]::IsNullOrEmpty($adminPasswordPlain)) {
            Write-Host "❌ Password cannot be empty!" -ForegroundColor Red
            exit 1
        }
        
        # Create a Python script to update the admin credentials
        $resetScript = @"
import sqlite3
import hashlib
import sys
import os

def reset_admin(username, password):
    db_file = 'data/signage.db' if os.path.exists('data/signage.db') else 'signage.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Delete existing admin users and create new one
    cursor.execute('DELETE FROM users WHERE username = ?', (username,))
    cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
    
    conn.commit()
    conn.close()
    print(f"✅ Admin credentials updated for user: {username}")

if __name__ == "__main__":
    reset_admin(sys.argv[1], sys.argv[2])
"@
        
        $resetScript | Out-File -FilePath "temp_reset_admin.py" -Encoding UTF8
        python temp_reset_admin.py $adminUsername $adminPasswordPlain
        Remove-Item "temp_reset_admin.py"
        
        Write-Host "✅ Admin credentials have been updated!" -ForegroundColor Green
        Write-Host ""
    }
} else {
    Write-Host "📝 Set up your admin account:" -ForegroundColor Yellow
    $adminUsername = Read-Host "Enter admin username (default: admin)"
    if ([string]::IsNullOrEmpty($adminUsername)) {
        $adminUsername = "admin"
    }
    
    $adminPassword = Read-Host "Enter admin password" -AsSecureString
    $adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword))
    
    if ([string]::IsNullOrEmpty($adminPasswordPlain)) {
        Write-Host "❌ Password cannot be empty! Using default password 'admin123'" -ForegroundColor Red
        $adminPasswordPlain = "admin123"
        Write-Host "⚠️  Remember to change this after first login!" -ForegroundColor Yellow
    }
    
    # Store credentials for first run
    $env:SIGNAGE_ADMIN_USER = $adminUsername
    $env:SIGNAGE_ADMIN_PASS = $adminPasswordPlain
}

Write-Host ""
Write-Host "✨ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌟 To start the application:" -ForegroundColor Cyan
Write-Host "   .\start.ps1" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Access at: http://localhost:5000" -ForegroundColor Cyan
Write-Host "🔑 Login with your configured credentials" -ForegroundColor Cyan
Write-Host ""
Write-Host "📚 Read README.md for full documentation" -ForegroundColor Cyan
