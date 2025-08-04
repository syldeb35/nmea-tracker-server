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

# Import du serveur NMEA principal
from nmea_server import (
    main_thread, cleanup_on_exit, shutdown_event, 
    HTTPS_PORT, signal_handler, app, socketio
)

class NMEAServerTray:
    def __init__(self):
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
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        # Mode console classique
        print("[INFO] Mode console - utilisez Ctrl+C pour arrêter")
        main_thread()
    else:
        # Mode system tray
        tray_app = NMEAServerTray()
        tray_app.run()

if __name__ == "__main__":
    main()
