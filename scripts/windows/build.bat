@echo off
echo ===== NMEA Tracker Server - Build Script (Windows) =====
echo.
echo ⚠️  NOUVEAU: Versions avancées disponibles !
echo.
echo Ce script build la version console standard.
echo Pour les versions System Tray et Service Windows, utilisez :
echo   build_enhanced.bat (dans le répertoire principal)
echo.
echo Versions disponibles avec build_enhanced.bat :
echo   1. Console (cette version)
echo   2. System Tray (icône dans la zone de notification)
echo   3. Service Windows (service en arrière-plan)
echo.
set /p continue="Continuer avec la version console ? (o/N): "
if /i not "%continue%"=="o" if /i not "%continue%"=="oui" (
    echo Annulé. Utilisez build_enhanced.bat pour plus d'options.
    pause
    exit /b 0
)
echo.

REM Définir le répertoire du projet
set "PROJECT_DIR=%~dp0..\.."
cd /d "%PROJECT_DIR%"

echo Working directory: %PROJECT_DIR%
echo.

REM Vérifier si un environnement virtuel existe
if exist ".venv\Scripts\activate.bat" (
    echo [0/4] Activation de l'environnement virtuel...
    call .venv\Scripts\activate.bat
    echo ✅ Environnement virtuel activé
    echo Python: %VIRTUAL_ENV%\Scripts\python.exe
    echo Pip: %VIRTUAL_ENV%\Scripts\pip.exe
    echo.
) else if exist "venv\Scripts\activate.bat" (
    echo [0/4] Activation de l'environnement virtuel...
    call venv\Scripts\activate.bat
    echo ✅ Environnement virtuel activé
    echo Python: %VIRTUAL_ENV%\Scripts\python.exe
    echo Pip: %VIRTUAL_ENV%\Scripts\pip.exe
    echo.
) else (
    echo [0/4] Aucun environnement virtuel détecté, utilisation du système...
    where python >nul 2>&1 && echo Python: %PATH% || echo Python non trouvé dans PATH
    where pip >nul 2>&1 && echo Pip: %PATH% || echo Pip non trouvé dans PATH
    echo.
)

echo [1/4] Nettoyage des anciens builds...
if exist "dist\nmea_tracker_server.exe" del "dist\nmea_tracker_server.exe"
if exist "build" rmdir /s /q "build"

REM Créer les répertoires de build
if not exist "dist" mkdir "dist"
if not exist "build" mkdir "build"

echo [2/4] Installation des dépendances...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec d'installation des dépendances
    pause
    exit /b 1
)

echo [3/4] Création de l'exécutable avec PyInstaller...
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERREUR: pyinstaller non trouvé!
    echo Installation de PyInstaller...
    pip install pyinstaller
)

pyinstaller nmea_server.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec de création de l'exécutable
    pause
    exit /b 1
)

echo [4/4] Vérification du build...
if exist "dist\nmea_tracker_server.exe" (
    echo.
    echo ✅ BUILD RÉUSSI !
    echo.
    echo Exécutable créé : dist\nmea_tracker_server.exe
    for %%I in ("dist\nmea_tracker_server.exe") do echo Taille du fichier : %%~zI octets
    echo.
    echo Pour tester : cd dist ^&^& nmea_tracker_server.exe
    echo.
) else (
    echo.
    echo ❌ ÉCHEC DU BUILD
    echo Vérifiez les erreurs ci-dessus.
    echo.
)

pause
