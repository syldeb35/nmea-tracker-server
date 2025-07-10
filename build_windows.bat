@echo off
echo ===== NMEA Tracker Server - Build Script =====
echo.

REM Vérification des prérequis
echo [0/5] Vérification des prérequis...
if not exist "cert.pem" (
    echo ❌ ERREUR: cert.pem manquant!
    echo Placez vos certificats SSL dans le répertoire du projet.
    goto :error
)
if not exist "key.pem" (
    echo ❌ ERREUR: key.pem manquant!
    echo Placez vos certificats SSL dans le répertoire du projet.
    goto :error
)
echo ✅ Certificats SSL trouvés

REM Créer le répertoire de build s'il n'existe pas
if not exist "dist" mkdir dist
if not exist "build" mkdir build

echo [1/5] Nettoyage des anciens builds...
if exist "dist\nmea_tracker_server.exe" del "dist\nmea_tracker_server.exe"
if exist "build" rmdir /s /q "build"

echo [2/5] Installation des dépendances...
pip install -r requirements.txt

echo [3/5] Vérification des templates...
if not exist "templates\config.html" (
    echo ❌ ERREUR: templates/config.html manquant!
    goto :error
)
if not exist "templates\index.html" (
    echo ❌ ERREUR: templates/index.html manquant!
    goto :error
)
echo ✅ Templates trouvés

echo [4/5] Création de l'exécutable avec PyInstaller...
pyinstaller nmea_server.spec --clean --noconfirm

echo [5/5] Vérification du build...
if exist "dist\nmea_tracker_server.exe" (
    echo.
    echo ✅ BUILD RÉUSSI !
    echo.
    echo Exécutable créé : dist\nmea_tracker_server.exe
    echo Taille du fichier :
    for %%I in ("dist\nmea_tracker_server.exe") do echo   %%~zI bytes (~%%~zI / 1024 / 1024 MB)
    echo.
    echo 📁 Fichiers inclus dans l'exécutable :
    echo   - Code Python principal
    echo   - Templates HTML (config.html, index.html, favicon.svg)
    echo   - Certificats SSL (cert.pem, key.pem)
    echo   - Configuration (.env)
    echo   - Icône personnalisée (icon.ico)
    echo   - Runtime Python + dépendances
    echo.
    echo 🚀 Pour tester : cd dist ^&^& nmea_tracker_server.exe
    echo 🌐 Interface web : https://localhost:5000/config.html
    echo.
) else (
    echo.
    echo ❌ ÉCHEC DU BUILD
    echo Vérifiez les erreurs ci-dessus.
    echo.
)

echo Appuyez sur une touche pour continuer...
pause >nul
goto :end

:error
echo.
echo ❌ BUILD IMPOSSIBLE - Erreur de prérequis
echo.
pause >nul

:end
