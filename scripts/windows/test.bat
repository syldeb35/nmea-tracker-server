@echo off
echo ===== Test de l'exécutable NMEA Tracker Server (Windows) =====
echo.

REM Définir le répertoire du projet
set "PROJECT_DIR=%~dp0..\.."
cd /d "%PROJECT_DIR%"

REM Vérifier si l'exécutable existe
if not exist "dist\nmea_tracker_server.exe" (
    echo ❌ Exécutable non trouvé dans dist\nmea_tracker_server.exe
    echo Veuillez d'abord exécuter scripts\windows\build.bat
    pause
    exit /b 1
)

echo ✅ Exécutable trouvé: dist\nmea_tracker_server.exe
for %%I in ("dist\nmea_tracker_server.exe") do echo 📊 Taille: %%~zI octets
echo.

echo 🚀 Test de lancement de l'exécutable...
echo    (Ctrl+C pour arrêter après quelques secondes)
echo.

REM Lancer l'exécutable en arrière-plan
cd dist
start "NMEA Server Test" nmea_tracker_server.exe

REM Attendre un peu pour que le serveur démarre
timeout /t 5 /nobreak >nul

REM Tester la connexion HTTP avec curl si disponible
where curl >nul 2>&1
if %errorlevel% equ 0 (
    echo 🌐 Test de connexion HTTP...
    curl -s -k --connect-timeout 5 https://localhost:5000/ >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ Serveur HTTPS répond sur le port 5000
    ) else (
        curl -s --connect-timeout 5 http://localhost:5000/ >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ Serveur HTTP répond sur le port 5000
        ) else (
            echo ⚠️  Serveur en cours de démarrage ou port différent
        )
    )
) else (
    echo ⚠️  curl non installé, test de connexion ignoré
)

cd ..

echo.
echo 📋 RÉSUMÉ DU TEST:
echo    Pour lancer manuellement:
echo      cd dist ^&^& nmea_tracker_server.exe
echo.
echo    Interface web:
echo      https://localhost:5000/
echo      https://localhost:5000/config.html
echo.

pause
