#!/bin/bash

# Script de diagnostic pour l'exécutable Linux généré par PyInstaller
# Aide à identifier les problèmes d'exécution

set -e

echo "===== Diagnostic Exécutable Linux ====="
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
EXECUTABLE_PATH="$1"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ -z "$EXECUTABLE_PATH" ]; then
    log_error "Usage: $0 <path_to_executable>"
    echo "Example: $0 ./nmea_tracker_server_linux"
    exit 1
fi

echo "📁 Répertoire du projet: $PROJECT_ROOT"
echo "🚀 Exécutable à tester: $EXECUTABLE_PATH"
echo

# 1. Vérifications préliminaires
log_info "1. Vérifications préliminaires..."

if [ ! -f "$EXECUTABLE_PATH" ]; then
    log_error "Fichier exécutable non trouvé: $EXECUTABLE_PATH"
    exit 1
fi

if [ ! -x "$EXECUTABLE_PATH" ]; then
    log_error "Fichier non exécutable: $EXECUTABLE_PATH"
    echo "Correction: chmod +x '$EXECUTABLE_PATH'"
    exit 1
fi

log_success "✓ Fichier exécutable trouvé et permissions OK"

# 2. Informations sur l'exécutable
log_info "2. Informations sur l'exécutable..."

echo "Type de fichier:"
file "$EXECUTABLE_PATH" | sed 's/^/  /'

echo "Taille:"
ls -lh "$EXECUTABLE_PATH" | awk '{print "  " $5 " (" $9 ")"}'

echo "Permissions:"
ls -l "$EXECUTABLE_PATH" | awk '{print "  " $1 " " $3 ":" $4}'

# 3. Test avec affichage détaillé des erreurs
log_info "3. Test d'exécution avec diagnostic..."

echo "Tentative d'exécution avec capture d'erreurs..."
echo "Commande: '$EXECUTABLE_PATH' --help"
echo

# Test 1: --help
if timeout 10s "$EXECUTABLE_PATH" --help 2>&1; then
    log_success "✓ Option --help fonctionne"
else
    exit_code=$?
    log_warning "Option --help a échoué (exit code: $exit_code)"
fi

echo
echo "----------------------------------------"
echo

# Test 2: Exécution normale avec timeout et capture
log_info "Test d'exécution normale (timeout 15s)..."
echo

if timeout 15s "$EXECUTABLE_PATH" 2>&1; then
    log_success "✓ Exécution normale réussie"
else
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        log_warning "Timeout atteint (15s) - Le serveur semble démarrer mais ne se termine pas"
        log_info "C'est normal pour un serveur web en mode daemon"
    else
        log_error "Échec d'exécution (exit code: $exit_code)"
    fi
fi

echo
echo "----------------------------------------"
echo

# 4. Tests avec variables d'environnement debug
log_info "4. Test avec debug PyInstaller..."

echo "Variables d'environnement debug activées:"
echo "  _MEIPASS debug, PYTHONPATH debug"
echo

if timeout 10s env _MEIPASS_DEBUG=1 PYTHONUNBUFFERED=1 "$EXECUTABLE_PATH" --version 2>&1 || true; then
    log_info "Test debug PyInstaller terminé"
fi

echo
echo "----------------------------------------"
echo

# 5. Vérification des dépendances système
log_info "5. Vérification des dépendances système..."

echo "Bibliothèques liées (ldd):"
if ldd "$EXECUTABLE_PATH" 2>/dev/null | head -20 | sed 's/^/  /'; then
    log_success "✓ Analyse ldd réussie"
else
    log_warning "Analyse ldd échouée ou exécutable statique"
fi

echo

# 6. Vérification environnement Python
log_info "6. Vérification environnement système..."

echo "Python disponible:"
python3 --version 2>/dev/null | sed 's/^/  /' || echo "  Python3 non disponible"

echo "Bibliothèques Python installées (sélection):"
pip3 list 2>/dev/null | grep -E "(flask|pyserial|gevent)" | sed 's/^/  /' || echo "  Informations pip non disponibles"

echo

# 7. Recommandations de debug
log_info "7. Recommandations de debug..."

echo "🔧 Pour plus de détails sur l'erreur:"
echo "  1. Exécuter avec strace: strace '$EXECUTABLE_PATH' 2>&1 | tail -50"
echo "  2. Vérifier les logs système: journalctl -f"
echo "  3. Exécuter en mode verbose: '$EXECUTABLE_PATH' -v"
echo

echo "🐍 Pour tester le script Python original:"
echo "  cd '$PROJECT_ROOT'"
echo "  python3 nmea_server.py"
echo

echo "📦 Pour reconstruire l'exécutable:"
echo "  cd '$PROJECT_ROOT'"
echo "  ./scripts/linux/build.sh"
echo

# 8. Test rapide du script Python original si disponible
if [ -f "$PROJECT_ROOT/nmea_server.py" ]; then
    log_info "8. Test rapide du script Python original..."
    
    cd "$PROJECT_ROOT"
    if timeout 5s python3 -c "import nmea_server; print('Import OK')" 2>&1; then
        log_success "✓ Script Python original importe sans erreur"
    else
        log_error "✗ Problème avec le script Python original"
        echo "  Vérifiez les dépendances: pip3 install -r requirements.txt"
    fi
else
    log_warning "Script Python original non trouvé dans $PROJECT_ROOT"
fi

echo
log_info "Diagnostic terminé. Analysez les messages ci-dessus pour identifier le problème."
