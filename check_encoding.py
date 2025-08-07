#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validation de l'encodage pour nmea_server_test.py
Vérifie qu'aucun caractère Unicode problématique n'est présent
"""

import re
import sys

def check_unicode_issues(filename):
    """Vérifie les problèmes d'encodage Unicode dans un fichier"""
    
    # Caractères problématiques qui causent des erreurs d'encodage cp1252
    problematic_chars = [
        '→',  # U+2192 RIGHTWARDS ARROW
        '✅',  # U+2705 WHITE HEAVY CHECK MARK  
        '❌',  # U+274C CROSS MARK
        '🛑',  # U+1F6D1 STOP SIGN
        '⚠️',  # U+26A0 WARNING SIGN
        '📡',  # U+1F4E1 SATELLITE ANTENNA
        '🔧',  # U+1F527 WRENCH
        '🚀',  # U+1F680 ROCKET
        '📊',  # U+1F4CA BAR CHART
    ]
    
    issues_found = []
    line_number = 0
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, 1):
                for char in problematic_chars:
                    if char in line:
                        issues_found.append({
                            'line': line_number,
                            'char': char,
                            'context': line.strip()[:100] + ('...' if len(line.strip()) > 100 else '')
                        })
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier: {e}")
        return None
    
    return issues_found

def main():
    filename = "nmea_server_test.py"
    print(f"Vérification des caractères Unicode problématiques dans {filename}...")
    print("=" * 60)
    
    issues = check_unicode_issues(filename)
    
    if issues is None:
        print("❌ Impossible de vérifier le fichier")
        return 1
    
    if not issues:
        print("✅ Aucun caractère Unicode problématique trouvé!")
        print("Le fichier devrait compiler sans erreur d'encodage.")
    else:
        print(f"❌ {len(issues)} problème(s) trouvé(s):")
        print()
        for issue in issues:
            print(f"Ligne {issue['line']}: caractère '{issue['char']}'")
            print(f"  Context: {issue['context']}")
            print()
        
        print("Corrections suggérées:")
        print("→  remplacer par  ->")
        print("✅  remplacer par  OK")
        print("❌  remplacer par  ERROR")  
        print("🛑  remplacer par  STOP")
    
    print("=" * 60)
    return len(issues)

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
