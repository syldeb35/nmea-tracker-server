@echo off
echo ===== Test Automatisé Build Enhanced =====
echo.

REM Aller dans le répertoire du projet
cd /d "%~dp0"

echo 📁 Répertoire : %cd%
echo.

echo [TEST] Activation de l'environnement virtuel...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo ✅ Environnement virtuel activé
) else (
    echo ❌ Environnement virtuel non trouvé
    echo Exécutez d'abord : setup_enhanced.bat
    pause
    exit /b 1
)

echo.
echo [TEST] Vérification des dépendances...
pip list | findstr "pystray"
if %errorlevel% equ 0 (
    echo ✅ pystray installé
) else (
    echo ❌ pystray manquant - installation...
    pip install pystray
)

pip list | findstr "pyinstaller"
if %errorlevel% equ 0 (
    echo ✅ pyinstaller installé
) else (
    echo ❌ pyinstaller manquant - installation...
    pip install pyinstaller
)

echo.
echo [TEST] Build de la version System Tray...

REM Nettoyer les anciens builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
mkdir "dist"

REM Builder avec PyInstaller
echo Exécution de PyInstaller...
pyinstaller nmea_server_tray.spec --clean --noconfirm

echo.
echo [TEST] Vérification du résultat...
if exist "dist\nmea_tracker_tray.exe" (
    echo ✅ BUILD RÉUSSI !
    echo.
    echo 📁 Fichier créé : dist\nmea_tracker_tray.exe
    for %%I in ("dist\nmea_tracker_tray.exe") do echo 📊 Taille : %%~zI octets
    echo.
    echo 🧪 Test de lancement rapide...
    cd dist
    timeout 3 nmea_tracker_tray.exe --console >nul 2>&1
    cd ..
    echo ✅ Test de lancement OK
) else (
    echo ❌ ÉCHEC DU BUILD
    echo Vérifiez les erreurs ci-dessus
)

echo.
echo ===== RÉSUMÉ =====
if exist "dist\nmea_tracker_tray.exe" (
    echo ✅ Build System Tray réussi
    echo 🚀 Pour lancer : cd dist ^&^& nmea_tracker_tray.exe
) else (
    echo ❌ Build échoué
)

echo.
pause
