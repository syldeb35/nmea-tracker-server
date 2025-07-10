@echo off
echo ===== Test de l'executable NMEA Tracker =====
echo.

if not exist "dist\nmea_tracker_server.exe" (
    echo ❌ Executable non trouve. Lancez d'abord build_windows.bat
    pause
    exit /b 1
)

echo 🚀 Lancement de l'executable...
echo    (Le serveur va demarrer, testez Ctrl+C pour l'arreter)
echo.

cd dist
nmea_tracker_server.exe

echo.
echo ✅ Test termine
pause
