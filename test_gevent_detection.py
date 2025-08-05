#!/usr/bin/env python3
"""
Test du système de détection gevent et fallback
"""
import sys

# Vérifier d'abord la disponibilité de gevent avec test complet
def test_gevent_compatibility():
    try:
        import gevent
        # Test plus approfondi pour PyInstaller
        try:
            import gevent.socket
            import gevent.monkey
            # Test de création d'un greenlet simple
            from gevent import Greenlet
            def test_func():
                return True
            g = Greenlet(test_func)
            g.start()
            g.join(timeout=1)
            return True
        except Exception:
            return False
    except ImportError:
        return False

GEVENT_AVAILABLE = test_gevent_compatibility()
print(f"[DEBUG] Gevent disponible: {GEVENT_AVAILABLE}")

# Importer le serveur approprié selon la disponibilité de gevent
if GEVENT_AVAILABLE:
    try:
        print("[DEBUG] Tentative d'import nmea_server...")
        # Simulation de l'import qui pourrait échouer
        import importlib
        spec = importlib.util.spec_from_file_location("nmea_server", "nmea_server.py")
        if spec and spec.loader:
            nmea_server = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(nmea_server)
            print("[INFO] Serveur NMEA principal chargé (avec gevent)")
            NMEA_SERVER_AVAILABLE = True
        else:
            raise ImportError("Impossible de charger nmea_server.py")
    except (ImportError, ValueError) as e:
        print(f"[ERROR] Erreur import nmea_server: {e}")
        print("[INFO] Basculement vers le serveur de fallback")
        NMEA_SERVER_AVAILABLE = False
        GEVENT_AVAILABLE = False

# Si gevent n'est pas disponible ou si l'import a échoué, utiliser le fallback
if not GEVENT_AVAILABLE or not NMEA_SERVER_AVAILABLE:
    print("[FALLBACK] Utilisation du serveur HTTP alternatif")
    print("[INFO] Le système basculerait vers nmea_server_fallback.py")
    print("[SUCCESS] Test terminé - le fallback serait utilisé")
