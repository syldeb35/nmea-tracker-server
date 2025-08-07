#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de correction automatique des caractères Unicode problématiques
Corrige tous les fichiers Python du projet
"""

import os
import re
import glob

def fix_unicode_chars(content):
    """Remplace les caractères Unicode problématiques par des équivalents ASCII"""
    
    # Dictionnaire de remplacement
    replacements = {
        '→': '->',      # U+2192 RIGHTWARDS ARROW
        '✅': 'OK',     # U+2705 WHITE HEAVY CHECK MARK  
        '❌': 'ERROR',  # U+274C CROSS MARK
        '🛑': 'STOP',   # U+1F6D1 STOP SIGN
        '⚠️': 'WARNING', # U+26A0 WARNING SIGN
        '📡': '[GPS]',  # U+1F4E1 SATELLITE ANTENNA
        '🔧': '[TOOL]', # U+1F527 WRENCH
        '🚀': '[START]',# U+1F680 ROCKET
        '📊': '[STATS]',# U+1F4CA BAR CHART
        '🆕': '[NEW]',  # U+1F195 NEW BUTTON
        '✓': 'OK',      # U+2713 CHECK MARK
        '⏸': '[PAUSE]', # U+23F8 PAUSE BUTTON
        '▶': '[PLAY]',  # U+25B6 PLAY BUTTON
        '⏹': '[STOP]',  # U+23F9 STOP BUTTON
        '🔴': '[ERROR]', # U+1F534 RED CIRCLE
        '🟢': '[OK]',    # U+1F7E2 GREEN CIRCLE
        '🟡': '[WARN]',  # U+1F7E1 YELLOW CIRCLE
        '⚡': '[FAST]',  # U+26A1 HIGH VOLTAGE
        '🔄': '[SYNC]',  # U+1F504 COUNTERCLOCKWISE
        '📝': '[LOG]',   # U+1F4DD MEMO
        '🌐': '[NET]',   # U+1F310 GLOBE
        '📶': '[SIGNAL]', # U+1F4F6 ANTENNA BARS
        
        # Caractères avec accents qui peuvent poser problème
        'é': 'e',
        'è': 'e',
        'à': 'a',
        'ù': 'u',
        'ç': 'c',
        'ê': 'e',
        'â': 'a',
        'î': 'i',
        'ô': 'o',
        'û': 'u',
        'ë': 'e',
        'ï': 'i',
        'ü': 'u',
        'ö': 'o',
        'ä': 'a',
    }
    
    # Appliquer tous les remplacements
    for unicode_char, ascii_replacement in replacements.items():
        content = content.replace(unicode_char, ascii_replacement)
    
    return content

def fix_file(filepath):
    """Corrige un fichier Python"""
    try:
        print(f"Correction de {filepath}...")
        
        # Lire le fichier
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Compter les caractères problématiques avant
        original_content = content
        
        # Appliquer les corrections
        fixed_content = fix_unicode_chars(content)
        
        # Vérifier s'il y a eu des changements
        if original_content != fixed_content:
            # Sauvegarder le fichier corrigé
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  ✓ Fichier corrigé: {filepath}")
            return True
        else:
            print(f"  - Aucune correction nécessaire: {filepath}")
            return False
            
    except Exception as e:
        print(f"  ✗ Erreur lors de la correction de {filepath}: {e}")
        return False

def main():
    print("========================================")
    print("  CORRECTION DES CARACTÈRES UNICODE")
    print("========================================")
    print()
    
    # Liste des fichiers Python à corriger
    python_files = [
        "nmea_server.py",
        "nmea_server_test.py",
        "nmea_server_manager.py", 
        "nmea_server_tray.py",
    ]
    
    # Ajouter tous les fichiers .py du répertoire courant
    all_py_files = glob.glob("*.py")
    for py_file in all_py_files:
        if py_file not in python_files:
            python_files.append(py_file)
    
    files_corrected = 0
    files_processed = 0
    
    for filename in python_files:
        if os.path.exists(filename):
            files_processed += 1
            if fix_file(filename):
                files_corrected += 1
        else:
            print(f"  - Fichier non trouvé: {filename}")
    
    print()
    print("========================================")
    print("           RÉSUMÉ")
    print("========================================")
    print(f"Fichiers traités: {files_processed}")
    print(f"Fichiers corrigés: {files_corrected}")
    print()
    
    if files_corrected > 0:
        print("✓ Corrections appliquées avec succès!")
        print("Vous pouvez maintenant relancer vos applications.")
    else:
        print("- Aucune correction nécessaire.")
    
    print()
    return files_corrected

if __name__ == "__main__":
    main()
