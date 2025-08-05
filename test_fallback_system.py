#!/usr/bin/env python3
"""
Test du système de fallback gevent
Vérifie que les imports fonctionnent correctement
"""

print("Test du système de fallback gevent...")
print("=" * 50)

# Test 1: Import direct du serveur principal
print("\n1. Test import nmea_server (avec gevent):")
try:
    import nmea_server
    print("✅ nmea_server importé avec succès")
    has_gevent = True
except ImportError as e:
    if "gevent" in str(e):
        print("⚠️ nmea_server échec (gevent non disponible)")
        has_gevent = False
    else:
        print(f"❌ nmea_server échec: {e}")
        has_gevent = False

# Test 2: Import du serveur fallback
print("\n2. Test import nmea_server_fallback (sans gevent):")
try:
    import nmea_server_fallback
    print("✅ nmea_server_fallback importé avec succès")
    has_fallback = True
except ImportError as e:
    print(f"❌ nmea_server_fallback échec: {e}")
    has_fallback = False

# Test 3: Import de nmea_server_tray avec fallback
print("\n3. Test import nmea_server_tray (avec fallback automatique):")
try:
    import nmea_server_tray
    if nmea_server_tray.NMEA_SERVER_AVAILABLE:
        print("✅ nmea_server_tray importé avec serveur disponible")
    else:
        print("⚠️ nmea_server_tray importé mais serveur non disponible")
except ImportError as e:
    print(f"❌ nmea_server_tray échec: {e}")

# Test 4: Import de nmea_server_service avec fallback  
print("\n4. Test import nmea_server_service (avec fallback automatique):")
try:
    import nmea_server_service
    if nmea_server_service.NMEA_SERVER_AVAILABLE:
        print("✅ nmea_server_service importé avec serveur disponible")
    else:
        print("⚠️ nmea_server_service importé mais serveur non disponible")
except ImportError as e:
    print(f"❌ nmea_server_service échec: {e}")

# Résumé
print("\n" + "=" * 50)
print("RÉSUMÉ:")
print(f"• gevent disponible: {'✅ Oui' if has_gevent else '❌ Non'}")
print(f"• Fallback disponible: {'✅ Oui' if has_fallback else '❌ Non'}")

if has_gevent:
    print("→ Utilisation recommandée: nmea_server.py (optimal)")
elif has_fallback:
    print("→ Utilisation recommandée: nmea_server_fallback.py (compatible)")
else:
    print("→ Aucun serveur disponible - installer les dépendances")

print("\nTest terminé.")
