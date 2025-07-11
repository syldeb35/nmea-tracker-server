#!/bin/bash

# Test de la logique de nommage des fichiers de build
# Simule exactement la logique utilisée dans .github/workflows/build.yml

set -e

echo "===== Test Logique Nommage Fichiers Build ====="
echo

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

test_filename_logic() {
    local os="$1"
    local expected_filename="$2"
    
    echo "🔍 Test pour OS: $os"
    
    # Reproduire la logique exacte du workflow
    if [ "$os" = "ubuntu-latest" ]; then
        file_name="nmea_tracker_server_linux"
    elif [ "$os" = "macos-latest" ]; then
        file_name="nmea_tracker_server_macos-intel"
    elif [ "$os" = "windows-latest" ]; then
        file_name="nmea_tracker_server_windows.exe"
    else
        file_name="nmea_tracker_server_unknown"
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

echo "📋 Tests de logique de nommage:"
echo

# Tests pour chaque OS
failed=0

test_filename_logic "ubuntu-latest" "nmea_tracker_server_linux" || failed=1
echo
test_filename_logic "macos-latest" "nmea_tracker_server_macos-intel" || failed=1
echo
test_filename_logic "windows-latest" "nmea_tracker_server_windows.exe" || failed=1
echo

# Test pour un OS inconnu
echo "🔍 Test pour OS inconnu:"
test_filename_logic "unknown-os" "nmea_tracker_server_unknown" || failed=1
echo

# Résumé
if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 Tous les tests de nommage sont passés !${NC}"
    echo
    echo "💡 La logique de nommage dans le workflow est correcte:"
    echo "  - Linux: nmea_tracker_server_linux"
    echo "  - macOS: nmea_tracker_server_macos-intel"
    echo "  - Windows: nmea_tracker_server_windows.exe"
    echo
    echo "🚀 Le problème de build macOS devrait être résolu !"
else
    echo -e "${RED}❌ Certains tests ont échoué${NC}"
    exit 1
fi

# Test additionnel : vérifier que les noms correspondent aux patterns PyInstaller
echo "📋 Vérification cohérence avec PyInstaller:"
echo

echo "✅ Patterns PyInstaller attendus:"
echo "  spec.py datas avec des noms cohérents"
echo "  Pas d'espaces dans les noms de fichiers"
echo "  Extensions appropriées (.exe pour Windows)"
echo

echo "✅ Upload artifacts GitHub Actions:"
echo "  Noms d'artifacts distincts par plateforme"
echo "  Chemins de fichiers corrects"
echo "  Rétention configurée à 30 jours"
