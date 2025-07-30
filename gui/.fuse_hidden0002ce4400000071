#!/bin/bash
set -e
echo "🚀 Starting NMEA Server GUI..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/upgrade GUI requirements
echo "Installing GUI dependencies..."
pip install -q -r requirements_gui.txt

# Start GUI
echo "Starting GUI application..."
python gui_config.py