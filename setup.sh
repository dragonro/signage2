#!/bin/bash

# Digital Signage Quick Setup Script
echo "🚀 Digital Signage Application - Quick Setup"
echo "==========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed."
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    mkdir -p data
fi

echo ""
echo "🔐 Admin Account Setup"
echo "====================="

# Check if database already exists
if [ -f "data/signage.db" ] || [ -f "signage.db" ]; then
    echo "⚠️  Database already exists. Would you like to reset admin credentials? (y/N)"
    read -r reset_admin
    if [[ $reset_admin =~ ^[Yy]$ ]]; then
        echo "📝 Setting new admin credentials..."
        echo -n "Enter new admin username (default: admin): "
        read -r admin_username
        admin_username=${admin_username:-admin}
        
        echo -n "Enter new admin password: "
        read -s admin_password
        echo ""
        
        if [ -z "$admin_password" ]; then
            echo "❌ Password cannot be empty!"
            exit 1
        fi
        
        # Create a Python script to update the admin credentials
        cat > temp_reset_admin.py << EOF
import sqlite3
import hashlib
import sys

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
    import os
    reset_admin(sys.argv[1], sys.argv[2])
EOF
        
        python3 temp_reset_admin.py "$admin_username" "$admin_password"
        rm temp_reset_admin.py
        
        echo "✅ Admin credentials have been updated!"
        echo ""
    fi
else
    echo "📝 Set up your admin account:"
    echo -n "Enter admin username (default: admin): "
    read -r admin_username
    admin_username=${admin_username:-admin}
    
    echo -n "Enter admin password: "
    read -s admin_password
    echo ""
    
    if [ -z "$admin_password" ]; then
        echo "❌ Password cannot be empty! Using default password 'admin123'"
        admin_password="admin123"
        echo "⚠️  Remember to change this after first login!"
    fi
    
    # Store credentials for first run
    export SIGNAGE_ADMIN_USER="$admin_username"
    export SIGNAGE_ADMIN_PASS="$admin_password"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "🌟 To start the application:"
echo "   ./start.sh"
echo ""
echo "🌐 Access at: http://localhost:5000"
echo "🔑 Login with your configured credentials"
echo ""
echo "📚 Read README.md for full documentation"
