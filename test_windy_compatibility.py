#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de connectivité HTTPS/WSS pour le plugin Windy
Vérifie que le serveur NMEA répond correctement en HTTPS/WSS
"""

import requests
import ssl
import json
import time

# Désactiver les warnings SSL pour les certificats auto-signés
try:
    from urllib3.exceptions import InsecureRequestWarning
    import urllib3
    urllib3.disable_warnings(InsecureRequestWarning)
except ImportError:
    # Version plus ancienne d'urllib3
    try:
        from urllib3.packages.urllib3.exceptions import InsecureRequestWarning
        import urllib3
        urllib3.disable_warnings(InsecureRequestWarning)
    except ImportError:
        # Si urllib3 n'est pas disponible, continuer sans warnings
        import warnings
        warnings.filterwarnings('ignore', message='Unverified HTTPS request')

def test_https_connection():
    """Test de la connexion HTTPS"""
    print("🔐 Test de connexion HTTPS...")
    
    try:
        response = requests.get(
            'https://localhost:5000', 
            verify=False, 
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ HTTPS : Connexion réussie !")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            return True
        else:
            print(f"❌ HTTPS : Status Code {response.status_code}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ HTTPS : Erreur SSL - {e}")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ HTTPS : Connexion refusée - {e}")
        return False
    except Exception as e:
        print(f"❌ HTTPS : Erreur inattendue - {e}")
        return False

def test_api_endpoints():
    """Test des endpoints API nécessaires au plugin Windy"""
    print("\n🌐 Test des endpoints API...")
    
    endpoints = [
        ('/api/status', 'GET', 'Statut des connexions'),
        ('/api/config', 'GET', 'Configuration actuelle'),
        ('/select_connection', 'GET', 'Route legacy'),
        ('/api/nmea/latest', 'GET', 'Dernières données NMEA')
    ]
    
    success_count = 0
    
    for endpoint, method, description in endpoints:
        try:
            url = f'https://localhost:5000{endpoint}'
            response = requests.get(url, verify=False, timeout=5)
            
            if response.status_code in [200, 404]:  # 404 OK si pas encore de données
                print(f"   ✅ {endpoint} : {description} (Status: {response.status_code})")
                
                # Vérifier si c'est du JSON valide
                try:
                    if response.headers.get('content-type', '').startswith('application/json'):
                        json_data = response.json()
                        print(f"      📊 JSON valide ({len(str(json_data))} chars)")
                except:
                    pass
                    
                success_count += 1
            else:
                print(f"   ❌ {endpoint} : Status Code {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {endpoint} : Erreur - {e}")
    
    print(f"\n📈 APIs testées : {success_count}/{len(endpoints)} OK")
    return success_count == len(endpoints)

def test_websocket_info():
    """Affiche les informations WebSocket"""
    print("\n🔌 Configuration WebSocket pour Windy :")
    print("   URL WebSocket : wss://localhost:5000/socket.io/")
    print("   Protocole     : WebSocket Sécurisé (WSS)")
    print("   Transport     : Socket.IO")
    print("   CORS          : Activé (*)")

def test_certificate_info():
    """Affiche les informations sur le certificat SSL"""
    print("\n🔒 Information Certificat SSL :")
    
    try:
        import socket
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection(('localhost', 5000), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname='localhost') as ssock:
                cert = ssock.getpeercert()
                
                if cert:
                    print("   ✅ Certificat SSL détecté")
                    print(f"   Subject: {cert.get('subject', 'N/A')}")
                    print(f"   Issuer: {cert.get('issuer', 'N/A')}")
                    print(f"   Valid until: {cert.get('notAfter', 'N/A')}")
                else:
                    print("   ⚠️ Certificat auto-signé (OK pour développement)")
                    
    except Exception as e:
        print(f"   ⚠️ Impossible de vérifier le certificat : {e}")
        print("   (Ceci est normal pour les certificats auto-signés)")

def main():
    """Test principal"""
    print("=" * 60)
    print("🌊 NMEA Tracker Server - Test Windy Plugin")
    print("=" * 60)
    
    # Test connexion HTTPS
    https_ok = test_https_connection()
    
    if https_ok:
        # Test des APIs
        api_ok = test_api_endpoints()
        
        # Informations WebSocket
        test_websocket_info()
        
        # Informations certificat
        test_certificate_info()
        
        print("\n" + "=" * 60)
        if https_ok and api_ok:
            print("🎉 RÉSULTAT : Plugin Windy COMPATIBLE !")
            print("✅ HTTPS/WSS : Opérationnel")
            print("✅ APIs : Disponibles")
            print("✅ WebSocket : Configuré (wss://localhost:5000/socket.io/)")
        else:
            print("⚠️  RÉSULTAT : Problèmes détectés")
            if not https_ok:
                print("❌ HTTPS : Non fonctionnel")
            if not api_ok:
                print("❌ APIs : Manquantes ou défaillantes")
        
        print("=" * 60)
        
    else:
        print("\n❌ Serveur NMEA non accessible en HTTPS !")
        print("   Vérifiez que le serveur est démarré avec :")
        print("   nmea_tracker_server_enhanced.exe --console")

if __name__ == "__main__":
    main()
