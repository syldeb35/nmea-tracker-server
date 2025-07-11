#!/bin/bash

echo "===== Installation complète NMEA Tracker Server (macOS) ====="
echo

# Définir le répertoire du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "📁 Répertoire: $PROJECT_DIR"
echo

# Vérifier Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python3 non trouvé!"
    echo "Installation avec Homebrew: brew install python"
    echo "Ou téléchargez depuis: https://python.org"
    exit 1
fi

echo "✅ Python3 trouvé: $(python3 --version)"

# Vérifier Xcode Command Line Tools (requis pour certaines dépendances)
if ! xcode-select -p >/dev/null 2>&1; then
    echo "⚠️  Xcode Command Line Tools non installés"
    echo "Installation: xcode-select --install"
    echo "Continuez après l'installation..."
fi

# Créer l'environnement virtuel
if [ ! -d ".venv" ]; then
    echo "🔧 Création de l'environnement virtuel..."
    python3 -m venv .venv
    if [ $? -eq 0 ]; then
        echo "✅ Environnement virtuel créé"
    else
        echo "❌ Échec de création de l'environnement virtuel"
        exit 1
    fi
else
    echo "✅ Environnement virtuel existant trouvé"
fi

# Activer l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source .venv/bin/activate

# Mettre à jour pip
echo "🔧 Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
echo "📦 Installation des dépendances..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Dépendances installées"
    else
        echo "❌ Échec d'installation des dépendances"
        exit 1
    fi
else
    echo "❌ requirements.txt non trouvé"
    exit 1
fi

# Installer PyInstaller
echo "🔧 Installation de PyInstaller..."
pip install pyinstaller

echo
echo "✅ INSTALLATION TERMINÉE !"
echo
echo "Pour builder l'exécutable:"
echo "  ./scripts/macos/build.sh"
echo
echo "Pour tester directement:"
echo "  source .venv/bin/activate"
echo "  python nmea_server.py"
echo
