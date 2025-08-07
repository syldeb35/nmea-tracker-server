@echo off
REM =============================================================================
REM Compilation Script for NMEA Tracker Server Enhanced
REM Génère deux versions : console et system tray
REM =============================================================================

echo.
echo ============================================================================
echo NMEA Tracker Server Enhanced - Compilation
echo ============================================================================
echo.

REM Vérification de Python et PyInstaller
echo [1/4] Vérification de l'environnement...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installé ou non trouvé dans le PATH
    pause
    exit /b 1
)

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] PyInstaller n'est pas installé
    echo Installation en cours...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo [ERREUR] Impossible d'installer PyInstaller
        pause
        exit /b 1
    )
)

REM Installation des dépendances si nécessaire
echo [2/4] Vérification des dépendances...
pip install gevent flask flask-socketio flask-cors pyserial python-dotenv pystray pillow >nul 2>&1

REM Nettoyage des anciens builds
echo [3/4] Nettoyage des anciens builds...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Compilation version console
echo [4/4] Compilation en cours...
echo.
echo [4a/4] Version CONSOLE (nmea_tracker_server_enhanced.exe)...
pyinstaller --clean --noconfirm nmea_server_enhanced.spec
if %errorlevel% neq 0 (
    echo [ERREUR] Échec de la compilation version console
    pause
    exit /b 1
)

echo [4b/4] Version SYSTEM TRAY (nmea_tracker_server_tray.exe)...
pyinstaller --clean --noconfirm nmea_server_enhanced_tray.spec
if %errorlevel% neq 0 (
    echo [ERREUR] Échec de la compilation version tray
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo COMPILATION TERMINÉE AVEC SUCCÈS !
echo ============================================================================
echo.
echo Exécutables générés :
echo   📁 dist\nmea_tracker_server_enhanced.exe  (Console avec --tray support)
echo   📁 dist\nmea_tracker_server_tray.exe      (System Tray automatique)
echo.
echo Mode d'emploi :
echo   🖥️  Console mode     : nmea_tracker_server_enhanced.exe --console
echo   🔄 Auto mode        : nmea_tracker_server_enhanced.exe (détection auto)
echo   📍 System Tray      : nmea_tracker_server_tray.exe
echo.
echo Interface web disponible sur : https://localhost:5000
echo Configuration disponible sur : https://localhost:5000/config.html
echo.

REM Afficher la taille des fichiers
if exist "dist\nmea_tracker_server_enhanced.exe" (
    for %%A in ("dist\nmea_tracker_server_enhanced.exe") do echo Taille Console: %%~zA octets
)
if exist "dist\nmea_tracker_server_tray.exe" (
    for %%A in ("dist\nmea_tracker_server_tray.exe") do echo Taille Tray: %%~zA octets
)

echo.
pause
