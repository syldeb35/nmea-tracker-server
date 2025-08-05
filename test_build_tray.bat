@echo off
echo =======================================
echo  Test Build avec Fallback
echo  (Version légère pour validation)
echo =======================================
echo.

REM Nettoyer les builds précédents
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo Construction version System Tray avec fallback...
pyinstaller nmea_server_tray.spec --clean --noconfirm

if exist "dist\nmea_tracker_tray.exe" (
    echo ✓ Build réussi !
    
    echo.
    echo Test rapide de l'exécutable...
    echo Lancement en mode console pendant 5 secondes...
    
    REM Tester l'exécutable avec timeout
    start /wait cmd /c "cd dist && timeout /t 5 /nobreak >nul & taskkill /f /im nmea_tracker_tray.exe >nul 2>&1"
    dist\nmea_tracker_tray.exe --console &
    
    REM Attendre un peu puis vérifier si le processus tourne
    timeout /t 3 /nobreak >nul
    tasklist /fi "imagename eq nmea_tracker_tray.exe" 2>nul | find /i "nmea_tracker_tray.exe" >nul
    if errorlevel 1 (
        echo ❌ L'exécutable ne semble pas fonctionner
    ) else (
        echo ✅ L'exécutable fonctionne !
        REM Arrêter le processus
        taskkill /f /im nmea_tracker_tray.exe >nul 2>&1
    )
    
) else (
    echo ❌ Build échoué
)

echo.
echo Test terminé.
pause
