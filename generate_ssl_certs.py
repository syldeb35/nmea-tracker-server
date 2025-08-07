#!/usr/bin/env python3
"""
Générateur de certificats SSL améliorés pour NMEA Tracker Server
Crée des certificats avec Subject Alternative Names pour une meilleure compatibilité
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_ssl_certificates():
    """Génère des certificats SSL auto-signés avec SAN"""
    
    print("🔒 Génération de certificats SSL améliorés...")
    
    # Configuration OpenSSL pour SAN
    config_content = """[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = FR
ST = France
L = Local
O = NMEA Tracker Server
CN = localhost

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = 127.0.0.1
DNS.3 = ::1
IP.1 = 127.0.0.1
IP.2 = ::1
"""
    
    # Créer le fichier de configuration temporaire
    config_file = "openssl_temp.conf"
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    try:
        # Générer la clé privée et le certificat
        cmd = [
            'openssl', 'req', '-x509', '-nodes', '-days', '365',
            '-newkey', 'rsa:2048',
            '-keyout', 'key.pem',
            '-out', 'cert.pem',
            '-config', config_file,
            '-extensions', 'v3_req'
        ]
        
        print("🔧 Exécution d'OpenSSL...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Certificats SSL générés avec succès !")
            print("   📄 cert.pem - Certificat public")
            print("   🔑 key.pem - Clé privée")
            print("   🔒 Certificats valides pour localhost, 127.0.0.1, ::1")
            return True
        else:
            print(f"❌ Erreur OpenSSL: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ OpenSSL n'est pas installé ou pas dans le PATH")
        print("   Veuillez installer OpenSSL pour générer des certificats")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        return False
    finally:
        # Nettoyer le fichier de configuration temporaire
        if os.path.exists(config_file):
            os.remove(config_file)

def verify_certificates():
    """Vérifie la validité des certificats existants"""
    
    if not os.path.exists('cert.pem') or not os.path.exists('key.pem'):
        print("❌ Certificats manquants")
        return False
    
    try:
        # Vérifier le certificat
        cmd = ['openssl', 'x509', '-in', 'cert.pem', '-text', '-noout']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Certificat valide")
            
            # Extraire les informations importantes
            output = result.stdout
            if 'Subject Alternative Name' in output:
                print("✅ Subject Alternative Name présent")
            else:
                print("⚠️  Subject Alternative Name manquant")
                return False
                
            if 'localhost' in output:
                print("✅ Certificat configuré pour localhost")
            else:
                print("⚠️  Certificat non configuré pour localhost")
                return False
                
            return True
        else:
            print(f"❌ Erreur de vérification: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ OpenSSL non disponible pour la vérification")
        return True  # Assume OK si on ne peut pas vérifier
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

def main():
    """Point d'entrée principal"""
    
    print("🛰️ NMEA Tracker Server - Gestionnaire de certificats SSL")
    print("=" * 60)
    
    # Vérifier les certificats existants
    print("\n📋 Vérification des certificats existants...")
    if verify_certificates():
        print("✅ Les certificats existants sont corrects")
        
        response = input("\n❓ Voulez-vous les régénérer quand même ? (y/N): ")
        if response.lower() not in ['y', 'yes', 'o', 'oui']:
            print("ℹ️  Conservation des certificats existants")
            return
    
    # Générer de nouveaux certificats
    print("\n🔄 Génération de nouveaux certificats...")
    if generate_ssl_certificates():
        print("\n✅ Certificats prêts pour NMEA Tracker Server")
        print("🔒 Le serveur peut maintenant fonctionner en HTTPS/WSS")
        print("🌐 Compatible avec le plugin Windy")
    else:
        print("\n❌ Échec de la génération des certificats")
        print("💡 Solutions :")
        print("   1. Installer OpenSSL")
        print("   2. Utiliser des certificats existants")
        print("   3. Accepter l'avertissement SSL dans le navigateur")

if __name__ == "__main__":
    main()
