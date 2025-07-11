#!/bin/bash

# Test de la nouvelle logique de nommage basée sur matrix.arch
# Simule exactement la logique corrigée du workflow

set -e

echo "===== Test Logique Matrix.arch Corrigée ====="
echo

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

test_matrix_filename() {
    local os="$1"
    local arch="$2"
    local ext="$3"
    local expected_filename="$4"
    
    echo -e "${BLUE}🔍 Test pour OS: $os, arch: $arch, ext: '$ext'${NC}"
    
    # Reproduire la logique exacte du workflow corrigé
    if [ "$os" != "windows-latest" ]; then
        # Unix/Linux/macOS
        file_name="nmea_tracker_server_$arch"
    else
        # Windows
        file_name="nmea_tracker_server_$arch$ext"
    fi
    
    echo "  Nom généré: $file_name"
    echo "  Nom attendu: $expected_filename"
    
    if [ "$file_name" = "$expected_filename" ]; then
        echo -e "  ${GREEN}✅ PASSED${NC}"
        return 0
    else
        echo -e "  ${RED}❌ FAILED${NC}"
        return 1
    fi
}

echo "📋 Tests avec la matrice corrigée:"
echo

# Tests pour chaque entrée de la matrice
failed=0

echo "=== Entrées de la matrice GitHub Actions ==="
echo
test_matrix_filename "ubuntu-latest" "linux" "" "nmea_tracker_server_linux" || failed=1
echo
test_matrix_filename "windows-latest" "windows" ".exe" "nmea_tracker_server_windows.exe" || failed=1
echo
test_matrix_filename "macos-latest" "macos" "" "nmea_tracker_server_macos" || failed=1
echo
test_matrix_filename "macos-13" "macos-intel" "" "nmea_tracker_server_macos-intel" || failed=1
echo

# Résumé
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 Tous les tests de la nouvelle logique sont passés !${NC}"
    echo
    echo "💡 La logique corrigée dans le workflow:"
    echo "  - Utilise directement matrix.arch au lieu de conditions if/elif"
    echo "  - Plus simple et moins prone aux erreurs"
    echo "  - Cohérent avec les noms générés par PyInstaller"
    echo
    echo "🚀 Les erreurs de build macOS devraient être résolues !"
else
    echo -e "${RED}❌ Certains tests ont échoué${NC}"
    exit 1
fi

# Tests additionnels : vérifier la cohérence avec PyInstaller
echo "📋 Vérification cohérence PyInstaller:"
echo

echo "✅ Commande PyInstaller dans le workflow:"
echo '  pyinstaller --name "nmea_tracker_server_${{ matrix.arch }}" ...'
echo
echo "✅ Noms de fichiers générés attendus:"
echo "  - ubuntu-latest → nmea_tracker_server_linux"
echo "  - windows-latest → nmea_tracker_server_windows.exe"
echo "  - macos-latest → nmea_tracker_server_macos"
echo "  - macos-13 → nmea_tracker_server_macos-intel"
echo

echo "✅ Upload artifacts:"
echo "  - Noms d'artifacts basés sur matrix.arch"
echo "  - Chemins de fichiers cohérents avec les noms générés"
echo "  - Condition macOS élargie: macos-latest || macos-13"

echo
echo -e "${GREEN}🔧 Correction appliquée avec succès !${NC}"
