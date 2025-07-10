#!/bin/bash

echo "===== NMEA Tracker Server - Build Script ====="
echo

# Créer les répertoires de build
mkdir -p dist build

echo "[1/4] Nettoyage des anciens builds..."
rm -f dist/nmea_tracker_server
rm -rf build/*

echo "[2/4] Installation des dépendances..."
pip install -r requirements.txt

echo "[3/4] Création de l'exécutable avec PyInstaller..."
pyinstaller nmea_server.spec --clean --noconfirm

echo "[4/4] Vérification du build..."
if [ -f "dist/nmea_tracker_server" ]; then
    echo
    echo "✅ BUILD RÉUSSI !"
    echo
    echo "Exécutable créé : dist/nmea_tracker_server"
    echo "Taille du fichier : $(du -h dist/nmea_tracker_server | cut -f1)"
    echo
    echo "Pour tester : cd dist && ./nmea_tracker_server"
    echo
    chmod +x dist/nmea_tracker_server
else
    echo
    echo "❌ ÉCHEC DU BUILD"
    echo "Vérifiez les erreurs ci-dessus."
    echo
fi
