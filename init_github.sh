#!/bin/bash

echo "🚀 Initialisation du repository GitHub NMEA Tracker Server"
echo

# Vérifier si git est installé
if ! command -v git &> /dev/null; then
    echo "❌ Git n'est pas installé. Installez-le d'abord."
    exit 1
fi

# Vérifier si on est dans un repo git
if [ ! -d ".git" ]; then
    echo "📁 Initialisation du repository git..."
    git init
else
    echo "📁 Repository git déjà initialisé"
fi

# Ajouter tous les fichiers
echo "📋 Ajout des fichiers..."
git add .

# Premier commit
if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "💾 Premier commit..."
    git commit -m "🎉 Initial commit: NMEA Tracker Server v1.0.0

✨ Fonctionnalités:
- Serveur NMEA/AIS temps réel (Série, UDP, TCP)  
- Interface web moderne avec carte Leaflet.js
- Décodeur NMEA (GGA, RMC, GLL, VTG, HDT)
- Configuration web intuitive
- Exécutable autonome PyInstaller
- Support multi-plateforme
- Gestion d'arrêt propre (Ctrl+C)
- Icône personnalisée et certificats SSL"

else
    echo "💾 Mise à jour du commit..."
    git add .
    git commit -m "📝 Ajout documentation GitHub complète

- README.md professionnel avec badges
- LICENSE MIT  
- CHANGELOG.md détaillé
- .gitignore Python optimisé
- Scripts d'initialisation GitHub"
fi

echo
echo "📋 Instructions pour publier sur GitHub:"
echo
echo "1. Créez un nouveau repository sur GitHub:"
echo "   https://github.com/new"
echo
echo "2. Nommez-le: nmea-tracker-server"
echo
echo "3. Liez votre repository local:"
echo "   git remote add origin https://github.com/VOTRE_USERNAME/nmea-tracker-server.git"
echo
echo "4. Poussez votre code:"
echo "   git branch -M main"
echo "   git push -u origin main"
echo
echo "✅ Votre projet est prêt pour GitHub !"
echo
echo "🔗 N'oubliez pas de:"
echo "   - Modifier VOTRE_USERNAME dans README.md"
echo "   - Ajouter votre email de contact"
echo "   - Créer des releases avec les exécutables"
echo "   - Activer GitHub Pages si souhaité"
