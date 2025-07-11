@echo off
echo ===== Installation complète NMEA Tracker Server (Windows) =====
echo.

REM Définir le répertoire du projet
set "PROJECT_DIR=%~dp0..\.."
cd /d "%PROJECT_DIR%"

echo 📁 Répertoire: %PROJECT_DIR%
echo.

REM Vérifier Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python non trouvé!
    echo Téléchargez et installez Python depuis https://python.org
    echo Assurez-vous de cocher "Add Python to PATH" pendant l'installation
    pause
    exit /b 1
)

echo ✅ Python trouvé:
python --version
echo.

REM Créer l'environnement virtuel
if not exist ".venv" (
    echo 🔧 Création de l'environnement virtuel...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ Échec de création de l'environnement virtuel
        pause
        exit /b 1
    )
    echo ✅ Environnement virtuel créé
) else (
    echo ✅ Environnement virtuel existant trouvé
)

REM Activer l'environnement virtuel
echo 🔧 Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

REM Mettre à jour pip
echo 🔧 Mise à jour de pip...
python -m pip install --upgrade pip

REM Installer les dépendances
echo 📦 Installation des dépendances...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Échec d'installation des dépendances
        pause
        exit /b 1
    )
    echo ✅ Dépendances installées
) else (
    echo ❌ requirements.txt non trouvé
    pause
    exit /b 1
)

REM Installer PyInstaller
echo 🔧 Installation de PyInstaller...
pip install pyinstaller

echo.
echo ✅ INSTALLATION TERMINÉE !
echo.
echo Pour builder l'exécutable:
echo   scripts\windows\build.bat
echo.
echo Pour tester directement:
echo   .venv\Scripts\activate.bat
echo   python nmea_server.py
echo.

pause
