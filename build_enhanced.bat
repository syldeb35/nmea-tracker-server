@echo off
echo ===== NMEA Tracker Server - Build Enhanced (Windows) =====
echo.
echo Versions disponibles :
echo   1. Console (version standard)
echo   2. System Tray (icône dans la zone de notification)
echo   3. Service Windows (service en arrière-plan)
echo   4. Toutes les versions
echo.

REM Définir le répertoire du projet
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo Working directory: %PROJECT_DIR%
echo.

REM Menu de sélection
set /p choice="Choisissez la version à builder (1-4): "

if "%choice%"=="1" goto build_console
if "%choice%"=="2" goto build_tray
if "%choice%"=="3" goto build_service
if "%choice%"=="4" goto build_all
echo Choix invalide. Annulation.
pause
exit /b 1

:build_console
echo [INFO] Build de la version console...
call :build_version "nmea_server.spec" "nmea_tracker_server.exe" "Console"
goto end

:build_tray
echo [INFO] Build de la version System Tray...
call :install_enhanced_deps
call :build_version "nmea_server_tray.spec" "nmea_tracker_tray.exe" "System Tray"
goto end

:build_service
echo [INFO] Build de la version Service Windows...
call :install_enhanced_deps
call :build_version "nmea_server_service.spec" "nmea_tracker_service.exe" "Service Windows"
goto end

:build_all
echo [INFO] Build de toutes les versions...
call :install_enhanced_deps
call :build_version "nmea_server.spec" "nmea_tracker_server.exe" "Console"
call :build_version "nmea_server_tray.spec" "nmea_tracker_tray.exe" "System Tray"
call :build_version "nmea_server_service.spec" "nmea_tracker_service.exe" "Service Windows"
goto end

:install_enhanced_deps
echo [0/4] Installation des dépendances avancées...

REM Vérifier si un environnement virtuel existe et l'activer
if exist ".venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel .venv...
    call .venv\Scripts\activate.bat
    if %errorlevel% equ 0 (
        echo ✅ Environnement virtuel .venv activé
    ) else (
        echo ❌ ERREUR: Échec d'activation de l'environnement virtuel .venv
        pause
        exit /b 1
    )
) else if exist "venv\Scripts\activate.bat" (
    echo Activation de l'environnement virtuel venv...
    call venv\Scripts\activate.bat
    if %errorlevel% equ 0 (
        echo ✅ Environnement virtuel venv activé
    ) else (
        echo ❌ ERREUR: Échec d'activation de l'environnement virtuel venv
        pause
        exit /b 1
    )
) else (
    echo [WARNING] Aucun environnement virtuel détecté
    echo Vérification de Python dans le système...
    python --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ ERREUR: Python n'est pas installé ou pas dans le PATH
        echo.
        echo 🔧 SOLUTIONS :
        echo   1. Créer un environnement virtuel : python -m venv .venv
        echo   2. Ou installer Python système : https://python.org
        echo   3. Ou utiliser setup_enhanced.bat pour setup automatique
        echo.
        pause
        exit /b 1
    )
    echo ✅ Python système détecté
)

REM Vérifier que pip est maintenant disponible
echo Vérification de pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERREUR: pip n'est pas disponible même après activation de l'environnement
    echo Vérifiez que l'environnement virtuel est correctement configuré
    pause
    exit /b 1
)
echo ✅ pip disponible

echo Installation des dépendances depuis requirements_enhanced.txt...

pip install -r requirements_enhanced.txt
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec d'installation des dépendances avancées
    pause
    exit /b 1
)
echo ✅ Dépendances avancées installées
echo.
goto :eof

:build_version
set "spec_file=%~1"
set "exe_name=%~2"
set "version_name=%~3"

echo.
echo ===== BUILD %version_name% =====

REM Vérifier si le fichier spec existe
if not exist "%spec_file%" (
    echo ❌ ERREUR: Fichier %spec_file% non trouvé
    goto :eof
)

echo [1/4] Nettoyage des anciens builds...
if exist "dist\%exe_name%" del "dist\%exe_name%"
if exist "build" rmdir /s /q "build"

REM Créer les répertoires de build
if not exist "dist" mkdir "dist"
if not exist "build" mkdir "build"

echo [2/4] Vérification du fichier spec...
if not exist "%spec_file%" (
    echo ❌ ERREUR: Fichier %spec_file% non trouvé dans %cd%
    echo Fichiers .spec disponibles :
    dir /b *.spec 2>nul || echo Aucun fichier .spec trouvé
    goto :eof
)
echo ✅ Fichier %spec_file% trouvé

echo [2/4] Vérification de PyInstaller...
where pyinstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PyInstaller non trouvé, installation...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ❌ ERREUR: Échec d'installation de PyInstaller
        goto :eof
    )
    echo ✅ PyInstaller installé
) else (
    echo ✅ PyInstaller trouvé
)

echo [3/4] Création de l'exécutable %version_name%...
pyinstaller "%spec_file%" --clean --noconfirm
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec de création de l'exécutable %version_name%
    goto :eof
)

echo [4/4] Vérification du build %version_name%...
if exist "dist\%exe_name%" (
    echo ✅ BUILD %version_name% RÉUSSI !
    for %%I in ("dist\%exe_name%") do echo Taille : %%~zI octets
    
    REM Instructions spécifiques selon la version
    if "%version_name%"=="Console" (
        echo Usage : cd dist ^&^& %exe_name%
        echo Interface : https://localhost:8443/config.html
    )
    if "%version_name%"=="System Tray" (
        echo Usage : cd dist ^&^& %exe_name%
        echo L'icône apparaîtra dans la zone de notification
        echo Clic droit sur l'icône pour accéder au menu
    )
    if "%version_name%"=="Service Windows" (
        echo Installation : cd dist ^&^& %exe_name% install
        echo Démarrage : net start NMEATrackerServer
        echo Interface : https://localhost:8443/config.html
    )
    echo.
) else (
    echo ❌ ÉCHEC DU BUILD %version_name%
)
goto :eof

:end
echo.
echo ===== RÉSUMÉ DES BUILDS =====
if exist "dist\nmea_tracker_server.exe" (
    echo ✅ Console : dist\nmea_tracker_server.exe
)
if exist "dist\nmea_tracker_tray.exe" (
    echo ✅ System Tray : dist\nmea_tracker_tray.exe
)
if exist "dist\nmea_tracker_service.exe" (
    echo ✅ Service Windows : dist\nmea_tracker_service.exe
)
echo.
echo 📁 Tous les exécutables sont dans le dossier 'dist\'
echo.

pause
