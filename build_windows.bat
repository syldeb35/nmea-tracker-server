@echo off
chcp 65001 >nul
echo ===== NMEA Tracker Server - Build Script =====
echo.

REM Check prerequisites
echo [0/5] Checking prerequisites...
if not exist "cert.pem" (
    echo ERROR: cert.pem missing!
    echo Place your SSL certificates in the project directory.
    goto :error
)
if not exist "key.pem" (
    echo ERROR: key.pem missing!
    echo Place your SSL certificates in the project directory.
    goto :error
)
echo SSL certificates found

REM Create build directory if it doesn't exist
if not exist "dist" mkdir dist
if not exist "build" mkdir build

echo [1/5] Cleaning previous builds...
if exist "dist\nmea_tracker_server.exe" del "dist\nmea_tracker_server.exe"
if exist "build" rmdir /s /q "build"

echo [2/5] Installing dependencies...
pip install -r requirements.txt

echo [3/5] Checking templates...
if not exist "templates\config.html" (
    echo ERROR: templates/config.html missing!
    goto :error
)
if not exist "templates\index.html" (
    echo ERROR: templates/index.html missing!
    goto :error
)
echo Templates found

echo [4/5] Creating executable with PyInstaller...
pyinstaller nmea_server.spec --clean --noconfirm

echo [5/5] Verifying build...
if exist "dist\nmea_tracker_server.exe" (
    echo.
    echo BUILD SUCCESSFUL !
    echo.
    echo Executable created: dist\nmea_tracker_server.exe
    echo File size:
    for %%I in ("dist\nmea_tracker_server.exe") do echo   %%~zI bytes (~%%~zI / 1024 / 1024 MB)
    echo.
    echo Files included in executable:
    echo   - Main Python code
    echo   - HTML templates (config.html, index.html, favicon.svg)
    echo   - SSL certificates (cert.pem, key.pem)
    echo   - Configuration (.env)
    echo   - Custom icon (icon.ico)
    echo   - Python runtime + dependencies
    echo.
    echo To test: cd dist ^&^& nmea_tracker_server.exe
    echo Web interface: https://localhost:5000/config.html
    echo.
    goto :success
) else (
    echo.
    echo BUILD FAILED
    echo Check errors above.
    echo.
    goto :end
)

:success
echo Press any key to continue...
pause >nul
goto :end

:error
echo.
echo BUILD IMPOSSIBLE - Prerequisites error
echo.
pause >nul

:end
