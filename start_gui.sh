#!/bin/bash
echo "🚀 Starting NMEA Server GUI..."
if [ -f "gui_config.py" ]; then
    echo "Starting Qt GUI..."
    python3 gui_config.py
else
    echo "❌ gui_config.py not found"
    echo "Starting web interface instead..."
    python3 nmea_server.py
fi
