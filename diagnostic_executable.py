#!/usr/bin/env python3
"""
Diagnostic des modules disponibles dans l'exécutable PyInstaller
"""

import sys
import os

print("=== DIAGNOSTIC PYINSTALLER ===")
print(f"Exécutable: {sys.executable}")
print(f"Version Python: {sys.version}")
print(f"Répertoire courant: {os.getcwd()}")

# Vérifier si nous sommes dans un bundle PyInstaller
if hasattr(sys, '_MEIPASS'):
    print(f"PyInstaller bundle détecté: {sys._MEIPASS}")
    bundle_files = []
    try:
        for root, dirs, files in os.walk(sys._MEIPASS):
            for file in files:
                if file.endswith('.py') or file.endswith('.pyc'):
                    bundle_files.append(os.path.relpath(os.path.join(root, file), sys._MEIPASS))
        
        print(f"\nFichiers Python dans le bundle ({len(bundle_files)}):")
        for file in sorted(bundle_files)[:20]:  # Montrer les 20 premiers
            print(f"  {file}")
        if len(bundle_files) > 20:
            print(f"  ... et {len(bundle_files) - 20} autres")
            
    except Exception as e:
        print(f"Erreur lecture bundle: {e}")
else:
    print("Exécution en mode développement (pas PyInstaller)")

print("\n=== TEST DES MODULES CRITIQUES ===")

critical_modules = [
    'flask',
    'flask_socketio', 
    'flask_cors',
    'socketio',
    'serial',
    'logging.handlers',
    'dotenv',
    'threading',
    'importlib.util'
]

available = []
missing = []

for module in critical_modules:
    try:
        __import__(module)
        available.append(module)
        print(f"✅ {module}")
    except ImportError as e:
        missing.append(module)
        print(f"❌ {module} - {e}")

print(f"\n=== RÉSUMÉ ===")
print(f"✅ Disponibles: {len(available)}")
print(f"❌ Manquants: {len(missing)}")

if missing:
    print(f"\nModules manquants critiques:")
    for module in missing:
        print(f"  - {module}")

# Test spécifique pour le fallback
print(f"\n=== TEST FALLBACK ===")
try:
    # Chercher nmea_server_fallback dans différents emplacements
    fallback_paths = [
        "nmea_server_fallback.py",
        os.path.join(os.path.dirname(__file__), "nmea_server_fallback.py")
    ]
    
    if hasattr(sys, '_MEIPASS'):
        fallback_paths.append(os.path.join(sys._MEIPASS, "nmea_server_fallback.py"))
    
    fallback_found = False
    for path in fallback_paths:
        if os.path.exists(path):
            print(f"✅ Fallback trouvé: {path}")
            fallback_found = True
            break
    
    if not fallback_found:
        print(f"❌ nmea_server_fallback.py introuvable")
        print(f"Chemins testés:")
        for path in fallback_paths:
            print(f"  - {path}")

except Exception as e:
    print(f"❌ Erreur test fallback: {e}")

print(f"\nDiagnostic terminé.")
