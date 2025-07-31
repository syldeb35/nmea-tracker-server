@echo off
echo 🚀 Starting NMEA Server GUI...

if exist gui_config.py (
    echo Starting Qt GUI...
    python gui_config.py
) else (
    echo gui_config.py not found
    echo Starting web interface instead...
    python nmea_server.py
)
pause
