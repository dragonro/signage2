#!/bin/bash

# Digital Signage Startup Script for Linux/macOS
echo "Digital Signage Server - Starting..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p static/uploads data

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Check if running in development or production
if [ "$1" = "prod" ] || [ "$1" = "production" ]; then
    export FLASK_ENV=production
    echo "Starting in production mode..."
else
    echo "Starting in development mode..."
    echo "Use './start.sh prod' for production mode"
fi

# Start the application
echo "Starting Digital Signage Server..."
echo "Access the application at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"

python3 app.py
