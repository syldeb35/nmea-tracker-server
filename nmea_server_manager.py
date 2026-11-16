#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMEA Server System Tray Application (Version simplifiée)
Application de gestion du serveur NMEA depuis la barre système
"""

import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox, Menu
import webbrowser
import logging
from tkinter import simpledialog

# Configuration du logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tray_app.log'),
        logging.StreamHandler()
    ]
)

class NMEAServerTraySimple:
    def __init__(self):
        self.server_process = None
        self.server_running = False
        self.root = None
        self.server_script = "nmea_server.py"
        self.server_executable = "nmea_tracker_server.exe"
        
        # Vérifier si l'exécutable existe, sinon utiliser le script Python
        if os.path.exists(self.server_executable):
            self.server_command = [self.server_executable]
        elif os.path.exists(self.server_script):
            self.server_command = [sys.executable, self.server_script]
        else:
            logging.error("Ni l'exécutable ni le script Python n'ont été trouvés!")
            messagebox.showerror("Erreur", "Impossible de trouver le serveur NMEA!")
            sys.exit(1)
        
        self.setup_gui()
        
    def setup_gui(self):
        """Configure l'interface graphique simplifiée"""
        self.root = tk.Tk()
        self.root.title("NMEA Server Manager")
        self.root.geometry("400x300")
        self.root.resizable(False, False)
        
        # Essayer de définir une icône
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Frame principal
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titre
        title_label = tk.Label(main_frame, text="NMEA Tracker Server", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Status
        self.status_label = tk.Label(main_frame, text="Statut: Arrêté", 
                                   font=("Arial", 12))
        self.status_label.pack(pady=(0, 20))
        
        # Boutons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=(0, 20))
        
        self.start_button = tk.Button(button_frame, text="Démarrer le serveur", 
                                    command=self.start_server, width=20, height=2)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = tk.Button(button_frame, text="Arrêter le serveur", 
                                   command=self.stop_server, width=20, height=2,
                                   state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)
        
        # Boutons additionnels
        web_button = tk.Button(main_frame, text="Ouvrir l'interface web", 
                             command=self.open_web_interface, width=25)
        web_button.pack(pady=(10, 5))
        
        logs_button = tk.Button(main_frame, text="Voir les logs", 
                              command=self.view_logs, width=25)
        logs_button.pack(pady=5)
        
        # Zone de texte pour les logs
        log_frame = tk.Frame(main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        tk.Label(log_frame, text="Logs récents:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Scrollbar pour les logs
        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=8, yscrollcommand=scrollbar.set,
                              font=("Courier", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)
        
        # Menu
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self.show_about)
        help_menu.add_command(label="Quitter", command=self.quit_application)
        
        # Gestion de la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Minimiser dans la barre des tâches
        minimize_button = tk.Button(main_frame, text="Minimiser dans la barre des tâches", 
                                  command=self.minimize_to_taskbar, width=30)
        minimize_button.pack(pady=(10, 0))
        
        # Démarrer la surveillance des logs
        threading.Thread(target=self.update_logs, daemon=True).start()
        
    def log_message(self, message):
        """Ajoute un message aux logs"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Ajouter au widget de texte
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limiter le nombre de lignes (garder les 100 dernières)
        lines = self.log_text.get("1.0", tk.END).split("\n")
        if len(lines) > 100:
            self.log_text.delete("1.0", f"{len(lines)-100}.0")
        
        # Logger aussi dans le fichier
        logging.info(message)
        
    def start_server(self):
        """Démarre le serveur NMEA"""
        if self.server_running:
            self.log_message("Le serveur est déjà en cours d'exécution")
            return
            
        try:
            self.log_message(f"Démarrage du serveur: {' '.join(self.server_command)}")
            
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
            self.update_ui_state()
            self.log_message(f"Serveur démarré avec PID: {self.server_process.pid}")
            
            # Démarrer un thread pour surveiller le serveur
            threading.Thread(target=self.monitor_server, daemon=True).start()
                
        except Exception as e:
            self.log_message(f"Erreur lors du démarrage du serveur: {e}")
            messagebox.showerror("Erreur", f"Impossible de démarrer le serveur:\n{e}")
            
    def stop_server(self):
        """Arrête le serveur NMEA"""
        if not self.server_running:
            self.log_message("Le serveur n'est pas en cours d'exécution")
            return
            
        try:
            self.log_message("Arrêt du serveur...")
            
            if self.server_process:
                # Essayer d'arrêter proprement le processus
                if sys.platform == "win32":
                    self.server_process.terminate()
                else:
                    self.server_process.terminate()
                
                # Attendre un peu pour un arrêt propre
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.log_message("Arrêt forcé du serveur")
                    self.server_process.kill()
                    self.server_process.wait()
                
                self.server_process = None
                
            self.server_running = False
            self.update_ui_state()
            self.log_message("Serveur arrêté")
                
        except Exception as e:
            self.log_message(f"Erreur lors de l'arrêt du serveur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'arrêt du serveur:\n{e}")
            
    def monitor_server(self):
        """Surveille le serveur pour détecter s'il s'arrête inopinément"""
        while self.server_running and self.server_process:
            try:
                if self.server_process.poll() is not None:
                    self.log_message("Le serveur s'est arrêté inopinément")
                    self.server_running = False
                    self.root.after(0, self.update_ui_state)
                    break
                    
                time.sleep(2)
            except Exception as e:
                self.log_message(f"Erreur dans la surveillance du serveur: {e}")
                break
                
    def update_ui_state(self):
        """Met à jour l'état de l'interface utilisateur"""
        if self.server_running:
            self.status_label.config(text="Statut: En cours d'exécution", fg="green")
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Statut: Arrêté", fg="red")
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
    def open_web_interface(self):
        """Ouvre l'interface web du serveur"""
        if not self.server_running:
            messagebox.showwarning("Serveur arrêté", "Le serveur doit être démarré pour ouvrir l'interface web")
            return
            
        try:
            webbrowser.open('http://localhost:8080')
            self.log_message("Interface web ouverte")
        except Exception as e:
            self.log_message(f"Erreur lors de l'ouverture de l'interface web: {e}")
            messagebox.showerror("Erreur", f"Impossible d'ouvrir l'interface web:\n{e}")
            
    def view_logs(self):
        """Ouvre le dossier des logs"""
        try:
            if sys.platform == "win32":
                os.startfile(os.path.abspath('logs'))
            elif sys.platform == "darwin":
                subprocess.Popen(['open', os.path.abspath('logs')])
            else:
                subprocess.Popen(['xdg-open', os.path.abspath('logs')])
        except Exception as e:
            self.log_message(f"Erreur lors de l'ouverture du dossier logs: {e}")
            
    def show_about(self):
        """Affiche les informations sur l'application"""
        messagebox.showinfo(
            "À propos",
            "NMEA Tracker Server Manager\n\n"
            "Gestionnaire du serveur NMEA avec interface graphique.\n"
            "Permet de démarrer/arrêter le serveur et d'accéder à l'interface web.\n\n"
            "Version: 1.0"
        )
        
    def minimize_to_taskbar(self):
        """Minimise la fenêtre dans la barre des tâches"""
        self.root.iconify()
        
    def on_closing(self):
        """Gère la fermeture de la fenêtre"""
        if self.server_running:
            if messagebox.askyesno("Confirmation", 
                                 "Le serveur est en cours d'exécution. Voulez-vous l'arrêter et quitter?"):
                self.stop_server()
                self.root.after(1000, self.root.destroy)
            else:
                # Juste minimiser au lieu de fermer
                self.minimize_to_taskbar()
        else:
            self.root.destroy()
            
    def quit_application(self):
        """Quitte l'application"""
        if self.server_running:
            if messagebox.askyesno("Confirmation", 
                                 "Le serveur est en cours d'exécution. Voulez-vous l'arrêter et quitter?"):
                self.stop_server()
                self.root.after(1000, self.root.destroy)
            else:
                return
        else:
            self.root.destroy()
            
    def update_logs(self):
        """Met à jour les logs périodiquement"""
        while True:
            try:
                time.sleep(5)  # Attendre 5 secondes
            except:
                break
        
    def run(self):
        """Lance l'application"""
        self.log_message("Démarrage de l'application NMEA Server Manager")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.quit_application()

def main():
    """Point d'entrée principal"""
    try:
        app = NMEAServerTraySimple()
        app.run()
    except Exception as e:
        logging.error(f"Erreur fatale: {e}")
        messagebox.showerror("Erreur fatale", f"Une erreur fatale s'est produite:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
