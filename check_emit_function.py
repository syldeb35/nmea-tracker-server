#!/usr/bin/env python3
import re

def check_and_fix_nmea_server():
    print("🔍 Vérification de nmea_server.py...")
    
    with open('nmea_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si emit_nmea_data existe
    if 'def emit_nmea_data(' in content:
        print("✅ emit_nmea_data déjà définie")
        return
    
    print("❌ emit_nmea_data manquante, ajout en cours...")
    
    # Trouver où insérer la fonction (après les imports)
    lines = content.split('\n')
    insert_index = 0
    
    for i, line in enumerate(lines):
        if line.startswith('# Operating system detection') or line.startswith('IS_WINDOWS ='):
            insert_index = i
            break
    
    # Code à insérer
    new_code = [
        "",
        "# Variables globales pour les données NMEA en temps réel",
        "last_nmea_data = []  # Buffer des dernières données NMEA",
        "max_nmea_buffer = 50  # Garder les 50 dernières lignes",
        "",
        "def emit_nmea_data(source, message):",
        '    """Émet les données NMEA via WebSocket et les stocke"""',
        "    global last_nmea_data",
        "    ",
        "    try:",
        "        # Ajouter timestamp",
        '        timestamp = time.strftime("%H:%M:%S")',
        '        formatted_message = f"[{timestamp}][{source}] {message}"',
        "        ",
        "        # Ajouter au buffer",
        "        last_nmea_data.append(formatted_message)",
        "        if len(last_nmea_data) > max_nmea_buffer:",
        "            last_nmea_data.pop(0)",
        "        ",
        "        # Émettre via WebSocket (seulement si socketio est disponible)",
        "        try:",
        "            socketio.emit('nmea_data', {",
        "                'source': source,",
        "                'message': message,",
        "                'timestamp': timestamp,",
        "                'formatted': formatted_message",
        "            })",
        "        except Exception as ws_error:",
        "            # Si WebSocket échoue, continuer sans erreur",
        "            if 'DEBUG' in globals() and DEBUG:",
        '                print(f"[WEBSOCKET] Erreur émission: {ws_error}")',
        "                ",
        "    except Exception as e:",
        '        print(f"[EMIT] Erreur lors de l\'émission NMEA: {e}")',
        ""
    ]
    
    # Insérer le code
    lines[insert_index:insert_index] = new_code
    
    # Écrire le fichier modifié
    with open('nmea_server.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ emit_nmea_data ajoutée avec succès!")

if __name__ == "__main__":
    check_and_fix_nmea_server()
