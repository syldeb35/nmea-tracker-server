#!/usr/bin/env python3
"""
Test rapide des imports requis pour le fallback
"""

print("Test des dépendances pour nmea_server_fallback...")
print("=" * 50)

required_modules = [
    'flask',
    'flask_socketio', 
    'flask_cors',
    'socketio',
    'serial',
    'serial.tools.list_ports',
    'logging.handlers',
    'dotenv',
    'threading',
    'importlib.util',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'cryptography',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.x509',
]

missing_modules = []
available_modules = []

for module in required_modules:
    try:
        __import__(module)
        available_modules.append(module)
        print(f"✅ {module}")
    except ImportError as e:
        missing_modules.append(module)
        print(f"❌ {module} - {e}")

print("\n" + "=" * 50)
print("RÉSUMÉ:")
print(f"✅ Modules disponibles: {len(available_modules)}")
print(f"❌ Modules manquants: {len(missing_modules)}")

if missing_modules:
    print("\nModules manquants:")
    for module in missing_modules:
        print(f"  - {module}")
    print("\nSolution: pip install", " ".join(missing_modules))
else:
    print("\n🎉 Tous les modules requis sont disponibles !")
    print("Le fallback devrait fonctionner correctement.")

print("\nTest terminé.")
