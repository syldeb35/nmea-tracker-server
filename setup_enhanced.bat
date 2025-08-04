@echo off
echo ===== Setup NMEA Tracker Server - Enhanced (Windows) =====
echo.

REM Définir le répertoire de travail
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo 📁 Répertoire de travail : %PROJECT_DIR%
echo.

echo [1/4] Vérification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Python n'est pas installé ou pas dans le PATH
    echo.
    echo 🔧 SOLUTION:
    echo   1. Télécharger Python depuis https://python.org
    echo   2. IMPORTANT: Cocher "Add Python to PATH" lors de l'installation
    echo   3. Redémarrer PowerShell après installation
    echo   4. Relancer ce script
    echo.
    pause
    exit /b 1
)

python --version
echo ✅ Python détecté
echo.

echo [2/4] Création de l'environnement virtuel...
if exist ".venv" (
    echo ⚠️  Environnement virtuel .venv existe déjà
    set /p recreate="Recréer l'environnement ? (o/N): "
    if /i "!recreate!"=="o" (
        echo Suppression de l'ancien environnement...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv" (
    echo Création de l'environnement virtuel...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ ERREUR: Échec de création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé
) else (
    echo ✅ Environnement virtuel existant utilisé
)
echo.

echo [3/4] Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec d'activation de l'environnement virtuel
    pause
    exit /b 1
)
echo ✅ Environnement virtuel activé
echo.

echo [4/4] Installation des dépendances...
echo Mise à jour de pip...
python -m pip install --upgrade pip

echo Installation des dépendances de base...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec d'installation de requirements.txt
    pause
    exit /b 1
)

echo Installation des dépendances avancées...
pip install -r requirements_enhanced.txt
if %errorlevel% neq 0 (
    echo ❌ ERREUR: Échec d'installation de requirements_enhanced.txt
    pause
    exit /b 1
)

echo ✅ Toutes les dépendances installées
echo.

echo ===== SETUP TERMINÉ =====
echo.
echo ✅ Environnement prêt pour le build !
echo.
echo 🚀 PROCHAINES ÉTAPES :
echo.
echo 1. Pour builder la version System Tray :
echo    .\build_enhanced.bat
echo    (Choisir option 2)
echo.
echo 2. Pour builder toutes les versions :
echo    .\build_enhanced.bat
echo    (Choisir option 4)
echo.
echo 3. Pour tester le serveur directement :
echo    .\.venv\Scripts\python.exe nmea_server.py
echo.
echo 4. En cas de problème :
echo    .\diagnostic.bat
echo.

pause
