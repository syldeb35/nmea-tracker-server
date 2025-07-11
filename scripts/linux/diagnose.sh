#!/bin/bash

echo "===== Diagnostic NMEA Tracker Server (Linux) ====="
echo

# Définir le répertoire du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

echo "📁 Répertoire: $PROJECT_DIR"
echo "🖥️  Système: $(uname -s) $(uname -r)"
echo "💻 Architecture: $(uname -m)"
echo "🐧 Distribution: $(lsb_release -d 2>/dev/null | cut -f2 || cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo

# Vérifier l'environnement Python
echo "🐍 ENVIRONNEMENT PYTHON:"
if command -v python3 >/dev/null 2>&1; then
    echo "✅ python3: $(which python3) ($(python3 --version))"
else
    echo "❌ python3 non trouvé"
fi

if command -v pip3 >/dev/null 2>&1; then
    echo "✅ pip3: $(which pip3)"
else
    echo "❌ pip3 non trouvé"
fi

# Vérifier l'environnement virtuel
echo
echo "🌍 ENVIRONNEMENT VIRTUEL:"
if [ -n "$VIRTUAL_ENV" ]; then
    echo "✅ Environnement virtuel actif: $VIRTUAL_ENV"
    echo "   Python: $(which python)"
    echo "   Pip: $(which pip)"
else
    echo "⚠️  Aucun environnement virtuel actif"
    if [ -d ".venv" ]; then
        echo "✅ .venv trouvé (pour l'activer: source .venv/bin/activate)"
    elif [ -d "venv" ]; then
        echo "✅ venv trouvé (pour l'activer: source venv/bin/activate)"
    else
        echo "❌ Aucun environnement virtuel trouvé"
    fi
fi

# Vérifier les fichiers du projet
echo
echo "📄 FICHIERS DU PROJET:"
files=("nmea_server.py" "nmea_server.spec" "requirements.txt" "cert.pem" "key.pem")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file ($(du -h "$file" | cut -f1))"
    else
        if [ "$file" == "cert.pem" ] || [ "$file" == "key.pem" ]; then
            echo "⚠️  $file (certificats SSL optionnels)"
        else
            echo "❌ $file MANQUANT"
        fi
    fi
done

# Vérifier les dépendances
echo
echo "📦 DÉPENDANCES PYTHON:"
if [ -f "requirements.txt" ]; then
    while read -r requirement; do
        package=$(echo "$requirement" | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'<' -f1)
        if python3 -c "import $package" 2>/dev/null; then
            echo "✅ $package"
        else
            echo "❌ $package MANQUANT"
        fi
    done < requirements.txt
else
    echo "❌ requirements.txt manquant"
fi

# Vérifier PyInstaller
echo
echo "🔧 OUTILS DE BUILD:"
if command -v pyinstaller >/dev/null 2>&1; then
    echo "✅ pyinstaller: $(which pyinstaller) ($(pyinstaller --version))"
else
    echo "❌ pyinstaller non trouvé (pour l'installer: pip install pyinstaller)"
fi

# Vérifier l'exécutable
echo
echo "🚀 EXÉCUTABLE:"
if [ -f "dist/nmea_tracker_server" ]; then
    echo "✅ dist/nmea_tracker_server ($(du -h dist/nmea_tracker_server | cut -f1))"
    echo "   Permissions: $(ls -l dist/nmea_tracker_server | cut -d' ' -f1)"
    echo "   Dernière modification: $(stat -c %y dist/nmea_tracker_server)"
else
    echo "❌ Exécutable non trouvé (pour le créer: ./scripts/linux/build.sh)"
fi

# Vérifier les ports système
echo
echo "🌐 PORTS SYSTÈME:"
if command -v ss >/dev/null 2>&1; then
    ports=(5000 5005 5006)
    for port in "${ports[@]}"; do
        if ss -tuln | grep ":$port " >/dev/null; then
            echo "⚠️  Port $port déjà utilisé"
        else
            echo "✅ Port $port disponible"
        fi
    done
elif command -v netstat >/dev/null 2>&1; then
    ports=(5000 5005 5006)
    for port in "${ports[@]}"; do
        if netstat -tuln | grep ":$port " >/dev/null; then
            echo "⚠️  Port $port déjà utilisé"
        else
            echo "✅ Port $port disponible"
        fi
    done
else
    echo "⚠️  Impossible de vérifier les ports (ss/netstat non trouvé)"
fi

# Vérifier les permissions série
echo
echo "🔌 PORTS SÉRIE:"
if ls /dev/ttyUSB* >/dev/null 2>&1; then
    for port in /dev/ttyUSB*; do
        if [ -r "$port" ] && [ -w "$port" ]; then
            echo "✅ $port (accessible)"
        else
            echo "⚠️  $port (permissions insuffisantes - utilisez: sudo chmod 666 $port)"
        fi
    done
else
    echo "⚠️  Aucun port USB série détecté"
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
echo "📋 ACTIONS RECOMMANDÉES:"
echo "   1. Pour installer l'environnement complet: ./scripts/linux/setup.sh"
echo "   2. Pour vérifier les prérequis: ./scripts/linux/check_requirements.sh" 
echo "   3. Pour compiler l'exécutable: ./scripts/linux/build.sh"
echo "   4. Pour tester l'exécutable: ./scripts/linux/test.sh"
echo
echo "   En cas de problème de ports série:"
echo "     sudo usermod -a -G dialout \$USER"
echo "     sudo chmod 666 /dev/ttyUSB0  # ou le port approprié"
echo
