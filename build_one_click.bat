@echo off
echo ===== NMEA Tracker Server - Build One-Click =====
echo.
echo 🎯 Ce script va automatiquement :
echo   1. Vérifier/installer l'environnement
echo   2. Installer les dépendances
echo   3. Builder la version System Tray
echo.

set /p confirm="Continuer ? (o/N): "
if /i not "%confirm%"=="o" if /i not "%confirm%"=="oui" (
    echo Annulé.
    pause
    exit /b 0
)

echo.
echo ===== ÉTAPE 1/3 : SETUP =====
call setup_enhanced.bat
if %errorlevel% neq 0 (
    echo ❌ Échec du setup
    pause
    exit /b 1
)

echo.
echo ===== ÉTAPE 2/3 : TEST =====
call test_build.bat
if %errorlevel% neq 0 (
    echo ❌ Échec du test
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
