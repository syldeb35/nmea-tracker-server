#!/bin/bash

echo "===== NMEA Tracker Server - Script Manager ====="
echo

# Détecter le système d'exploitation
OS="unknown"
case "$(uname -s)" in
    Linux*)     OS="linux";;
    Darwin*)    OS="macos";;
    CYGWIN*|MINGW*|MSYS*) OS="windows";;
esac

echo "🖥️  Système détecté: $OS"
echo

# Vérifier si le répertoire de scripts existe
if [ ! -d "scripts/$OS" ]; then
    echo "❌ Scripts non trouvés pour $OS"
    echo "Répertoire attendu: scripts/$OS"
    exit 1
fi

echo "📁 Scripts disponibles dans scripts/$OS/:"
echo

# Lister les scripts disponibles
if [ "$OS" = "windows" ]; then
    echo "   1. setup.bat - Installation complète"
    echo "   2. build.bat - Compilation de l'exécutable"
    echo "   3. test.bat - Test de l'exécutable"
    echo
    echo "💡 Pour Windows, utilisez directement les fichiers .bat"
    echo "   Exemple: scripts\\windows\\setup.bat"
else
    # Rendre les scripts exécutables
    chmod +x scripts/$OS/*.sh 2>/dev/null
    
    echo "   1. setup.sh - Installation complète"
    echo "   2. check_requirements.sh - Vérification des prérequis"
    echo "   3. build.sh - Compilation de l'exécutable"
    echo "   4. test.sh - Test de l'exécutable"
    echo "   5. diagnose.sh - Diagnostic complet"
    echo "   6. create_python_distribution.sh - Distribution Python portable"
    echo "   7. cross_platform_info.sh - Info build cross-platform"
    echo "   8. test_github_actions.sh - Test workflows GitHub Actions"
    echo "   9. test_crossplatform_build.sh - Test build cross-platform"
    echo "   10. validate_project.sh - Validation finale du projet"
    echo
    
    # Menu interactif
    echo "🚀 Que voulez-vous faire ?"
    echo "   [1] Installation complète (setup)"
    echo "   [2] Vérifier les prérequis"
    echo "   [3] Compiler l'exécutable"
    echo "   [4] Tester l'exécutable"
    echo "   [5] Diagnostic complet"
    echo "   [6] Créer distribution Python portable (cross-platform)"
    echo "   [7] Info build cross-platform (macOS/Windows)"
    echo "   [8] Tester workflows GitHub Actions"
    echo "   [9] Tester build cross-platform"
    echo "   [10] Validation finale du projet"
    echo "   [q] Quitter"
    echo
    
    read -p "Votre choix: " choice
    
    case $choice in
        1)
            echo "Lancement de l'installation complète..."
            ./scripts/$OS/setup.sh
            ;;
        2)
            echo "Vérification des prérequis..."
            ./scripts/$OS/check_requirements.sh
            ;;
        3)
            echo "Compilation de l'exécutable..."
            ./scripts/$OS/build.sh
            ;;
        4)
            echo "Test de l'exécutable..."
            ./scripts/$OS/test.sh
            ;;
        5)
            echo "Diagnostic complet..."
            ./scripts/$OS/diagnose.sh
            ;;
        6)
            echo "Création de la distribution Python portable..."
            ./scripts/common/create_python_distribution.sh
            ;;
        7)
            echo "Informations sur le build cross-platform..."
            ./scripts/common/cross_platform_info.sh
            ;;
        8)
            echo "Test des workflows GitHub Actions..."
            ./scripts/common/test_github_actions.sh
            ;;
        9)
            echo "Test du build cross-platform..."
            ./scripts/common/test_crossplatform_build.sh
            ;;
        10)
            echo "Validation finale du projet..."
            ./scripts/common/validate_project.sh
            ;;
        q|Q)
            echo "Au revoir !"
            exit 0
            ;;
        *)
            echo "❌ Choix invalide"
            exit 1
            ;;
    esac
fi
