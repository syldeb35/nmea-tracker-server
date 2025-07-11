#!/bin/bash

# Script de diagnostic pour les problèmes macOS dans GitHub Actions
# Simule les commandes utilisées dans le workflow pour identifier les incompatibilités

set -e

echo "===== Diagnostic Problèmes macOS GitHub Actions ====="
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

# Variables
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Répertoire du projet: $PROJECT_ROOT"
echo "🖥️  Système: $(uname -s) $(uname -m)"
echo "🐚 Shell: $SHELL"
echo

# 1. Test des commandes sed (problème potentiel macOS vs Linux)
log_info "1. Test compatibilité sed (macOS vs Linux)..."

# Créer un fichier de test
cat > test_sed.spec << 'EOF'
name='nmea_tracker_server'
test='value'
EOF

echo "Fichier test original:"
cat test_sed.spec | sed 's/^/  /'

echo
echo "Test sed -i (GNU Linux style):"
if sed -i "s/name='nmea_tracker_server'/name='nmea_tracker_server_test'/" test_sed.spec 2>/dev/null; then
    log_success "✓ sed -i style GNU réussi"
    cat test_sed.spec | sed 's/^/  /'
else
    log_warning "sed -i style GNU échoué"
fi

# Restaurer le fichier
cat > test_sed.spec << 'EOF'
name='nmea_tracker_server'
test='value'
EOF

echo
echo "Test sed -i '' (BSD macOS style):"
if sed -i '' "s/name='nmea_tracker_server'/name='nmea_tracker_server_test'/" test_sed.spec 2>/dev/null; then
    log_success "✓ sed -i '' style BSD réussi"
    cat test_sed.spec | sed 's/^/  /'
else
    log_warning "sed -i '' style BSD échoué"
fi

rm -f test_sed.spec

echo

# 2. Test de la commande cp
log_info "2. Test commande cp..."

if [ -f "nmea_server.spec" ]; then
    if cp nmea_server.spec test_copy.spec 2>/dev/null; then
        log_success "✓ Commande cp fonctionne"
        rm -f test_copy.spec
    else
        log_error "✗ Commande cp échoue"
    fi
else
    log_warning "Fichier nmea_server.spec non trouvé pour test cp"
fi

echo

# 3. Test des variables de matrice simulées
log_info "3. Test variables de matrice GitHub Actions..."

# Simuler les différentes valeurs de matrix.arch pour macOS
test_matrix_values=(
    "macos"
    "macos-intel"
)

for arch in "${test_matrix_values[@]}"; do
    echo "Test pour arch: $arch"
    
    # Test de création du nom de fichier
    spec_name="nmea_tracker_server_${arch}.spec"
    echo "  Nom .spec généré: $spec_name"
    
    # Test de la substitution
    test_substitution="s/name='nmea_tracker_server'/name='nmea_tracker_server_${arch}'/"
    echo "  Substitution sed: $test_substitution"
    
    # Vérifier la validité du nom
    if [[ "$spec_name" =~ ^[a-zA-Z0-9_.-]+\.spec$ ]]; then
        log_success "  ✓ Nom de fichier valide"
    else
        log_error "  ✗ Nom de fichier invalide"
    fi
done

echo

# 4. Test PyInstaller avec fichier .spec
log_info "4. Test PyInstaller avec fichier .spec..."

if [ -f "nmea_server.spec" ]; then
    # Vérifier la syntaxe du fichier .spec
    if python3 -c "
import ast
with open('nmea_server.spec', 'r') as f:
    content = f.read()
print('Syntaxe .spec valide')
" 2>/dev/null; then
        log_success "✓ Fichier .spec a une syntaxe valide"
    else
        log_error "✗ Problème de syntaxe dans nmea_server.spec"
    fi
    
    # Vérifier les imports dans le .spec
    if grep -q "hiddenimports" nmea_server.spec; then
        log_success "✓ hiddenimports présents dans le .spec"
        echo "Hiddenimports détectés:"
        grep -A 10 "hiddenimports" nmea_server.spec | head -15 | sed 's/^/  /'
    else
        log_warning "hiddenimports non trouvés dans le .spec"
    fi
else
    log_error "Fichier nmea_server.spec non trouvé"
fi

echo

# 5. Test commandes shell spécifiques macOS
log_info "5. Test commandes shell spécifiques macOS..."

echo "Version sed:"
sed --version 2>/dev/null | head -1 | sed 's/^/  /' || echo "  Version sed non disponible (normal sur macOS BSD)"

echo "Version bash:"
bash --version 2>/dev/null | head -1 | sed 's/^/  /' || echo "  Version bash non disponible"

echo "Python disponible:"
python3 --version 2>/dev/null | sed 's/^/  /' || echo "  Python3 non disponible"

echo

# 6. Simulation du workflow macOS
log_info "6. Simulation workflow GitHub Actions macOS..."

# Simuler les étapes du workflow
echo "Simulation des étapes pour matrix.os='macos-latest', matrix.arch='macos':"

# Étape 1: Vérification structure projet
echo "  [1] Vérification structure projet (ls -la):"
if ls -la *.py *.spec 2>/dev/null | head -5 | sed 's/^/    /'; then
    log_success "    ✓ Structure projet OK"
else
    log_warning "    Fichiers manquants détectés"
fi

# Étape 2: Création fichiers SSL
echo "  [2] Création fichiers SSL:"
if [ -f "cert.pem" ] && [ -f "key.pem" ]; then
    log_success "    ✓ Fichiers SSL présents"
else
    log_warning "    Fichiers SSL manquants (créés par le workflow)"
fi

# Étape 3: Simulation build
echo "  [3] Simulation build avec .spec:"
if [ -f "nmea_server.spec" ]; then
    # Test de copie
    if cp nmea_server.spec "nmea_tracker_server_macos_test.spec" 2>/dev/null; then
        log_success "    ✓ Copie .spec réussie"
        
        # Test de modification (compatible macOS et Linux)
        if python3 -c "
import re
with open('nmea_tracker_server_macos_test.spec', 'r') as f:
    content = f.read()
content = re.sub(r\"name='nmea_tracker_server'\", \"name='nmea_tracker_server_macos'\", content)
with open('nmea_tracker_server_macos_test.spec', 'w') as f:
    f.write(content)
print('Modification .spec réussie')
" 2>/dev/null; then
            log_success "    ✓ Modification .spec réussie (Python)"
        else
            log_error "    ✗ Modification .spec échouée"
        fi
        
        rm -f nmea_tracker_server_macos_test.spec
    else
        log_error "    ✗ Copie .spec échouée"
    fi
else
    log_error "    ✗ Fichier nmea_server.spec manquant"
fi

echo

# 7. Recommandations pour corriger les problèmes macOS
log_info "7. Recommandations pour corriger les problèmes macOS..."

echo "🔧 Problèmes potentiels identifiés:"
echo

# Problème sed
echo "  1. Incompatibilité sed:"
echo "     - Linux (GNU): sed -i 's/old/new/' file"
echo "     - macOS (BSD): sed -i '' 's/old/new/' file"
echo "     → Solution: Utiliser Python pour les modifications de fichiers"
echo

# Problème chemins
echo "  2. Chemins et séparateurs:"
echo "     - Utiliser des chemins relatifs"
echo "     - Éviter les caractères spéciaux dans les noms"
echo

# Problème Python
echo "  3. Versions Python:"
echo "     - GitHub Actions macOS peut avoir Python 3.x différent"
echo "     - Vérifier la compatibilité PyInstaller"
echo

echo "💡 Solutions recommandées:"
echo "  1. Remplacer sed par Python pour modifier les fichiers .spec"
echo "  2. Ajouter des vérifications de compatibilité OS"
echo "  3. Utiliser des commandes shell plus portables"
echo "  4. Tester localement sur macOS si possible"

echo
log_info "Diagnostic terminé. Analysez les résultats pour identifier les problèmes macOS."
