@echo off
echo ===== Diagnostic NMEA Tracker Server Build =====
echo.

REM Définir le répertoire de travail
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo 📁 Répertoire de travail : %PROJECT_DIR%
echo.

echo 🔍 Vérification de l'environnement...
echo.

REM Vérifier Python
echo [1/6] Vérification de Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python --version
    echo ✅ Python installé
) else (
    echo ❌ Python non trouvé dans le PATH
    echo   Installez Python depuis https://python.org
)
echo.

REM Vérifier pip
echo [2/6] Vérification de pip...
pip --version >nul 2>&1
if %errorlevel% equ 0 (
    pip --version
    echo ✅ pip disponible
) else (
    echo ❌ pip non trouvé
)
echo.

REM Vérifier environnement virtuel
echo [3/6] Vérification des environnements virtuels...
if exist ".venv\Scripts\activate.bat" (
    echo ✅ Environnement virtuel .venv trouvé
    echo   Répertoire : %cd%\.venv\
) else (
    echo ❌ Environnement virtuel .venv non trouvé
)

if exist "venv\Scripts\activate.bat" (
    echo ✅ Environnement virtuel venv trouvé
    echo   Répertoire : %cd%\venv\
) else (
    echo ❌ Environnement virtuel venv non trouvé
)
echo.

REM Vérifier fichiers spec
echo [4/6] Vérification des fichiers .spec...
if exist "nmea_server_tray.spec" (
    echo ✅ nmea_server_tray.spec trouvé
) else (
    echo ❌ nmea_server_tray.spec manquant
)

if exist "nmea_server.spec" (
    echo ✅ nmea_server.spec trouvé
) else (
    echo ❌ nmea_server.spec manquant
)

if exist "nmea_server_service.spec" (
    echo ✅ nmea_server_service.spec trouvé
) else (
    echo ❌ nmea_server_service.spec manquant
)

echo.
echo 📋 Tous les fichiers .spec disponibles :
dir /b *.spec 2>nul || echo   Aucun fichier .spec trouvé
echo.

REM Vérifier fichiers requirements
echo [5/6] Vérification des fichiers requirements...
if exist "requirements.txt" (
    echo ✅ requirements.txt trouvé
) else (
    echo ❌ requirements.txt manquant
)

if exist "requirements_enhanced.txt" (
    echo ✅ requirements_enhanced.txt trouvé
) else (
    echo ❌ requirements_enhanced.txt manquant
)
echo.

REM Vérifier scripts Python
echo [6/6] Vérification des scripts Python...
if exist "nmea_server.py" (
    echo ✅ nmea_server.py trouvé
) else (
    echo ❌ nmea_server.py manquant
)

if exist "nmea_server_tray.py" (
    echo ✅ nmea_server_tray.py trouvé
) else (
    echo ❌ nmea_server_tray.py manquant
)

if exist "nmea_server_service.py" (
    echo ✅ nmea_server_service.py trouvé
) else (
    echo ❌ nmea_server_service.py manquant
)
echo.

echo ===== RECOMMANDATIONS =====
echo.

REM Analyser les problèmes et donner des recommandations
set "has_issues=0"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 🔧 INSTALLER PYTHON :
    echo   1. Télécharger depuis https://python.org
    echo   2. Cocher "Add Python to PATH" lors de l'installation
    echo   3. Redémarrer PowerShell après installation
    echo.
    set "has_issues=1"
)

if not exist ".venv\Scripts\activate.bat" if not exist "venv\Scripts\activate.bat" (
    echo 🔧 CRÉER UN ENVIRONNEMENT VIRTUEL :
    echo   python -m venv .venv
    echo   .\.venv\Scripts\activate.bat
    echo   pip install --upgrade pip
    echo.
    set "has_issues=1"
)

if not exist "requirements_enhanced.txt" (
    echo 🔧 FICHIER REQUIREMENTS MANQUANT :
    echo   Le fichier requirements_enhanced.txt est nécessaire
    echo   Vérifiez que vous êtes dans le bon répertoire
    echo.
    set "has_issues=1"
)

if not exist "nmea_server_tray.spec" (
    echo 🔧 FICHIERS SPEC MANQUANTS :
    echo   Les fichiers .spec de PyInstaller sont manquants
    echo   Vérifiez que vous êtes dans le bon répertoire
    echo.
    set "has_issues=1"
)

if "%has_issues%"=="0" (
    echo ✅ TOUT SEMBLE CORRECT !
    echo   Vous pouvez essayer de relancer build_enhanced.bat
) else (
    echo ⚠️  PROBLÈMES DÉTECTÉS - Suivez les recommandations ci-dessus
)

echo.
pause
