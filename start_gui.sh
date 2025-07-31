#!/bin/bash
echo "🚀 Starting NMEA Server GUI..."

# Check if GUI config exists
if [ -f "gui_config.py" ]; then
    echo "Starting Qt GUI..."
    python gui_config.py
else
    echo "❌ gui_config.py not found"
    echo "Starting web interface instead..."
    python nmea_server.py
fi
