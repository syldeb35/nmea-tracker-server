@echo off
echo ========================================
echo  NMEA Server - Build with System Tray
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in the PATH
    pause
    exit /b 1
)

echo [1/5] Installing dependencies for the main server...
pip install gevent flask flask-socketio flask-cors pyserial python-dotenv cryptography

echo.
echo [2/5] Installing dependencies for the system tray...
pip install pillow pystray psutil

echo.
echo [3/5] Installing PyInstaller...
pip install pyinstaller

echo.
echo [4/5] Compiling the main NMEA server...
if exist "build\nmea_server" rmdir /s /q "build\nmea_server"
if exist "dist\nmea_tracker_server.exe" del "dist\nmea_tracker_server.exe"

pyinstaller nmea_server.spec
if errorlevel 1 (
    echo ERROR: Failed to compile the main server
    pause
    exit /b 1
)

REM Copy the executable to the main directory so the tray can find it
if exist "dist\nmea_tracker_server.exe" (
    copy "dist\nmea_tracker_server.exe" "nmea_tracker_server.exe"
    echo ✓ Main server compiled successfully
) else (
    echo ERROR: The main server executable was not generated
    pause
    exit /b 1
)

echo.
echo [5/5] Compiling the System Tray application...
if exist "build\nmea_server_tray" rmdir /s /q "build\nmea_server_tray"
if exist "dist\nmea_server_tray.exe" del "dist\nmea_server_tray.exe"

pyinstaller nmea_server_tray.spec
if errorlevel 1 (
    echo ERROR: Failed to compile the tray application
    pause
    exit /b 1
)

if exist "dist\nmea_server_tray.exe" (
    copy "dist\nmea_server_tray.exe" "nmea_server_tray.exe"
    echo ✓ System Tray application compiled successfully
) else (
    echo ERROR: The system tray executable was not generated
    pause
    exit /b 1
)

echo.
echo ========================================
echo           BUILD COMPLETE
echo ========================================
echo.
echo Generated files:
echo - nmea_tracker_server.exe (main server)
echo - nmea_server_tray.exe (system tray manager)
echo.
echo How to use:
echo 1. Launch nmea_server_tray.exe
echo 2. The icon will appear in the system tray
echo 3. Right-click the icon to start/stop the server
echo.
echo Press any key to continue...
pause >nul
