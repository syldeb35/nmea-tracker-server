#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMEA Server System Tray Application
Application de gestion du serveur NMEA depuis la barre système
"""

import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import pystray
from pystray import MenuItem as item
import webbrowser
import psutil
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tray_app.log'),
        logging.StreamHandler()
    ]
)

class NMEAServerTray:
    def __init__(self):
        self.server_process = None
        self.server_running = False
        self.icon = None
        self.server_script = "nmea_server_test.py"
        self.server_executable = "nmea_tracker_server2.exe"
        
        # Vérifier si l'exécutable existe, sinon utiliser le script Python
        if os.path.exists(self.server_executable):
            self.server_command = [self.server_executable]
        elif os.path.exists(self.server_script):
            self.server_command = [sys.executable, self.server_script]
        else:
            logging.error("Ni l'exécutable ni le script Python n'ont été trouvés!")
            messagebox.showerror("Erreur", "Impossible de trouver le serveur NMEA!")
            sys.exit(1)
        
        # Créer le dossier logs s'il n'existe pas
        os.makedirs('logs', exist_ok=True)
        
        self.setup_icon()
        
    def create_icon_image(self, is_running=False):
        """Crée une icône colorée selon l'état du serveur"""
        try:
            # Essayer de charger l'icône personnalisée comme base
            if os.path.exists("icon.png"):
                base_image = Image.open("icon.png").convert('RGBA')
                # Redimensionner si nécessaire
                base_image = base_image.resize((64, 64), Image.Resampling.LANCZOS)
                
                # Appliquer une teinte colorée selon l'état
                overlay = Image.new('RGBA', (64, 64), (0, 255, 0, 100) if is_running else (255, 0, 0, 100))
                image = Image.alpha_composite(base_image, overlay)
            else:
                # Créer une icône simple colorée
                color = (0, 200, 0, 255) if is_running else (200, 0, 0, 255)  # Vert ou Rouge
                image = Image.new('RGBA', (64, 64), color)
                
                # Ajouter un cercle plus foncé au centre pour plus de visibilité
                draw = ImageDraw.Draw(image)
                center_color = (0, 150, 0, 255) if is_running else (150, 0, 0, 255)
                draw.ellipse([16, 16, 48, 48], fill=center_color)
                
            return image
            
        except Exception as e:
            logging.warning(f"Impossible de créer l'icône: {e}")
            # Icône de fallback colorée
            color = (0, 200, 0, 255) if is_running else (200, 0, 0, 255)
            return Image.new('RGBA', (64, 64), color)

    def setup_icon(self):
        """Configure l'icône du system tray"""
        # Créer l'icône initiale (serveur arrêté = rouge)
        image = self.create_icon_image(is_running=False)
        
        # Créer le menu contextuel
        menu = pystray.Menu(
            item('Démarrer le serveur', self.start_server, enabled=lambda item: not self.server_running),
            item('Arrêter le serveur', self.stop_server, enabled=lambda item: self.server_running),
            pystray.Menu.SEPARATOR,
            item('Ouvrir l\'interface web', self.open_web_interface, enabled=lambda item: self.server_running),
            item('Ouvrir la page de configuration', self.open_config_interface, enabled=lambda item: self.server_running),
            item('Voir les logs', self.view_logs),
            pystray.Menu.SEPARATOR,
            item('À propos', self.show_about),
            item('Quitter', self.quit_application)
        )
        
        # Créer l'icône système
        self.icon = pystray.Icon(
            "NMEA Server",
            image,
            "NMEA Tracker Server",
            menu
        )
        
    def update_icon_status(self, is_running):
        """Met à jour la couleur de l'icône selon l'état du serveur"""
        try:
            if self.icon:
                new_image = self.create_icon_image(is_running)
                self.icon.icon = new_image
                # Mettre à jour aussi le tooltip
                status_text = "En cours d'exécution" if is_running else "Arrêté"
                self.icon.title = f"NMEA Tracker Server - {status_text}"
                logging.debug(f"Icône mise à jour: {'Vert' if is_running else 'Rouge'}")
        except Exception as e:
            logging.error(f"Erreur mise à jour icône: {e}")
        
    def start_server(self, icon=None, item=None):
        """Démarre le serveur NMEA"""
        if self.server_running:
            logging.info("Le serveur est déjà en cours d'exécution")
            return
            
        try:
            logging.info(f"Démarrage du serveur: {' '.join(self.server_command)}")
            
            # Démarrer le serveur en mode sans console (CREATE_NO_WINDOW sur Windows)
            startupinfo = None
            creation_flags = 0
            
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.server_process = subprocess.Popen(
                self.server_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=creation_flags,
                cwd=os.getcwd()
            )
            
            self.server_running = True
            logging.info(f"Serveur démarré avec PID: {self.server_process.pid}")
            
            # Mettre à jour l'icône en vert
            self.update_icon_status(True)
            
            # Démarrer un thread pour surveiller le serveur
            threading.Thread(target=self.monitor_server, daemon=True).start()
            
            # Notification
            if self.icon:
                self.icon.notify("Serveur NMEA démarré", "Le serveur est maintenant en cours d'exécution")
                
        except Exception as e:
            logging.error(f"Erreur lors du démarrage du serveur: {e}")
            messagebox.showerror("Erreur", f"Impossible de démarrer le serveur:\n{e}")
            
    def stop_server(self, icon=None, item=None):
        """Arrête le serveur NMEA"""
        if not self.server_running:
            logging.info("Le serveur n'est pas en cours d'exécution")
            return
            
        try:
            logging.info("Arrêt du serveur...")
            
            if self.server_process:
                # Essayer d'arrêter proprement le processus
                if sys.platform == "win32":
                    # Sur Windows, utiliser terminate
                    self.server_process.terminate()
                else:
                    # Sur Unix, utiliser SIGTERM
                    self.server_process.terminate()
                
                # Attendre un peu pour un arrêt propre
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Forcer l'arrêt si nécessaire
                    logging.warning("Arrêt forcé du serveur")
                    self.server_process.kill()
                    self.server_process.wait()
                
                self.server_process = None
                
            # Essayer aussi de tuer tout processus restant
            self.kill_remaining_processes()
            
            self.server_running = False
            logging.info("Serveur arrêté")
            
            # Mettre à jour l'icône en rouge
            self.update_icon_status(False)
            
            # Notification
            if self.icon:
                self.icon.notify("Serveur NMEA arrêté", "Le serveur a été arrêté")
                
        except Exception as e:
            logging.error(f"Erreur lors de l'arrêt du serveur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'arrêt du serveur:\n{e}")
            
    def kill_remaining_processes(self):
        """Tue tous les processus du serveur NMEA qui pourraient encore tourner"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Chercher les processus qui correspondent à notre serveur
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if ('nmea_server_test.py' in cmdline or 
                            'nmea_tracker_server2.exe' in cmdline):
                            logging.info(f"Arrêt du processus restant: PID {proc.info['pid']}")
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logging.error(f"Erreur lors du nettoyage des processus: {e}")
            
    def monitor_server(self):
        """Surveille le serveur pour détecter s'il s'arrête inopinément"""
        while self.server_running and self.server_process:
            try:
                # Vérifier si le processus est toujours vivant
                if self.server_process.poll() is not None:
                    logging.warning("Le serveur s'est arrêté inopinément")
                    self.server_running = False
                    # Mettre à jour l'icône en rouge
                    self.update_icon_status(False)
                    if self.icon:
                        self.icon.notify("Serveur arrêté", "Le serveur s'est arrêté inopinément")
                    break
                    
                time.sleep(2)  # Vérifier toutes les 2 secondes
            except Exception as e:
                logging.error(f"Erreur dans la surveillance du serveur: {e}")
                break
                
    def open_web_interface(self, icon=None, item=None):
        """Ouvre l'interface web du serveur"""
        if not self.server_running:
            messagebox.showwarning("Serveur arrêté", "Le serveur doit être démarré pour ouvrir l'interface web")
            return
            
        try:
            webbrowser.open('https://localhost:5000')
            logging.info("Interface web ouverte")
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture de l'interface web: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'interface web:\n{e}")
            
    def open_config_interface(self, icon=None, item=None):
        """Ouvre l'interface web du serveur"""
        if not self.server_running:
            messagebox.showwarning("Serveur arrêté", "Le serveur doit être démarré pour ouvrir l'interface web")
            return
            
        try:
            webbrowser.open('https://localhost:5000/config.html')
            logging.info("Interface web ouverte")
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture de l'interface web: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'interface web:\n{e}")
            
    def view_logs(self, icon=None, item=None):
        """Ouvre le dossier des logs"""
        try:
            if sys.platform == "win32":
                os.startfile(os.path.abspath('logs'))
            elif sys.platform == "darwin":
                subprocess.Popen(['open', os.path.abspath('logs')])
            else:
                subprocess.Popen(['xdg-open', os.path.abspath('logs')])
        except Exception as e:
            logging.error(f"Erreur lors de l'ouverture du dossier logs: {e}")
            
    def show_about(self, icon=None, item=None):
        """Affiche les informations sur l'application"""
        messagebox.showinfo(
            "À propos",
            "NMEA Tracker Server - System Tray\n\n"
            "Gestionnaire du serveur NMEA depuis la barre système.\n"
            "Permet de démarrer/arrêter le serveur et d'accéder à l'interface web.\n\n"
            "Version: 1.0"
        )
        
    def quit_application(self, icon=None, item=None):
        """Quitte l'application"""
        if self.server_running:
            if messagebox.askyesno("Confirmation", "Le serveur est en cours d'exécution. Voulez-vous l'arrêter et quitter?"):
                self.stop_server()
            else:
                return
                
        logging.info("Fermeture de l'application tray")
        if self.icon:
            self.icon.stop()
        sys.exit(0)
        
    def run(self):
        """Lance l'application system tray"""
        logging.info("Démarrage de l'application NMEA Server Tray")
        try:
            self.icon.run()
        except KeyboardInterrupt:
            self.quit_application()

def main():
    """Point d'entrée principal"""
    try:
        app = NMEAServerTray()
        app.run()
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
        messagebox.showerror("Erreur fatale", f"Une erreur fatale s'est produite:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
