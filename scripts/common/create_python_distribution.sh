#!/bin/bash

echo "===== Création d'une distribution Python portable ====="
echo

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_DIR"

DIST_DIR="dist/python_portable"
ARCHIVE_NAME="nmea_tracker_server_python_portable"

echo "Nettoyage des anciens builds..."
rm -rf "$DIST_DIR"
rm -f "dist/${ARCHIVE_NAME}.tar.gz"
rm -f "dist/${ARCHIVE_NAME}.zip"

echo "Création du répertoire de distribution..."
mkdir -p "$DIST_DIR"

echo "Copie des fichiers essentiels..."
cp nmea_server.py "$DIST_DIR/"
cp requirements.txt "$DIST_DIR/"
cp cert.pem key.pem "$DIST_DIR/" 2>/dev/null || echo "Certificats non trouvés (optionnel)"
cp -r templates "$DIST_DIR/"
cp README.md "$DIST_DIR/" 2>/dev/null || echo "README.md non trouvé"

echo "Création du script de lancement universel..."
cat > "$DIST_DIR/run.py" << 'EOF'
#!/usr/bin/env python3
"""
NMEA Tracker Server - Launcher
Cross-platform Python launcher for the NMEA Tracker Server
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python():
    """Vérification de la version Python"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 ou supérieur requis")
        print(f"Version actuelle: {sys.version}")
        return False
    return True

def install_requirements():
    """Installation des dépendances"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("❌ Fichier requirements.txt non trouvé")
        return False
    
    print("📦 Installation des dépendances...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ])
        return True
    except subprocess.CalledProcessError:
        print("❌ Échec de l'installation des dépendances")
        return False

def main():
    """Point d'entrée principal"""
    print("🚢 NMEA Tracker Server - Démarrage")
    print("=" * 50)
    
    if not check_python():
        sys.exit(1)
    
    # Vérification des dépendances
    try:
        import flask
        import serial
        import socketio
    except ImportError:
        print("📋 Installation des dépendances manquantes...")
        if not install_requirements():
            sys.exit(1)
    
    # Lancement du serveur
    server_file = Path(__file__).parent / "nmea_server.py"
    if not server_file.exists():
        print("❌ nmea_server.py non trouvé")
        sys.exit(1)
    
    print("🚀 Lancement du serveur NMEA...")
    try:
        subprocess.call([sys.executable, str(server_file)])
    except KeyboardInterrupt:
        print("\n👋 Arrêt du serveur")

if __name__ == "__main__":
    main()
EOF

echo "Création du script de lancement macOS..."
cat > "$DIST_DIR/run_macos.sh" << 'EOF'
#!/bin/bash
# NMEA Tracker Server - Launcher pour macOS

echo "🍎 NMEA Tracker Server - macOS"
echo "================================"

# Vérification de Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo "❌ Python non trouvé!"
    echo "Installez Python depuis https://python.org ou avec Homebrew:"
    echo "brew install python"
    exit 1
fi

echo "🐍 Python trouvé: $($PYTHON_CMD --version)"

# Vérification de pip
if ! $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
    echo "❌ pip non trouvé!"
    echo "Installez pip avec: $PYTHON_CMD -m ensurepip --upgrade"
    exit 1
fi

# Installation des dépendances
echo "📦 Installation des dépendances..."
$PYTHON_CMD -m pip install -r requirements.txt

# Lancement
echo "🚀 Lancement du serveur..."
$PYTHON_CMD nmea_server.py
EOF

echo "Création des instructions d'installation..."
cat > "$DIST_DIR/INSTALL.md" << 'EOF'
# 🚢 NMEA Tracker Server - Installation

## 📋 Prérequis

- **Python 3.8+** (requis)
- **pip** (généralement inclus avec Python)

## 🖥️ Installation par OS

### 🍎 macOS

1. **Installer Python** (si nécessaire):
   ```bash
   # Avec Homebrew (recommandé)
   brew install python
   
   # Ou télécharger depuis python.org
   ```

2. **Lancer le serveur**:
   ```bash
   chmod +x run_macos.sh
   ./run_macos.sh
   ```

### 🐧 Linux

1. **Installer Python** (si nécessaire):
   ```bash
   sudo apt update && sudo apt install python3 python3-pip  # Ubuntu/Debian
   sudo dnf install python3 python3-pip                     # Fedora
   ```

2. **Lancer le serveur**:
   ```bash
   python3 run.py
   ```

### 🪟 Windows

1. **Installer Python** depuis [python.org](https://python.org)
   - ✅ Cocher "Add Python to PATH"

2. **Lancer le serveur**:
   ```cmd
   python run.py
   ```

## 🌐 Accès à l'interface

Une fois démarré, ouvrez votre navigateur sur:
- **Interface principale**: https://localhost:5000/
- **Configuration**: https://localhost:5000/config.html

## 🔧 Configuration

1. Accédez à la page de configuration
2. Sélectionnez vos types de connexion (Serial/UDP/TCP)
3. Configurez les paramètres réseau et série
4. Cliquez sur "Apply"

## 📚 Support

- Documentation complète dans README.md
- Issues: [GitHub Repository]
EOF

chmod +x "$DIST_DIR/run.py"
chmod +x "$DIST_DIR/run_macos.sh"

echo "Création des archives..."
cd dist

# Archive ZIP (Windows/macOS friendly)
zip -r "${ARCHIVE_NAME}.zip" python_portable/
echo "✅ Archive ZIP créée: dist/${ARCHIVE_NAME}.zip"

# Archive TAR.GZ (Linux/macOS friendly)
tar -czf "${ARCHIVE_NAME}.tar.gz" python_portable/
echo "✅ Archive TAR.GZ créée: dist/${ARCHIVE_NAME}.tar.gz"

cd ..

echo
echo "🎉 DISTRIBUTION PYTHON PORTABLE CRÉÉE !"
echo
echo "📁 Contenu:"
echo "  - Serveur NMEA Python"
echo "  - Scripts de lancement cross-platform"
echo "  - Instructions d'installation"
echo "  - Tous les fichiers nécessaires"
echo
echo "📦 Archives disponibles:"
echo "  - dist/${ARCHIVE_NAME}.zip (pour Windows/macOS)"
echo "  - dist/${ARCHIVE_NAME}.tar.gz (pour Linux/macOS)"
echo
echo "🚀 Les utilisateurs macOS peuvent maintenant:"
echo "  1. Télécharger et extraire l'archive"
echo "  2. Exécuter: ./run_macos.sh"
echo "  3. Profiter du serveur NMEA !"
