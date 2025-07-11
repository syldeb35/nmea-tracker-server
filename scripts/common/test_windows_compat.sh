#!/bin/bash

echo "===== Test de compatibilité Windows (simulation encodage) ====="
echo

# Test avec différents encodages pour simuler Windows
test_encoding() {
    local description="$1"
    local command="$2"
    
    echo "🔍 Test: $description"
    
    # Simulation d'un environnement plus strict (sans emojis)
    if echo "$command" | grep -q "✅\|❌\|🚀\|🔧"; then
        echo "❌ ERREUR: Emoji détecté dans la commande"
        echo "  Commande: $command"
        echo "  → Problème d'encodage potentiel sur Windows"
        return 1
    else
        echo "✅ OK: Pas d'emoji détecté"
        
        # Exécution de la commande
        if eval "$command" > /dev/null 2>&1; then
            echo "✅ Commande exécutée avec succès"
            return 0
        else
            echo "❌ Échec de la commande"
            return 1
        fi
    fi
}

echo "📋 Tests des commandes du workflow GitHub Actions..."
echo

# Test 1: Commande d'import
test_encoding "Import avec version Python" \
    'python3 -c "import nmea_server, sys; print(\"[OK] Success on Python \" + sys.version.split()[0])"'

echo

# Test 2: Commande de vérification des templates
test_encoding "Vérification des templates" \
    'python3 -c "from pathlib import Path; templates = Path(\"templates\"); assert templates.exists(); print(\"[OK] Templates verification passed\")"'

echo

# Test 3: Test d'une commande avec emoji (devrait échouer)
echo "🔍 Test de détection d'emoji (doit échouer):"
test_encoding "Test avec emoji (volontairement)" \
    'python3 -c "print(\"✅ This should fail\")"'

echo

echo "📊 Résumé:"
echo "  - Les commandes du workflow sont maintenant compatibles Windows"
echo "  - Plus d'emojis Unicode dans les outputs Python"
echo "  - Utilisation de [OK], [FAIL], etc. à la place"

echo
echo "💡 Pour tester sur un vrai Windows:"
echo "  - Utilisez une VM Windows ou WSL"
echo "  - Ou attendez la validation GitHub Actions"
