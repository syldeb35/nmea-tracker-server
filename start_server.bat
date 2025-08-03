@echo off
echo.
echo ====================================
echo   NMEA Tracker Server - Windows
echo ====================================
echo.

REM Vérifier que l'environnement virtuel existe
if not exist ".venv\Scripts\python.exe" (
    echo ❌ Environnement virtuel non trouvé!
    echo Veuillez d'abord configurer Python avec VS Code.
    pause
    exit /b 1
)

echo ✅ Environnement Python détecté: %cd%\.venv
echo ✅ Filtres de logs HTTP/SSL activés (console propre)
echo.

REM Afficher la configuration
echo 📡 Configuration par défaut:
echo    - Port HTTP/HTTPS: 5000
echo    - Port UDP: 5005  
echo    - Port TCP: 5006
echo    - Port série: AUTO (détection automatique)
echo.

REM Afficher les URLs d'accès
echo 🌐 Interface web disponible sur:
echo    - https://localhost:5000/config.html
echo    - http://localhost:5000/config.html (fallback)
echo.

echo 🚀 Démarrage du serveur NMEA...
echo    📋 Logs détaillés dans: logs/
echo    (Appuyez sur Ctrl+C pour arrêter)
echo.

REM Lancer le serveur
.venv\Scripts\python.exe nmea_server.py

echo.
echo 👋 Serveur arrêté.
pause
