#!/bin/bash

echo "===== Installation complète NMEA Tracker Server (Linux) ====="
echo

# Définir le répertoire du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "📁 Répertoire: $PROJECT_DIR"
echo

# Vérifier Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "❌ Python3 non trouvé!"
    echo "Installation sur Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "Installation sur CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "Installation sur Arch: sudo pacman -S python python-pip"
    echo "Installation sur Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi

echo "✅ Python3 trouvé: $(python3 --version)"

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
echo "  ./scripts/linux/build.sh"
echo
echo "Pour tester directement:"
echo "  source .venv/bin/activate"
echo "  python nmea_server.py"
echo
