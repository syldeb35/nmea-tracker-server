#!/bin/bash

echo "===== Test de l'exécutable NMEA Tracker ====="
echo

if [ ! -f "dist/nmea_tracker_server" ]; then
    echo "❌ Exécutable non trouvé. Lancez d'abord build_unix.sh"
    exit 1
fi

echo "🚀 Lancement de l'exécutable..."
echo "   (Le serveur va démarrer, testez Ctrl+C pour l'arrêter)"
echo

cd dist
./nmea_tracker_server

echo
echo "✅ Test terminé"
