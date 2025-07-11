#!/bin/bash

echo "===== Vérification des prérequis (Linux) ====="
echo

# Définir le répertoire du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "📁 Répertoire de travail: $PROJECT_DIR"
echo

# Vérifier Python
echo "🐍 Vérification de Python..."
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Python3 trouvé: $(which python3)"
    echo "   Version: $(python3 --version)"
elif command -v python >/dev/null 2>&1; then
    echo "✅ Python trouvé: $(which python)"
    echo "   Version: $(python --version)"
else
    echo "❌ Python non trouvé! Veuillez installer Python 3.8+"
    echo "   Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "   CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "   Arch: sudo pacman -S python python-pip"
    echo "   Fedora: sudo dnf install python3 python3-pip"
    exit 1
fi
echo

# Vérifier pip
echo "📦 Vérification de pip..."
if command -v pip3 >/dev/null 2>&1; then
    echo "✅ pip3 trouvé: $(which pip3)"
    echo "   Version: $(pip3 --version)"
elif command -v pip >/dev/null 2>&1; then
    echo "✅ pip trouvé: $(which pip)"
    echo "   Version: $(pip --version)"
else
    echo "❌ pip non trouvé! Veuillez installer pip"
    exit 1
fi
echo

# Vérifier l'environnement virtuel
echo "🌍 Vérification de l'environnement virtuel..."
if [ -d ".venv" ]; then
    echo "✅ Environnement virtuel '.venv' trouvé"
    if [ -f ".venv/bin/activate" ]; then
        echo "✅ Script d'activation trouvé"
    else
        echo "❌ Script d'activation manquant"
    fi
elif [ -d "venv" ]; then
    echo "✅ Environnement virtuel 'venv' trouvé"
    if [ -f "venv/bin/activate" ]; then
        echo "✅ Script d'activation trouvé"
    else
        echo "❌ Script d'activation manquant"
    fi
else
    echo "⚠️  Aucun environnement virtuel trouvé"
    echo "   Recommandation: python3 -m venv .venv"
fi
echo

# Vérifier les fichiers requis
echo "📄 Vérification des fichiers requis..."
files=("requirements.txt" "nmea_server.py" "nmea_server.spec")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file trouvé"
    else
        echo "❌ $file manquant"
    fi
done
echo

# Vérifier PyInstaller
echo "🔧 Vérification de PyInstaller..."
if command -v pyinstaller >/dev/null 2>&1; then
    echo "✅ PyInstaller trouvé: $(which pyinstaller)"
    echo "   Version: $(pyinstaller --version)"
else
    echo "⚠️  PyInstaller non trouvé (sera installé automatiquement)"
fi
echo

# Vérifier les permissions série
echo "🔌 Vérification des ports série..."
if ls /dev/ttyUSB* >/dev/null 2>&1; then
    for port in /dev/ttyUSB*; do
        if [ -r "$port" ] && [ -w "$port" ]; then
            echo "✅ $port (accessible)"
        else
            echo "⚠️  $port (permissions insuffisantes)"
            echo "   Solution: sudo chmod 666 $port"
            echo "   ou: sudo usermod -a -G dialout \$USER (puis redémarrer)"
        fi
    done
else
    echo "ℹ️  Aucun port USB série détecté"
fi

if ls /dev/rfcomm* >/dev/null 2>&1; then
    for port in /dev/rfcomm*; do
        if [ -r "$port" ] && [ -w "$port" ]; then
            echo "✅ $port (Bluetooth accessible)"
        else
            echo "⚠️  $port (permissions Bluetooth insuffisantes)"
        fi
    done
else
    echo "ℹ️  Aucun port Bluetooth détecté"
fi
echo

# Résumé
echo "📋 RÉSUMÉ:"
echo "   Pour créer un environnement virtuel:"
echo "     python3 -m venv .venv"
echo "     source .venv/bin/activate"
echo "     pip install -r requirements.txt"
echo
echo "   Pour builder:"
echo "     ./scripts/linux/build.sh"
echo
