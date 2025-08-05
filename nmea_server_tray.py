#!/usr/bin/env python3
"""
NMEA Tracker Server - System Tray Version
Application qui se lance dans la zone de notification Windows
"""

import sys
import threading
import time
import webbrowser
from pathlib import Path

# Imports spécifiques Windows pour le system tray
try:
    import pystray
    from pystray import MenuItem as item
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("[WARNING] pystray et/ou PIL non disponibles - mode console uniquement")

# Import du serveur NMEA principal avec fallback pour gevent
NMEA_SERVER_AVAILABLE = False
main_thread = None
cleanup_on_exit = None
shutdown_event = None
HTTPS_PORT = 5000
signal_handler = None
app = None
socketio = None

# Vérifier d'abord la disponibilité de gevent
try:
    import gevent
    GEVENT_AVAILABLE = True
except ImportError:
    GEVENT_AVAILABLE = False

# Importer le serveur approprié selon la disponibilité de gevent
if GEVENT_AVAILABLE:
    try:
        from nmea_server import (
            main_thread, cleanup_on_exit, shutdown_event, 
            HTTPS_PORT, signal_handler, app, socketio
        )
        NMEA_SERVER_AVAILABLE = True
        print("[INFO] Serveur NMEA principal chargé (avec gevent)")
    except ImportError as e:
        print(f"[ERROR] Erreur import nmea_server: {e}")
        NMEA_SERVER_AVAILABLE = False
else:
    print("[FALLBACK] gevent non disponible - utilisation du serveur HTTP alternatif")
    try:
        # Import dynamique du fallback
        import importlib.util
        import os
        
        # Chercher nmea_server_fallback.py dans le répertoire courant
        fallback_path = None
        possible_paths = [
            "nmea_server_fallback.py",
            os.path.join(os.path.dirname(__file__), "nmea_server_fallback.py"),
            os.path.join(sys._MEIPASS if hasattr(sys, '_MEIPASS') else ".", "nmea_server_fallback.py")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                fallback_path = path
                break
        
        if fallback_path:
            # Charger le module fallback
            spec = importlib.util.spec_from_file_location("nmea_server_fallback", fallback_path)
            fallback_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(fallback_module)
            
            # Importer les fonctions nécessaires
            main_thread = fallback_module.main_thread
            cleanup_on_exit = fallback_module.cleanup_on_exit
            shutdown_event = fallback_module.shutdown_event
            HTTPS_PORT = fallback_module.HTTPS_PORT
            signal_handler = fallback_module.signal_handler
            app = fallback_module.app
            socketio = fallback_module.socketio
            
            NMEA_SERVER_AVAILABLE = True
            print("[INFO] Serveur NMEA fallback chargé (sans gevent)")
        else:
            print("[ERROR] nmea_server_fallback.py non trouvé")
            NMEA_SERVER_AVAILABLE = False
            
    except Exception as fallback_error:
        print(f"[ERROR] Erreur chargement fallback: {fallback_error}")
        print("[ERROR] Serveur NMEA non disponible")
        print("Solution: installer gevent ou utiliser Python 3.11")
        print("  pip install gevent")
        NMEA_SERVER_AVAILABLE = False

class NMEAServerTray:
    def __init__(self):
        if not NMEA_SERVER_AVAILABLE:
            print("[ERROR] Serveur NMEA non disponible - impossible de démarrer le system tray")
            return
            
        self.icon = None
        self.server_thread = None
        self.running = False
        
    def create_image(self, color='blue'):
        """Créer une icône simple pour le system tray"""
        # Créer une image 64x64 avec un cercle
        image = Image.new('RGB', (64, 64), color='white')
        draw = ImageDraw.Draw(image)
        
        # Dessiner un cercle coloré
        if color == 'blue':
            fill_color = (0, 100, 200)
        elif color == 'green':
            fill_color = (0, 150, 0)
        elif color == 'red':
            fill_color = (200, 0, 0)
        else:
            fill_color = (100, 100, 100)
            
        draw.ellipse((8, 8, 56, 56), fill=fill_color, outline='black', width=2)
        
        # Ajouter un "N" pour NMEA
        draw.text((25, 20), "N", fill='white', font_size=20)
        
        return image

    def start_server(self):
        """Démarrer le serveur NMEA dans un thread séparé"""
        if not self.running:
            print("[TRAY] Démarrage du serveur NMEA...")
            self.running = True
            self.server_thread = threading.Thread(target=main_thread, daemon=True)
            self.server_thread.start()
            
            # Changer l'icône en vert pour indiquer que le serveur fonctionne
            if self.icon:
                self.icon.icon = self.create_image('green')
                self.icon.title = f"NMEA Server - Running on port {HTTPS_PORT}"
            
            print(f"[TRAY] Serveur démarré sur le port {HTTPS_PORT}")

    def stop_server(self):
        """Arrêter le serveur NMEA"""
        if self.running:
            print("[TRAY] Arrêt du serveur NMEA...")
            shutdown_event.set()
            self.running = False
            
            # Changer l'icône en rouge pour indiquer l'arrêt
            if self.icon:
                self.icon.icon = self.create_image('red')
                self.icon.title = "NMEA Server - Stopped"
            
            # Attendre que le thread se termine
            if self.server_thread and self.server_thread.is_alive():
                self.server_thread.join(timeout=5)
            
            cleanup_on_exit()
            print("[TRAY] Serveur arrêté")

    def open_config(self):
        """Ouvrir l'interface de configuration dans le navigateur"""
        url = f"https://localhost:{HTTPS_PORT}/config.html"
        print(f"[TRAY] Ouverture de l'interface : {url}")
        webbrowser.open(url)

    def open_dashboard(self):
        """Ouvrir le tableau de bord dans le navigateur"""
        url = f"https://localhost:{HTTPS_PORT}/"
        print(f"[TRAY] Ouverture du tableau de bord : {url}")
        webbrowser.open(url)

    def quit_app(self):
        """Quitter complètement l'application"""
        print("[TRAY] Fermeture de l'application...")
        self.stop_server()
        if self.icon:
            self.icon.stop()

    def create_menu(self):
        """Créer le menu contextuel du system tray"""
        return pystray.Menu(
            item('📊 Tableau de bord', self.open_dashboard),
            item('⚙️ Configuration', self.open_config),
            pystray.Menu.SEPARATOR,
            item('▶️ Démarrer serveur', self.start_server, 
                 enabled=lambda: not self.running),
            item('⏹️ Arrêter serveur', self.stop_server, 
                 enabled=lambda: self.running),
            pystray.Menu.SEPARATOR,
            item('❌ Quitter', self.quit_app)
        )

    def run(self):
        """Lancer l'application en mode system tray"""
        if not TRAY_AVAILABLE:
            print("[ERROR] System tray non disponible - mode console uniquement")
            print("Installez les dépendances : pip install pystray pillow")
            main_thread()
            return

        print("[TRAY] Démarrage de l'application NMEA Server...")
        print(f"[TRAY] L'icône apparaîtra dans la zone de notification")
        print(f"[TRAY] Interface web : https://localhost:{HTTPS_PORT}/config.html")
        
        # Créer l'icône système
        self.icon = pystray.Icon(
            "NMEA Server",
            self.create_image('blue'),
            f"NMEA Server - Port {HTTPS_PORT}",
            self.create_menu()
        )
        
        # Démarrer automatiquement le serveur
        self.start_server()
        
        # Lancer la boucle du system tray (bloquant)
        try:
            self.icon.run()
        except KeyboardInterrupt:
            self.quit_app()

def main():
    """Point d'entrée principal"""
    if not NMEA_SERVER_AVAILABLE:
        print("[ERROR] Serveur NMEA non disponible")
        print("Solution: installer gevent ou utiliser Python 3.11")
        print("  pip install gevent")
        sys.exit(1)
        
    if len(sys.argv) > 1:
        if sys.argv[1] == '--console':
            # Mode console classique
            print("[INFO] Mode console - utilisez Ctrl+C pour arrêter")
            main_thread()
        elif sys.argv[1] == '--diagnostic':
            # Mode diagnostic pour debug
            print("[INFO] Mode diagnostic")
            try:
                import diagnostic_executable
            except ImportError:
                print("[ERROR] Diagnostic non disponible")
                sys.exit(1)
        else:
            print("[INFO] Arguments disponibles: --console, --diagnostic")
            sys.exit(0)
    else:
        # Mode system tray
        if not TRAY_AVAILABLE:
            print("[ERROR] pystray non disponible - basculement en mode console")
            main_thread()
        else:
            tray_app = NMEAServerTray()
            if NMEA_SERVER_AVAILABLE:
                tray_app.run()

if __name__ == "__main__":
    main()
