#!/bin/bash

echo "===== Test Local du Workflow GitHub Actions ====="
echo

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "🔍 Vérification de la structure du projet..."
echo

# Vérification des fichiers essentiels
files_to_check=(
    "nmea_server.py"
    "requirements.txt"
    "templates/index.html"
    "templates/config.html"
    "templates/favicon.svg"
)

missing_files=()
for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (MANQUANT)"
        missing_files+=("$file")
    fi
done

echo

# Vérification des fichiers optionnels
optional_files=(
    "cert.pem"
    "key.pem"
    ".env"
)

echo "📋 Fichiers optionnels:"
for file in "${optional_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file (présent)"
    else
        echo "⚠️  $file (manquant - sera créé automatiquement)"
    fi
done

echo

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "❌ ERREUR: Fichiers essentiels manquants!"
    echo "Créez ces fichiers avant de continuer:"
    for file in "${missing_files[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

echo "🐍 Test d'import Python..."
if python3 -c "import nmea_server; print('✅ Import Python réussi')" 2>/dev/null; then
    echo "✅ Le script Python s'importe correctement"
else
    echo "❌ Erreur d'import Python"
    echo "Vérifiez les dépendances avec: pip install -r requirements.txt"
    exit 1
fi

echo

echo "📦 Test de création de la distribution Python..."
if [ -f "scripts/common/create_python_distribution.sh" ]; then
    chmod +x scripts/common/create_python_distribution.sh
    if ./scripts/common/create_python_distribution.sh > /dev/null 2>&1; then
        echo "✅ Distribution Python créée avec succès"
        
        # Vérification des archives
        if [ -f "dist/nmea_tracker_server_python_portable.zip" ]; then
            size=$(du -h dist/nmea_tracker_server_python_portable.zip | cut -f1)
            echo "  📁 Archive ZIP: $size"
        fi
        
        if [ -f "dist/nmea_tracker_server_python_portable.tar.gz" ]; then
            size=$(du -h dist/nmea_tracker_server_python_portable.tar.gz | cut -f1)
            echo "  📁 Archive TAR.GZ: $size"
        fi
    else
        echo "❌ Échec de création de la distribution Python"
        exit 1
    fi
else
    echo "❌ Script de distribution manquant"
    exit 1
fi

echo

echo "🔧 Création des fichiers SSL temporaires pour test..."
if [ ! -f "cert.pem" ]; then
    echo "# Dummy certificate for testing" > cert.pem
    echo "✅ cert.pem temporaire créé"
fi

if [ ! -f "key.pem" ]; then
    echo "# Dummy key for testing" > key.pem
    echo "✅ key.pem temporaire créé"
fi

echo

echo "🏗️  Test de build PyInstaller (optionnel)..."
echo "Ce test peut prendre plusieurs minutes..."

if command -v pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller détecté, test de build..."
    
    # Nettoyage
    rm -rf build/ dist/nmea_tracker_server* 2>/dev/null
    
    # Test de build simple
    if pyinstaller --onefile --clean --noconfirm nmea_server.spec > build_test.log 2>&1; then
        if [ -f "dist/nmea_tracker_server" ] || [ -f "dist/nmea_tracker_server.exe" ]; then
            echo "✅ Build PyInstaller réussi"
            
            # Affichage de la taille
            for exe in dist/nmea_tracker_server*; do
                if [ -f "$exe" ]; then
                    size=$(du -h "$exe" | cut -f1)
                    echo "  📦 Exécutable: $(basename "$exe") ($size)"
                fi
            done
        else
            echo "❌ Build PyInstaller échoué (exécutable non trouvé)"
            echo "Logs dans build_test.log"
        fi
    else
        echo "❌ Build PyInstaller échoué"
        echo "Logs dans build_test.log"
    fi
else
    echo "⚠️  PyInstaller non installé, test ignoré"
    echo "Pour installer: pip install pyinstaller"
fi

echo

echo "🧹 Nettoyage des fichiers temporaires..."
rm -f cert.pem key.pem build_test.log 2>/dev/null

echo

echo "🎉 TEST TERMINÉ !"
echo
echo "📋 Résumé:"
echo "  ✅ Structure de projet validée"
echo "  ✅ Import Python fonctionnel"
echo "  ✅ Distribution Python créée"
echo
echo "🚀 Votre projet est prêt pour GitHub Actions !"
echo
echo "💡 Pour déclencher le workflow:"
echo "   1. Committez et poussez vos changements"
echo "   2. Créez un tag: git tag v1.0.0 && git push --tags"
echo "   3. Ou utilisez 'workflow_dispatch' depuis l'interface GitHub"
