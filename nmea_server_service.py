#!/usr/bin/env python3
"""
NMEA Tracker Server - Windows Service
Permet d'installer le serveur NMEA comme un service Windows
"""

import sys
import os
import time
import threading
import servicemanager
import socket

try:
    import win32event
    import win32service
    import win32serviceutil
    import win32api
    import win32con
    SERVICE_AVAILABLE = True
except ImportError:
    SERVICE_AVAILABLE = False
    print("[WARNING] Modules win32 non disponibles - service non supporté")

# Import du serveur NMEA principal avec fallback pour gevent
try:
    from nmea_server import (
        main_thread, cleanup_on_exit, shutdown_event, 
        HTTPS_PORT, signal_handler
    )
    NMEA_SERVER_AVAILABLE = True
except ImportError as e:
    if "gevent" in str(e):
        print("[FALLBACK] gevent non disponible - utilisation du serveur HTTP alternatif")
        try:
            from nmea_server_fallback import (
                main_thread, cleanup_on_exit, shutdown_event, 
                HTTPS_PORT, signal_handler
            )
            NMEA_SERVER_AVAILABLE = True
        except ImportError:
            print("[ERROR] Aucun serveur NMEA disponible")
            NMEA_SERVER_AVAILABLE = False
    else:
        print(f"[ERROR] Erreur import nmea_server: {e}")
        NMEA_SERVER_AVAILABLE = False

class NMEAServerService(win32serviceutil.ServiceFramework):
    """Service Windows pour le serveur NMEA"""
    
    _svc_name_ = "NMEATrackerServer"
    _svc_display_name_ = "NMEA Tracker Server"
    _svc_description_ = "Serveur NMEA pour le suivi GPS/AIS - Interface web sur port " + str(HTTPS_PORT)
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.server_thread = None
        socket.setdefaulttimeout(60)
        
    def SvcStop(self):
        """Arrêter le service"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPING,
            (self._svc_name_, '')
        )
        
        # Déclencher l'arrêt du serveur NMEA
        shutdown_event.set()
        
        # Attendre que le thread se termine
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=10)
        
        # Nettoyage
        cleanup_on_exit()
        
        # Signaler l'arrêt au gestionnaire de services
        win32event.SetEvent(self.hWaitStop)
        
    def SvcDoRun(self):
        """Démarrer le service"""
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            # Démarrer le serveur NMEA dans un thread séparé
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            # Attendre le signal d'arrêt
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Erreur du service NMEA: {e}")
            
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )
    
    def run_server(self):
        """Exécuter le serveur NMEA"""
        try:
            servicemanager.LogInfoMsg(f"Démarrage du serveur NMEA sur le port {HTTPS_PORT}")
            main_thread()
        except Exception as e:
            servicemanager.LogErrorMsg(f"Erreur du serveur NMEA: {e}")

def install_service():
    """Installer le service Windows"""
    if not SERVICE_AVAILABLE:
        print("[ERROR] Modules win32 requis non disponibles")
        print("Installez avec : pip install pywin32")
        return False
        
    try:
        win32serviceutil.InstallService(
            NMEAServerService,
            NMEAServerService._svc_name_,
            NMEAServerService._svc_display_name_,
            description=NMEAServerService._svc_description_
        )
        print(f"✅ Service '{NMEAServerService._svc_display_name_}' installé avec succès")
        print(f"   Interface web : https://localhost:{HTTPS_PORT}/config.html")
        print("\nCommandes disponibles :")
        print(f"  Démarrer : net start {NMEAServerService._svc_name_}")
        print(f"  Arrêter  : net stop {NMEAServerService._svc_name_}")
        print(f"  Statut   : sc query {NMEAServerService._svc_name_}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'installation du service : {e}")
        return False

def remove_service():
    """Désinstaller le service Windows"""
    try:
        win32serviceutil.RemoveService(NMEAServerService._svc_name_)
        print(f"✅ Service '{NMEAServerService._svc_display_name_}' désinstallé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la désinstallation du service : {e}")
        return False

def start_service():
    """Démarrer le service Windows"""
    try:
        win32serviceutil.StartService(NMEAServerService._svc_name_)
        print(f"✅ Service '{NMEAServerService._svc_display_name_}' démarré")
        print(f"   Interface web : https://localhost:{HTTPS_PORT}/config.html")
        return True
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du service : {e}")
        return False

def stop_service():
    """Arrêter le service Windows"""
    try:
        win32serviceutil.StopService(NMEAServerService._svc_name_)
        print(f"✅ Service '{NMEAServerService._svc_display_name_}' arrêté")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'arrêt du service : {e}")
        return False

def main():
    """Point d'entrée principal"""
    if len(sys.argv) == 1:
        # Démarrage normal du service (appelé par Windows)
        if SERVICE_AVAILABLE:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(NMEAServerService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            print("[ERROR] Service non supporté - modules win32 manquants")
            sys.exit(1)
    else:
        # Gestion des arguments de ligne de commande
        command = sys.argv[1].lower()
        
        if command == 'install':
            if install_service():
                print("\n🔧 Pour démarrer automatiquement au boot :")
                print(f"   sc config {NMEAServerService._svc_name_} start= auto")
        
        elif command == 'remove' or command == 'uninstall':
            remove_service()
        
        elif command == 'start':
            start_service()
        
        elif command == 'stop':
            stop_service()
        
        elif command == 'restart':
            print("Redémarrage du service...")
            stop_service()
            time.sleep(2)
            start_service()
        
        elif command == 'debug':
            # Mode debug - exécuter directement sans service
            print("[DEBUG] Mode debug - exécution directe")
            main_thread()
        
        else:
            print("Usage:")
            print(f"  {sys.argv[0]} install    - Installer le service")
            print(f"  {sys.argv[0]} remove     - Désinstaller le service")
            print(f"  {sys.argv[0]} start      - Démarrer le service")
            print(f"  {sys.argv[0]} stop       - Arrêter le service")
            print(f"  {sys.argv[0]} restart    - Redémarrer le service")
            print(f"  {sys.argv[0]} debug      - Mode debug (sans service)")

if __name__ == "__main__":
    main()
