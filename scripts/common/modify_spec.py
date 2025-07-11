#!/usr/bin/env python3
"""
Script pour modifier le nom dans les fichiers .spec de PyInstaller
Compatible macOS et Linux - évite les problèmes sed
"""
import re
import sys
import os

def modify_spec_file(spec_file, arch):
    """Modifie le nom de l'exécutable dans un fichier .spec"""
    if not os.path.exists(spec_file):
        print(f"❌ Erreur: Fichier {spec_file} non trouvé")
        return False
    
    try:
        # Lire le fichier
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Modifier le nom
        new_name = f"nmea_tracker_server_{arch}"
        content = re.sub(
            r"name='nmea_tracker_server'",
            f"name='{new_name}'",
            content
        )
        
        # Écrire le fichier modifié
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Fichier {spec_file} modifié: nom = '{new_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la modification de {spec_file}: {e}")
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 modify_spec.py <spec_file> <arch>")
        print("Exemple: python3 modify_spec.py nmea_tracker_server_macos.spec macos")
        sys.exit(1)
    
    spec_file = sys.argv[1]
    arch = sys.argv[2]
    
    success = modify_spec_file(spec_file, arch)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
