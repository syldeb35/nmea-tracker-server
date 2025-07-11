#!/bin/bash

# Script de test local pour le build PyInstaller avec fichier .spec amélioré
# Teste le build et l'exécution de l'exécutable généré

set -e

echo "===== Test Build Local avec .spec Amélioré ====="
echo

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Répertoire du projet: $PROJECT_ROOT"
echo

# 1. Vérifications préliminaires
log_info "1. Vérifications préliminaires..."

if [ ! -f "nmea_server.py" ]; then
    log_error "nmea_server.py non trouvé"
    exit 1
fi

if [ ! -f "nmea_server.spec" ]; then
    log_error "nmea_server.spec non trouvé"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt non trouvé"
    exit 1
fi

log_success "✓ Fichiers source présents"

# 2. Vérification des dépendances
log_info "2. Vérification des dépendances..."

if ! python3 -c "import pyinstaller" 2>/dev/null; then
    log_warning "PyInstaller non installé, installation..."
    pip3 install pyinstaller
fi

# Test import du script principal
if python3 -c "import nmea_server; print('Import OK')" 2>/dev/null; then
    log_success "✓ Script Python principal importe correctement"
else
    log_error "Problème avec l'import du script principal"
    log_info "Installation des dépendances..."
    pip3 install -r requirements.txt
fi

# 3. Nettoyage des builds précédents
log_info "3. Nettoyage des builds précédents..."

rm -rf build/ dist/ __pycache__/
rm -f *.spec.bak nmea_tracker_server_test.spec

log_success "✓ Nettoyage terminé"

# 4. Création du fichier .spec de test
log_info "4. Création du fichier .spec de test..."

cp nmea_server.spec nmea_tracker_server_test.spec
sed -i "s/name='nmea_tracker_server'/name='nmea_tracker_server_test'/" nmea_tracker_server_test.spec

log_success "✓ Fichier .spec de test créé"

# 5. Build avec PyInstaller
log_info "5. Build avec PyInstaller..."

echo "Commande: pyinstaller nmea_tracker_server_test.spec"
echo

if pyinstaller nmea_tracker_server_test.spec; then
    log_success "✓ Build PyInstaller réussi"
else
    log_error "Échec du build PyInstaller"
    exit 1
fi

# 6. Vérification du fichier généré
log_info "6. Vérification du fichier généré..."

EXECUTABLE="dist/nmea_tracker_server_test"

if [ -f "$EXECUTABLE" ]; then
    log_success "✓ Exécutable généré: $EXECUTABLE"
    
    echo "Informations sur l'exécutable:"
    ls -lh "$EXECUTABLE" | sed 's/^/  /'
    file "$EXECUTABLE" | sed 's/^/  /'
else
    log_error "Exécutable non trouvé: $EXECUTABLE"
    echo "Contenu du répertoire dist/:"
    ls -la dist/ | sed 's/^/  /'
    exit 1
fi

# 7. Test d'exécution rapide
log_info "7. Test d'exécution rapide..."

echo "Test: $EXECUTABLE --help (timeout 10s)"

if timeout 10s "$EXECUTABLE" --help 2>&1; then
    log_success "✓ Test --help réussi"
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        log_warning "Timeout atteint (normal pour un serveur)"
    else
        log_error "Test --help échoué (exit code: $exit_code)"
    fi
fi

echo

# 8. Test d'import détaillé
log_info "8. Test d'import avec debug PyInstaller..."

echo "Test avec variables debug activées (timeout 15s):"

if timeout 15s env _MEIPASS_DEBUG=1 PYTHONUNBUFFERED=1 "$EXECUTABLE" --version 2>&1 | head -20; then
    log_info "Test debug terminé"
else
    log_warning "Test debug avec timeout/erreur"
fi

echo

# 9. Analyse des dépendances
log_info "9. Analyse des dépendances..."

echo "Bibliothèques liées (ldd):"
ldd "$EXECUTABLE" 2>/dev/null | head -15 | sed 's/^/  /' || log_warning "Analyse ldd échouée"

echo

# 10. Résumé et recommandations
log_info "10. Résumé et recommandations..."

echo "📊 Résultats du test:"
echo "  ✅ Build PyInstaller: OK"
echo "  ✅ Fichier généré: $(ls -lh "$EXECUTABLE" | awk '{print $5}')"
echo "  ⚠️  Test d'exécution: À vérifier manuellement"
echo

echo "🔧 Pour tester manuellement:"
echo "  1. Test basique: '$EXECUTABLE'"
echo "  2. Test debug: 'PYTHONUNBUFFERED=1 $EXECUTABLE'"
echo "  3. Test strace: 'strace $EXECUTABLE 2>&1 | tail -50'"
echo

echo "📦 Pour déployer:"
echo "  1. Copier vers GitHub Actions: git add . && git commit && git push"
echo "  2. Ou utiliser: './scripts/linux/build.sh'"
echo

if [ -f "$EXECUTABLE" ]; then
    log_success "🎉 Build local réussi ! Exécutable prêt pour test."
    echo "   Chemin: $EXECUTABLE"
else
    log_error "❌ Build local échoué."
fi

# Nettoyage optionnel
read -p "Supprimer les fichiers de build temporaires ? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf build/ nmea_tracker_server_test.spec
    log_info "Fichiers temporaires supprimés"
fi
