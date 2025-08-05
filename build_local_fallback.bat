@echo off
echo =======================================
echo  NMEA Tracker Server - Build Local
echo  Compatible Python 3.13 (sans gevent)
echo =======================================
echo.

REM Detecter l'environnement Python
python --version 2>nul
if errorlevel 1 (
    echo ERREUR: Python non trouve dans PATH
    echo Solution: Installer Python ou ajouter au PATH
    pause
    exit /b 1
)

echo Environnement Python detecte:
python --version
echo.

REM Installer les dependances de base
echo Installation des dependances de base...
pip install -r requirements_enhanced_alt.txt
if errorlevel 1 (
    echo ERREUR: Installation des dependances echouee
    echo Tentative avec requirements de base...
    pip install -r requirements.txt
    pip install pystray pillow pyinstaller
)

echo.
echo =======================================
echo  Construction des executables
echo =======================================
echo.

REM Nettoyer les precedents builds
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Creer les certificats SSL si necessaires
echo Creation des certificats SSL...
python -c "
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta
    import ipaddress
    
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, 'localhost')])
    cert = x509.CertificateBuilder().subject_name(subject).issuer_name(issuer).public_key(private_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.utcnow()).not_valid_after(datetime.utcnow() + timedelta(days=365)).sign(private_key, hashes.SHA256())
    
    with open('cert.pem', 'wb') as f: f.write(cert.public_bytes(serialization.Encoding.PEM))
    with open('key.pem', 'wb') as f: f.write(private_key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()))
    print('Certificats SSL crees avec succes')
except Exception as e:
    print(f'Erreur creation certificats: {e}')
"

echo.
echo Construction de la version System Tray...
pyinstaller nmea_server_tray.spec --clean --noconfirm
if exist "dist\nmea_tracker_tray.exe" (
    echo ✓ System Tray build reussi
    for %%f in (dist\nmea_tracker_tray.exe) do echo   Taille: %%~zf octets
) else (
    echo ✗ System Tray build echoue
)

echo.
echo Construction de la version Service...
pyinstaller nmea_server_service.spec --clean --noconfirm
if exist "dist\nmea_tracker_service.exe" (
    echo ✓ Service build reussi
    for %%f in (dist\nmea_tracker_service.exe) do echo   Taille: %%~zf octets
) else (
    echo ✗ Service build echoue
)

echo.
echo Construction de la version Console...
pyinstaller nmea_server.spec --clean --noconfirm
if exist "dist\nmea_tracker_server.exe" (
    echo ✓ Console build reussi
    for %%f in (dist\nmea_tracker_server.exe) do echo   Taille: %%~zf octets
) else (
    echo ✗ Console build echoue
)

echo.
echo =======================================
echo  Resultats du build
echo =======================================
if exist "dist\nmea_tracker_tray.exe" echo ✓ nmea_tracker_tray.exe - Interface system tray
if exist "dist\nmea_tracker_service.exe" echo ✓ nmea_tracker_service.exe - Service Windows
if exist "dist\nmea_tracker_server.exe" echo ✓ nmea_tracker_server.exe - Version console

echo.
echo Les executables sont dans le dossier 'dist\'
echo.
echo Test de fonctionnement (optionnel):
echo   dist\nmea_tracker_tray.exe --console
echo.

REM Test rapide de l'executable si demande
set /p test_choice="Tester l'executable maintenant ? (y/n): "
if /i "%test_choice%"=="y" (
    echo.
    echo Test de l'executable System Tray...
    if exist "dist\nmea_tracker_tray.exe" (
        echo Lancement du test (arret automatique dans 10 secondes)...
        timeout /t 2 >nul
        start /wait /b dist\nmea_tracker_tray.exe --console
    ) else (
        echo Executable non trouve
    )
)

pause
