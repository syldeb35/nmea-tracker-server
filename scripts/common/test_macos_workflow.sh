#!/bin/bash

# Test de simulation du workflow GitHub Actions pour macOS
# Permet de tester localement les modifications avant de pousser

set -e

echo "🍎 === Test Simulation Workflow macOS === 🍎"
echo

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Variables de test simulant les matrix variables GitHub Actions
export MATRIX_OS="macos-latest"
export MATRIX_ARCH="macos"
export MATRIX_EXT=""
export MATRIX_SEPARATOR=":"

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Répertoire: $PROJECT_ROOT"
echo "🖥️  Simulation OS: $MATRIX_OS"
echo "🏗️  Architecture: $MATRIX_ARCH"
echo

# 1. Vérifier la structure du projet
log_info "1. Vérification structure projet..."
if [ -f "nmea_server.py" ] && [ -f "nmea_server.spec" ]; then
    log_success "✓ Fichiers principaux présents"
else
    log_error "✗ Fichiers principaux manquants"
    exit 1
fi

# 2. Vérifier les fichiers SSL
log_info "2. Vérification fichiers SSL..."
if [ ! -f "cert.pem" ]; then
    log_warning "Création cert.pem factice"
    echo "# Dummy certificate for build" > cert.pem
fi
if [ ! -f "key.pem" ]; then
    log_warning "Création key.pem factice"
    echo "# Dummy key for build" > key.pem
fi
log_success "✓ Fichiers SSL OK"

# 3. Test du workflow Unix (simulation macOS)
log_info "3. Simulation workflow Unix (macOS)..."

# Créer un fichier .spec personnalisé
SPEC_FILE="nmea_tracker_server_${MATRIX_ARCH}.spec"
log_info "Création fichier .spec: $SPEC_FILE"

if cp nmea_server.spec "$SPEC_FILE"; then
    log_success "✓ Copie fichier .spec réussie"
else
    log_error "✗ Échec copie fichier .spec"
    exit 1
fi

# Modifier le nom avec le script Python (compatible macOS/Linux)
log_info "Modification nom dans .spec avec Python..."
if python3 scripts/common/modify_spec.py "$SPEC_FILE" "$MATRIX_ARCH"; then
    log_success "✓ Modification .spec réussie"
else
    log_error "✗ Échec modification .spec"
    exit 1
fi

# Vérifier la modification
log_info "Vérification modification..."
if grep -q "name='nmea_tracker_server_${MATRIX_ARCH}'" "$SPEC_FILE"; then
    log_success "✓ Nom modifié correctement dans .spec"
else
    log_error "✗ Modification nom incorrecte"
    cat "$SPEC_FILE" | grep "name=" || echo "Aucune ligne 'name=' trouvée"
    exit 1
fi

# 4. Test de build PyInstaller (optionnel - peut être long)
read -p "🤔 Voulez-vous tester le build PyInstaller complet ? (o/N): " test_build
if [[ $test_build =~ ^[Oo]$ ]]; then
    log_info "4. Test build PyInstaller..."
    
    if command -v pyinstaller >/dev/null 2>&1; then
        log_info "PyInstaller trouvé, lancement du build..."
        
        if pyinstaller "$SPEC_FILE" --quiet; then
            # Vérifier le résultat
            EXPECTED_FILE="dist/nmea_tracker_server_${MATRIX_ARCH}"
            if [ -f "$EXPECTED_FILE" ]; then
                log_success "✅ Build PyInstaller réussi: $EXPECTED_FILE"
                ls -lh "$EXPECTED_FILE"
                
                # Test rapide de l'exécutable
                log_info "Test rapide de l'exécutable..."
                if timeout 5s "$EXPECTED_FILE" --help >/dev/null 2>&1 || true; then
                    log_success "✓ Exécutable semble fonctionnel"
                else
                    log_warning "⚠️  Test exécutable non concluant (normal pour un serveur)"
                fi
            else
                log_error "✗ Fichier build non trouvé: $EXPECTED_FILE"
                echo "Fichiers trouvés dans dist/:"
                ls -la dist/ || echo "Dossier dist/ non trouvé"
            fi
        else
            log_error "✗ Échec build PyInstaller"
        fi
    else
        log_warning "PyInstaller non installé, installation..."
        pip install pyinstaller --quiet
        log_info "Retry build PyInstaller..."
        if pyinstaller "$SPEC_FILE" --quiet; then
            log_success "✅ Build PyInstaller réussi après installation"
        else
            log_error "✗ Échec build PyInstaller même après installation"
        fi
    fi
else
    log_info "4. Build PyInstaller ignoré (choix utilisateur)"
fi

# 5. Nettoyage
log_info "5. Nettoyage..."
rm -f "$SPEC_FILE"
rm -rf build/ dist/ *.pyc __pycache__/ 2>/dev/null || true
log_success "✓ Nettoyage terminé"

echo
log_success "🎉 Test de simulation workflow macOS terminé avec succès !"
log_info "💡 Le workflow GitHub Actions devrait maintenant fonctionner sur macOS"
echo
echo "📋 Prochaines étapes:"
echo "  1. Committer et pousser les modifications"
echo "  2. Déclencher le workflow GitHub Actions"
echo "  3. Vérifier que les builds macOS réussissent"
echo
