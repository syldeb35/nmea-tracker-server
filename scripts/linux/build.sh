#!/bin/bash

echo "===== NMEA Tracker Server - Build Script (Linux) ====="
echo

# Définir le répertoire du projet (parent du répertoire scripts)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "Working directory: $PROJECT_DIR"
echo

# Vérifier si un environnement virtuel existe
if [ -d ".venv" ]; then
    echo "[0/4] Activation de l'environnement virtuel..."
    source .venv/bin/activate
    echo "✅ Environnement virtuel activé"
    echo "Python: $(which python)"
    echo "Pip: $(which pip)"
    echo
elif [ -d "venv" ]; then
    echo "[0/4] Activation de l'environnement virtuel..."
    source venv/bin/activate
    echo "✅ Environnement virtuel activé"
    echo "Python: $(which python)"
    echo "Pip: $(which pip)"
    echo
else
    echo "[0/4] Aucun environnement virtuel détecté, utilisation du système..."
    echo "Python: $(which python3 || which python)"
    echo "Pip: $(which pip3 || which pip)"
    echo
fi

echo "[1/4] Nettoyage des anciens builds..."
rm -f dist/nmea_tracker_server
rm -rf build/*

# Créer les répertoires de build
mkdir -p dist build

echo "[2/4] Installation des dépendances..."
# Utiliser pip3 ou pip selon la disponibilité
if command -v pip >/dev/null 2>&1; then
    pip install -r requirements.txt
elif command -v pip3 >/dev/null 2>&1; then
    pip3 install -r requirements.txt
else
    echo "❌ ERREUR: pip non trouvé!"
    exit 1
fi

echo "[3/4] Création de l'exécutable avec PyInstaller..."
# Utiliser pyinstaller depuis l'environnement actuel
if command -v pyinstaller >/dev/null 2>&1; then
    pyinstaller nmea_server.spec --clean --noconfirm
else
    echo "❌ ERREUR: pyinstaller non trouvé!"
    echo "Installation de PyInstaller..."
    if command -v pip >/dev/null 2>&1; then
        pip install pyinstaller
    elif command -v pip3 >/dev/null 2>&1; then
        pip3 install pyinstaller
    fi
    pyinstaller nmea_server.spec --clean --noconfirm
fi

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
