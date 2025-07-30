@echo off
REM filepath: start_gui.bat
echo Starting NMEA Server GUI...

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating Python virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/upgrade GUI requirements
echo Installing GUI dependencies...
pip install -q -r requirements_gui.txt

REM Start GUI
echo Starting GUI application...
python gui_config.py

pause