#!/bin/bash

echo "===== Test de l'exécutable NMEA Tracker Server (Linux) ====="
echo

# Définir le répertoire du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

# Vérifier si l'exécutable existe
if [ ! -f "dist/nmea_tracker_server" ]; then
    echo "❌ Exécutable non trouvé dans dist/nmea_tracker_server"
    echo "Veuillez d'abord exécuter ./scripts/linux/build.sh"
    exit 1
fi

echo "✅ Exécutable trouvé: dist/nmea_tracker_server"
echo "📊 Taille: $(du -h dist/nmea_tracker_server | cut -f1)"
echo "🔐 Permissions: $(ls -l dist/nmea_tracker_server | cut -d' ' -f1)"
echo

# Vérifier les permissions d'exécution
if [ ! -x "dist/nmea_tracker_server" ]; then
    echo "🔧 Ajout des permissions d'exécution..."
    chmod +x dist/nmea_tracker_server
fi

echo "🚀 Test de lancement de l'exécutable..."
echo "   (Ctrl+C pour arrêter après quelques secondes)"
echo

# Lancer l'exécutable en arrière-plan
cd dist
timeout 10s ./nmea_tracker_server &
PID=$!

# Attendre un peu pour que le serveur démarre
sleep 3

# Vérifier si le processus est en cours
if kill -0 $PID 2>/dev/null; then
    echo "✅ Serveur démarré avec succès (PID: $PID)"
    
    # Tester la connexion HTTP
    if command -v curl >/dev/null 2>&1; then
        echo "🌐 Test de connexion HTTP..."
        if curl -s -k --connect-timeout 5 https://localhost:5000/ >/dev/null 2>&1; then
            echo "✅ Serveur HTTPS répond sur le port 5000"
        elif curl -s --connect-timeout 5 http://localhost:5000/ >/dev/null 2>&1; then
            echo "✅ Serveur HTTP répond sur le port 5000"
        else
            echo "⚠️  Serveur en cours de démarrage ou port différent"
        fi
    else
        echo "⚠️  curl non installé, test de connexion ignoré"
    fi
    
    # Arrêter le processus
    echo "🛑 Arrêt du serveur de test..."
    kill $PID 2>/dev/null
    wait $PID 2>/dev/null
    echo "✅ Serveur arrêté"
else
    echo "❌ Échec du démarrage du serveur"
    echo "Vérifiez les logs ci-dessus pour les erreurs"
fi

cd ..

echo
echo "📋 RÉSUMÉ DU TEST:"
echo "   Pour lancer manuellement:"
echo "     cd dist && ./nmea_tracker_server"
echo
echo "   Interface web:"
echo "     https://localhost:5000/"
echo "     https://localhost:5000/config.html"
echo
