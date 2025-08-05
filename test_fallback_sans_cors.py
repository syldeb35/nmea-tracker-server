#!/usr/bin/env python3
"""
Test du fallback sans flask_cors
"""

print("Test du fallback sans flask_cors...")

# Simuler l'absence de flask_cors
import sys
import importlib

# Sauvegarder l'import original
original_import = __builtins__.__import__

def mock_import(name, *args, **kwargs):
    if name == 'flask_cors':
        raise ImportError("No module named 'flask_cors'")
    return original_import(name, *args, **kwargs)

# Remplacer temporairement l'import
__builtins__.__import__ = mock_import

try:
    print("Tentative d'import du fallback sans flask_cors...")
    import nmea_server_fallback
    print("✅ Import réussi !")
    print(f"CORS disponible: {nmea_server_fallback.CORS_AVAILABLE}")
    
    # Test rapide des fonctions principales
    if hasattr(nmea_server_fallback, 'app'):
        print("✅ Flask app créée")
    if hasattr(nmea_server_fallback, 'socketio'):
        print("✅ SocketIO initialisé")
    if hasattr(nmea_server_fallback, 'main_thread'):
        print("✅ main_thread disponible")
        
    print("\n🎉 Le fallback fonctionne sans flask_cors !")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    # Restaurer l'import original
    __builtins__.__import__ = original_import

print("\nTest terminé.")
