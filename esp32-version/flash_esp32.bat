@echo off
echo ===== NMEA Tracker ESP32 - Flash Tool =====
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found! Please install Python first.
    goto :error
)

REM Check for build script
if not exist "build_esp32.py" (
    echo ERROR: build_esp32.py not found!
    goto :error
)

echo [1/3] Installing dependencies...
pip install esptool adafruit-ampy pyserial

echo [2/3] Building and flashing ESP32...
python build_esp32.py %*

echo [3/3] Flash completed!
echo.
echo Connect to ESP32 WiFi: NMEA_Tracker_ESP32
echo Web interface: http://192.168.4.1
echo.

pause
goto :end

:error
echo.
echo Build failed - check errors above
echo.
pause

:end
