#!/bin/bash

echo "===== NMEA Tracker Server - Cross-Platform Build Documentation ====="
echo

cat << 'EOF'
🚫 LIMITATION IMPORTANTE: 
Vous ne pouvez pas créer un exécutable macOS natif depuis Linux/Windows.

✅ SOLUTIONS DISPONIBLES:

1. 📦 DISTRIBUTION PYTHON (Recommandé)
   - Fonctionne sur tous les OS avec Python installé
   - Plus léger et plus compatible
   - Voir: scripts/python_distribution.sh

2. 🐳 DOCKER CONTAINER
   - Cross-platform par nature
   - Fonctionne sur macOS avec Docker Desktop
   - Voir: docker build -t nmea-server .

3. 🤖 GITHUB ACTIONS (Build automatique)
   - Builds automatiques sur macOS runners
   - Voir: .github/workflows/build.yml
   - Activez en créant un tag: git tag v1.0.0 && git push --tags

4. 📋 INSTRUCTIONS POUR UTILISATEURS MACOS
   - Fournir des instructions d'installation Python
   - Script d'installation automatique

🎯 RECOMMANDATION:
Pour distribution macOS, utilisez la solution Python + script d'installation
au lieu d'un exécutable compilé.

EOF

echo "Voulez-vous créer un package Python distributable ? (y/N)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo
    echo "Création du package Python..."
    ./scripts/common/create_python_distribution.sh
else
    echo
    echo "Pour plus d'informations, consultez le README.md"
fi
