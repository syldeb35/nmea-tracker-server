@echo off
echo ===== NMEA Tracker Server - Build One-Click (Compatibilité) =====
echo.
echo 🎯 Ce script va automatiquement :
echo   1. Installer l'environnement SANS gevent (compatibilité Python 3.13)
echo   2. Installer les dépendances compatibles
echo   3. Builder la version System Tray
echo.
echo ⚠️  Mode compatibilité : évite les problèmes avec gevent/Cython
echo.

set /p confirm="Continuer ? (o/N): "
if /i not "%confirm%"=="o" if /i not "%confirm%"=="oui" (
    echo Annulé.
    pause
    exit /b 0
)

echo.
echo ===== ÉTAPE 1/3 : SETUP COMPATIBILITÉ =====
call setup_compatibility.bat
if %errorlevel% neq 0 (
    echo ❌ Échec du setup
    pause
    exit /b 1
)

echo.
echo ===== ÉTAPE 2/3 : TEST BUILD =====
echo Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

echo Test de build System Tray...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
mkdir "dist"

echo Exécution de PyInstaller...
pyinstaller nmea_server_tray.spec --clean --noconfirm

if exist "dist\nmea_tracker_tray.exe" (
    echo ✅ Build System Tray réussi !
    for %%I in ("dist\nmea_tracker_tray.exe") do echo 📊 Taille : %%~zI octets
) else (
    echo ❌ Échec du build
    pause
    exit /b 1
)

echo.
echo ===== ÉTAPE 3/3 : FINALISATION =====
echo.
echo ✅ BUILD TERMINÉ AVEC SUCCÈS !
echo.
echo 📁 Fichier créé : dist\nmea_tracker_tray.exe
echo.
echo 🚀 UTILISATION :
echo   1. Lancez : dist\nmea_tracker_tray.exe
echo   2. Cherchez l'icône dans la zone de notification
echo   3. Clic droit sur l'icône → menu
echo   4. Interface web : https://localhost:8443/config.html
echo.
echo ⚠️  Mode compatibilité actif (sans gevent)
echo    Performance réduite mais stabilité maximale
echo.

set /p launch="Lancer maintenant ? (o/N): "
if /i "%launch%"=="o" if /i "%launch%"=="oui" (
    echo Lancement de l'application...
    start dist\nmea_tracker_tray.exe
    echo ✅ Application lancée !
    echo Cherchez l'icône NMEA dans la zone de notification.
)

echo.
echo 🎉 Terminé ! Bon usage du serveur NMEA !
pause
