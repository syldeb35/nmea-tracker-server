#!/bin/bash

echo "===== Test des commandes GitHub Actions en local ====="
echo

# Couleurs pour les outputs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

failed_tests=0
total_tests=0

# Fonction de test
run_test() {
    local test_name="$1"
    local command="$2"
    
    total_tests=$((total_tests + 1))
    echo -e "${YELLOW}[TEST $total_tests]${NC} $test_name"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "Command: $command"
        failed_tests=$((failed_tests + 1))
    fi
    echo
}

echo "🔍 Tests des commandes du workflow Python..."
echo

# Test 1: Import Python basique
run_test "Import nmea_server" \
    "python3 -c 'import nmea_server; print(\"OK\")'"

# Test 2: Import avec version Python (syntaxe corrigée)
run_test "Import avec version Python" \
    "python3 -c 'import nmea_server, sys; print(\"✅ Success on Python \" + sys.version.split()[0])'"

# Test 3: Vérification templates
run_test "Vérification des templates" \
    "python3 -c 'from pathlib import Path; templates = Path(\"templates\"); assert templates.exists(); assert (templates / \"index.html\").exists(); assert (templates / \"config.html\").exists(); print(\"✅ Templates verification passed\")'"

# Test 4: Installation des dépendances
run_test "Test requirements.txt" \
    "python3 -m pip install -r requirements.txt > /dev/null 2>&1"

# Test 5: Script de distribution Python
run_test "Création distribution Python" \
    "[ -x scripts/common/create_python_distribution.sh ] && ./scripts/common/create_python_distribution.sh > /dev/null 2>&1"

# Test 6: Vérification des fichiers essentiels
run_test "Fichiers essentiels présents" \
    "[ -f nmea_server.py ] && [ -f requirements.txt ] && [ -d templates ]"

# Test 7: Syntax check du fichier principal
run_test "Vérification syntaxe Python" \
    "python3 -m py_compile nmea_server.py"

echo "📊 Résumé des tests:"
echo "  Total: $total_tests"
echo -e "  ${GREEN}Réussis: $((total_tests - failed_tests))${NC}"

if [ $failed_tests -gt 0 ]; then
    echo -e "  ${RED}Échoués: $failed_tests${NC}"
    echo
    echo -e "${RED}❌ Certains tests ont échoué !${NC}"
    echo "Corrigez les erreurs avant de pousser sur GitHub."
    exit 1
else
    echo -e "  ${RED}Échoués: 0${NC}"
    echo
    echo -e "${GREEN}🎉 Tous les tests sont passés !${NC}"
    echo "Votre code est prêt pour GitHub Actions."
fi

echo
echo "💡 Pour déclencher les workflows GitHub Actions:"
echo "   git add . && git commit -m 'Fix workflow syntax' && git push"
echo "   # Ou pour un build complet:"
echo "   git tag v1.0.2 && git push --tags"
