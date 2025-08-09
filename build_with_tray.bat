@echo off
echo ========================================
echo  NMEA Server - Build avec System Tray
echo ========================================
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installé ou n'est pas dans le PATH
    pause
    exit /b 1
)

echo [1/5] Installation des dépendances pour le serveur principal...
pip install gevent flask flask-socketio flask-cors pyserial python-dotenv cryptography

echo.
echo [2/5] Installation des dépendances pour le system tray...
pip install pillow pystray psutil

echo.
echo [3/5] Installation de PyInstaller...
pip install pyinstaller

echo.
echo [4/5] Compilation du serveur NMEA principal...
if exist "build\nmea_server" rmdir /s /q "build\nmea_server"
if exist "dist\nmea_tracker_server.exe" del "dist\nmea_tracker_server.exe"

pyinstaller nmea_server.spec
if errorlevel 1 (
    echo ERREUR: Échec de la compilation du serveur principal
    pause
    exit /b 1
)

REM Copier l'exécutable dans le répertoire principal pour que le tray le trouve
if exist "dist\nmea_tracker_server.exe" (
    copy "dist\nmea_tracker_server.exe" "nmea_tracker_server.exe"
    echo ✓ Serveur principal compilé avec succès
) else (
    echo ERREUR: L'exécutable du serveur principal n'a pas été généré
    pause
    exit /b 1
)

echo.
echo [5/5] Compilation de l'application System Tray...
if exist "build\nmea_server_tray" rmdir /s /q "build\nmea_server_tray"
if exist "dist\nmea_server_tray.exe" del "dist\nmea_server_tray.exe"

pyinstaller nmea_server_tray.spec
if errorlevel 1 (
    echo ERREUR: Échec de la compilation de l'application tray
    pause
    exit /b 1
)

if exist "dist\nmea_server_tray.exe" (
    copy "dist\nmea_server_tray.exe" "nmea_server_tray.exe"
    echo ✓ Application System Tray compilée avec succès
) else (
    echo ERREUR: L'exécutable du system tray n'a pas été généré
    pause
    exit /b 1
)

echo.
echo ========================================
echo           COMPILATION TERMINÉE
echo ========================================
echo.
echo Fichiers générés:
echo - nmea_tracker_server.exe (serveur principal)
echo - nmea_server_tray.exe (gestionnaire system tray)
echo.
echo Pour utiliser:
echo 1. Lancez nmea_server_tray.exe
echo 2. L'icône apparaîtra dans la barre système
echo 3. Clic droit sur l'icône pour démarrer/arrêter le serveur
echo.
echo Appuyez sur une touche pour continuer...
pause >nul
