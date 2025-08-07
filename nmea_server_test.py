#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# NMEA Server for Windy Plugin


# To avoid thread issues with Flask-SocketIO
from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer
import os, sys
import platform
import re
import socket
import serial
import serial.tools.list_ports
import threading
import logging
import signal
import atexit
import subprocess
import time  # Required import
import datetime
import ipaddress
import warnings
from flask import Flask, Response, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
# import ssl

# Operating system detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Conditional stderr redirection (safer on Windows)
if not IS_WINDOWS:
    sys.stderr = open(os.devnull, 'w')  # Only on Linux
else:
    print("[INFO] Windows mode detected - stderr not redirected")

# Load environment variables from .env file
load_dotenv()

# === GLOBAL VARIABLES ===
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
UDP_IP = os.getenv("UDP_IP", "0.0.0.0")
UDP_PORT = int(os.getenv("UDP_PORT", "5005"))
TCP_IP = os.getenv("TCP_IP", "0.0.0.0")
TCP_PORT = int(os.getenv("TCP_PORT", "5006"))
HTTPS_PORT = int(os.getenv("HTTPS_PORT", "5000"))

# Nouvelles variables pour modes client/serveur
UDP_MODE = os.getenv("UDP_MODE", "server")  # "server" ou "client"
TCP_MODE = os.getenv("TCP_MODE", "server")  # "server" ou "client"
UDP_TARGET_IP = os.getenv("UDP_TARGET_IP", "")
UDP_TARGET_PORT = int(os.getenv("UDP_TARGET_PORT", "50110"))
TCP_TARGET_IP = os.getenv("TCP_TARGET_IP", "")
TCP_TARGET_PORT = int(os.getenv("TCP_TARGET_PORT", "50110"))
REJECTED_PATTERN = re.compile(r'^\$([A-Z][A-Z])(GS[A-Z]|XDR|AMAID|AMCLK|AMSA|SGR|MMB|MDA)')

# Ajouter ces variables globales après les imports et avant les autres variables
# (vers la ligne 50-60, après les imports mais avant les variables globales)

# Variables globales pour les données NMEA en temps réel
last_nmea_data = []  # Buffer des dernières données NMEA
max_nmea_buffer = 50  # Garder les 50 dernières lignes

# === NMEA DATA EMISSION FUNCTION ===
# Émettre les données NMEA via WebSocket et les stocker dans le buffer

def emit_nmea_data(source, message):
    """Émet les données NMEA via WebSocket et les stocke"""
    global last_nmea_data
    
    try:
        # Vérifications des paramètres d'entrée
        if source is None or source == "":
            source = "UNKNOWN"
        if message is None or message == "":
            debug_logger.debug("Message NMEA vide - ignoré")
            return
            
        # Nettoyer le message
        message = str(message).strip()
        if not message or message == "undefined":
            debug_logger.debug(f"Message invalide ignoré: '{message}'")
            return
        
        # Ajouter timestamp
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}][{source}] {message}"
        
        # Ajouter au buffer
        last_nmea_data.append(formatted_message)
        if len(last_nmea_data) > max_nmea_buffer:
            last_nmea_data.pop(0)
        
        # 🆕 LOG NMEA dans fichier au lieu de console
        nmea_logger.info(f"{source}: {message}")
        
        # 🆕 DEBUG seulement si activé ET en mode verbose
        if DEBUG:
            debug_logger.debug(f"EMIT {source}: {message[:50]}...")
            
        # Émettre pour Windy Plugin (chaîne NMEA pure)
        try:
            socketio.emit('nmea_data', message)
        except Exception as windy_error:
            error_logger.error(f"Erreur émission Windy: {windy_error}")
        
        # Émettre pour l'interface web avec informations source
        try:
            web_data = {
                'source': source,
                'message': message,
                'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
            }
            socketio.emit('nmea_data_web', web_data)
        except Exception as ws_error:
            error_logger.error(f"Erreur émission WebSocket: {ws_error}")
                
    except Exception as e:
        error_logger.error(f"Erreur lors de l'émission NMEA: {e}")


# === PYINSTALLER RESOURCE PATH HELPER ===
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === ENVIRONMENT CONFIG LOADING ADAPTED TO SYSTEM ===
# Default serial port according to OS
DEFAULT_SERIAL_PORT = "COM5" if IS_WINDOWS else "AUTO"
SERIAL_PORT = os.getenv("SERIAL_PORT", DEFAULT_SERIAL_PORT).strip()
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 4800))
ENABLE_SERIAL = os.getenv("ENABLE_SERIAL", "True").lower() == "true"
ENABLE_UDP = os.getenv("ENABLE_UDP", "True").lower() == "true"
ENABLE_TCP = os.getenv("ENABLE_TCP", "True").lower() == "true"

print(f"[INFO] System detected: {platform.system()}")
print(f"[INFO] Default serial port: {SERIAL_PORT}")

# === LOG CONFIGURATION AVANCÉE ===
# 🆕 SUPPRESSION COMPLÈTE des logs HTTP/SSL/gevent sur TOUS les systèmes
import logging
import warnings
import datetime
import ipaddress
from logging.handlers import RotatingFileHandler

# Supprimer TOUS les logs HTTP (werkzeug/Flask)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL + 1)
logging.getLogger('werkzeug.serving').setLevel(logging.CRITICAL + 1)
logging.getLogger('flask').setLevel(logging.ERROR)

# Supprimer TOUS les logs SSL et gevent
logging.getLogger('gevent').setLevel(logging.CRITICAL + 1)  # Plus que CRITICAL
logging.getLogger('gevent.ssl').setLevel(logging.CRITICAL + 1)
logging.getLogger('gevent.baseserver').setLevel(logging.CRITICAL + 1)
logging.getLogger('gevent.server').setLevel(logging.CRITICAL + 1)
logging.getLogger('gevent.pywsgi').setLevel(logging.CRITICAL + 1)
logging.getLogger('ssl').setLevel(logging.CRITICAL + 1)

# Supprimer les warnings Python SSL
warnings.filterwarnings('ignore', category=Warning)
warnings.filterwarnings('ignore', message='.*SSL.*')
warnings.filterwarnings('ignore', message='.*certificate.*')

# 🆕 SUPPRESSION COMPLÈTE DES LOGS HTTP/WERKZEUG
# Désactiver complètement Werkzeug et tous les logs HTTP
logging.getLogger('werkzeug').disabled = True
logging.getLogger('werkzeug.serving').disabled = True

# Redirection complète de stdout pour les logs HTTP gevent
import sys
class HTTPLogFilter:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout if original_stdout is not None else sys.__stdout__
        
    def write(self, text):
        # Protection contre stdout None
        if self.original_stdout is None:
            return
            
        # Filtrer les logs HTTP (contiennent des patterns typiques)
        http_patterns = [
            'GET /', 'POST /', 'PUT /', 'DELETE /',
            'HTTP/1.1', 'socket.io', '127.0.0.1', 'localhost'
        ]
        
        # Si le texte contient un pattern HTTP, l'ignorer
        if any(pattern in text for pattern in http_patterns):
            return
        
        # Sinon, écrire vers stdout original
        try:
            self.original_stdout.write(text)
        except (AttributeError, OSError):
            pass  # Ignorer si stdout n'est pas disponible
        
    def flush(self):
        if self.original_stdout is not None:
            try:
                self.original_stdout.flush()
            except (AttributeError, OSError):
                pass
        
    def fileno(self):
        if self.original_stdout is not None:
            try:
                return self.original_stdout.fileno()
            except (AttributeError, OSError):
                return -1
        return -1

# Appliquer le filtre HTTP uniquement sur Windows où c'est problématique
# Et seulement si stdout est disponible
if IS_WINDOWS and sys.stdout is not None:
    sys.stdout = HTTPLogFilter(sys.stdout)
    # Le message sera affiché plus tard après la définition de main_logger

# Supprimer urllib3 warnings si disponible
try:
    import urllib3
    urllib3.disable_warnings()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
    urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)
except ImportError:
    pass

# 🆕 SYSTÈME DE LOGS STRUCTURÉ PAR FICHIERS
os.makedirs("logs", exist_ok=True)

# Formatter commun pour tous les logs - SANS caractères spéciaux
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

# 🆕 LOGGER POUR TRAMES NMEA (remplace les print EMIT-DEBUG)
nmea_logger = logging.getLogger("nmea_data")
nmea_logger.setLevel(logging.INFO)
nmea_handler = RotatingFileHandler("logs/nmea_data.log", maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
nmea_handler.setFormatter(file_formatter)
nmea_logger.addHandler(nmea_handler)

# 🆕 LOGGER POUR DEBUG GÉNÉRAL (remplace les print DEBUG)
debug_logger = logging.getLogger("debug")
debug_logger.setLevel(logging.DEBUG)
debug_handler = RotatingFileHandler("logs/debug.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
debug_handler.setFormatter(file_formatter)
debug_logger.addHandler(debug_handler)

# 🆕 LOGGER POUR CONNEXIONS TCP/UDP (détails techniques)
network_logger = logging.getLogger("network")
network_logger.setLevel(logging.INFO)
network_handler = RotatingFileHandler("logs/network.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
network_handler.setFormatter(file_formatter)
network_logger.addHandler(network_handler)

# 🆕 LOGGER POUR ERREURS SYSTÈME
error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
error_handler = RotatingFileHandler("logs/errors.log", maxBytes=1024*1024, backupCount=5, encoding='utf-8')
error_handler.setFormatter(file_formatter)
error_logger.addHandler(error_handler)

# 🆕 Logger principal pour les messages importants (console + fichier)
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)

# Handler fichier pour main avec UTF-8
main_file_handler = RotatingFileHandler("logs/main.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
main_file_handler.setFormatter(file_formatter)
main_logger.addHandler(main_file_handler)

# Handler console pour main (messages importants seulement)
main_console_handler = logging.StreamHandler()
main_console_handler.setFormatter(console_formatter)
main_logger.addHandler(main_console_handler)

# 🆕 Afficher les messages d'initialisation des filtres
if IS_WINDOWS:
    main_logger.info("Filtre HTTP activé pour Windows")

# 🆕 Redirection stderr pour SSL (conservée)
class SSLErrorFilter:
    """Filtre pour supprimer les erreurs SSL spécifiques"""
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr if original_stderr is not None else sys.__stderr__
        
    def write(self, text):
        # Protection contre stderr None
        if self.original_stderr is None:
            return
            
        # 🆕 Liste étendue des patterns SSL à filtrer
        ssl_patterns = [
            'ssl:', 'sslv3_alert', 'certificate_unknown', 
            'gevent', 'greenlet', 'wrap_socket_and_handle',
            'handshake', '_ssl.c:', 'ssl.sslerror',
            'certificate_verify_failed', 'ssl handshake failed',
            'wsgiserver', 'baseserver', 'pywsgi'
        ]
        
        # Filtrer les erreurs SSL connues
        if any(keyword in text.lower() for keyword in ssl_patterns):
            return  # Ignorer complètement
        
        # Écrire tout le reste vers stderr original
        try:
            self.original_stderr.write(text)
        except (AttributeError, OSError):
            pass  # Ignorer si stderr n'est pas disponible
        
    def flush(self):
        if self.original_stderr is not None:
            try:
                self.original_stderr.flush()
            except (AttributeError, OSError):
                pass
        
    def fileno(self):
        if self.original_stderr is not None:
            try:
                return self.original_stderr.fileno()
            except (AttributeError, OSError):
                return -1
        return -1

# Appliquer le filtre SSL seulement sur Windows où c'est problématique
# Et seulement si stderr est disponible
if IS_WINDOWS and sys.stderr is not None:
    sys.stderr = SSLErrorFilter(sys.stderr)

main_logger.info("Système de logs initialisé")

# === FLASK SERVER ===
app = Flask(__name__)

# Configuration SocketIO adaptative selon l'environnement
def setup_socketio():
    try:
        # Essayer gevent en premier (performance optimale)
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
        main_logger.info("SocketIO configuré avec gevent (performance optimale)")
        return socketio
    except (ValueError, ImportError) as e:
        main_logger.warning(f"Gevent non disponible ({e}), utilisation du mode threading")
        try:
            # Fallback vers threading (compatible PyInstaller)
            socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
            main_logger.info("SocketIO configuré avec threading (compatible PyInstaller)")
            return socketio
        except Exception as e2:
            main_logger.warning(f"Threading échoué ({e2}), mode par défaut")
            # Dernier recours
            socketio = SocketIO(app, cors_allowed_origins="*")
            main_logger.info("SocketIO configuré en mode par défaut")
            return socketio

socketio = setup_socketio()
CORS(app)  # Allow all origins (wildcard origin *)

# === BLUETOOTH GPS MANAGER (initialisé tôt pour éviter les erreurs de référence) ===
# Déclaration en global - sera initialisé après la classe BluetoothGPSManager
bluetooth_manager = None

# === SHUTDOWN MANAGEMENT ===
shutdown_event = threading.Event()
http_server = None

def signal_handler(signum, frame):
    """Handle shutdown signals (Ctrl+C, SIGTERM, etc.)"""
    print(f"\n[INFO] Signal {signum} received - shutting down gracefully...")
    shutdown_event.set()
    
    # Stop HTTP server
    global http_server
    if http_server:
        print("[INFO] Stopping HTTP server...")
        http_server.stop()
    
    # Stop all threads
    serial_stop.set()
    udp_stop.set()
    tcp_stop.set()
    bluetooth_monitor_stop.set()
    
    print("[INFO] Shutdown complete.")
    sys.exit(0)

def cleanup_on_exit():
    """Cleanup function called on normal exit"""
    if not shutdown_event.is_set():
        shutdown_event.set()
        serial_stop.set()
        udp_stop.set()
        tcp_stop.set()
        bluetooth_monitor_stop.set()
        print("[INFO] Cleanup completed.")

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination
if not IS_WINDOWS:
    signal.signal(signal.SIGHUP, signal_handler)   # Hang up (Unix only)

# Register cleanup function
atexit.register(cleanup_on_exit)

# === SIMPLE BLUETOOTH SERIAL PORT DETECTION ===
def detect_bluetooth_serial_port():
    """
    Détection automatique et connexion GPS Bluetooth.
    Utilise le gestionnaire Bluetooth pour découverte et connexion automatiques.
    Compatible avec Windows, macOS, Linux.
    Returns the port name (e.g. /dev/rfcomm0 or COM4), or None.
    """
    global bluetooth_manager
    # Sur Linux, utiliser le gestionnaire Bluetooth automatique
    if IS_LINUX:
        print("[AUTO-DETECT] Utilisation du gestionnaire Bluetooth automatique...")
        auto_port = bluetooth_manager.maintain_connection()
        if auto_port:
            return auto_port
    
    # Fallback: méthode traditionnelle par énumération des ports
    print("[AUTO-DETECT] Recherche traditionnelle des ports série...")
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("[AUTO-DETECT] Aucun port série détecté")
        return None
    
    print(f"[AUTO-DETECT] {len(ports)} port(s) série trouvé(s):")
    for port in ports:
        print(f"  - {port.device}: {port.description}")
    
    # Patterns adaptés selon l'OS
    if IS_WINDOWS:
        # Recherche plus large sur Windows
        bt_patterns = [
            re.compile(r"bluetooth", re.IGNORECASE),
            re.compile(r"bt", re.IGNORECASE),
            re.compile(r"serial", re.IGNORECASE),
            re.compile(r"com\d+", re.IGNORECASE),
            re.compile(r"usb", re.IGNORECASE)
        ]
    else:
        bt_patterns = [
            re.compile(r"bluetooth", re.IGNORECASE),
            re.compile(r"rfcomm", re.IGNORECASE),
            re.compile(r"tty", re.IGNORECASE)
        ]

    for port in ports:
        port_name = port.device
        desc = port.description or ""
        hwid = port.hwid or ""

        for pattern in bt_patterns:
            if pattern.search(port_name) or pattern.search(desc) or pattern.search(hwid):
                print(f"[AUTO-DETECT] Port série détecté: {port_name} ({desc})")
                return port_name
    
    # Si rien trouvé, retourner le premier port disponible sur Windows
    if IS_WINDOWS and ports:
        first_port = ports[0].device
        print(f"[AUTO-DETECT] Aucun port Bluetooth, utilisation du premier port: {first_port}")
        return first_port
    
    print("[AUTO-DETECT] Aucun port série Bluetooth détecté.")
    return None

def list_serial_ports():
    """Returns the list of available serial ports (name and description)."""
    ports = list(serial.tools.list_ports.comports())
    return [(p.device, p.description) for p in ports]
    
        
# === FLAGS AND THREADS FOR DYNAMIC MANAGEMENT ===
serial_thread = None
udp_thread = None
tcp_thread = None
bluetooth_monitor_thread = None
serial_stop = threading.Event()
udp_stop = threading.Event()
tcp_stop = threading.Event()
bluetooth_monitor_stop = threading.Event()

# === NMEA DATA CLEANING FUNCTION ===
# This function cleans NMEA data by removing common repeater prefixes and unwanted characters.
# It is designed to handle various NMEA formats and ensure clean data for processing.
# It removes common repeater prefixes, cleans up double dollar signs, and strips control characters.
# It is used to ensure that only valid NMEA sentences are processed and emitted.
def clean_nmea_data(data):
    """Nettoie les données NMEA des préfixes de répéteur"""
    import re
    
    # Supprimer les préfixes courants des répéteurs
    data = re.sub(r'^\$[A-Z0-9]{2,6}\$', '$', data)
    
    # Nettoyer les doubles $
    data = re.sub(r'\$+', '$', data)
    
    # Supprimer les caractères de contrôle
    data = re.sub(r'[\r\n\x00-\x1F]', '', data)
    
    return data.strip()


# Function to listen to UDP broadcasts in server mode
# This function listens for UDP broadcasts on a specified port and emits the received NMEA data.
def udp_listener(stop_event):
    # 🆕 Forcer l'IP de binding
    bind_ip = "0.0.0.0"  # Forcer pour Windows
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((bind_ip, UDP_PORT))  # Utiliser bind_ip au lieu de UDP_IP
        print(f"[UDP] Listening on {bind_ip}:{UDP_PORT}")
        sock.settimeout(1.0)
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                message = clean_nmea_data(data.decode('utf-8', errors='ignore'))
                if not REJECTED_PATTERN.match(message):
                    nmea_logger.info(f"[UDP] {message}")
                    if message and message.strip():
                        emit_nmea_data("UDP", message.strip())
            except socket.timeout:
                continue
            except Exception as e:
                if not shutdown_event.is_set():
                    print(f"[UDP] Error: {e}")
                break
                
    except Exception as e:
        print(f"[UDP] Bind error on {bind_ip}:{UDP_PORT} - {e}")
        return
    finally:
        try:
            sock.close()
        except:
            pass
            
    print("[UDP] Stopped.")

# Function to listen to UDP broadcasts in client mode
# This function listens for UDP broadcasts on a specified port and emits the received NMEA data.
# It is designed to handle incoming messages, filter out unwanted patterns, and emit valid NMEA data.
# It uses a stop event to allow graceful shutdown of the listener thread.

def udp_client_listener(target_ip, target_port, stop_event):
    """Écoute UDP en mode client/broadcast"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Configuration pour recevoir les broadcasts
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Bind sur toutes les interfaces pour recevoir les broadcasts
    sock.bind(('0.0.0.0', target_port))
    
    print(f"[UDP-CLIENT] Écoute broadcasts sur port {target_port}")
    sock.settimeout(1.0)
    
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8', errors='ignore').strip()
            
            if not REJECTED_PATTERN.match(message):
                nmea_logger.info(f"[UDP-CLIENT] {message}")
                if message and message.strip():
                    emit_nmea_data("UDP", message.strip())
                    
        except socket.timeout:
            continue
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[UDP-CLIENT] Error: {e}")
            break
            
    sock.close()
    print("[UDP-CLIENT] Stopped.")

def tcp_listener(stop_event):
    """Écoute TCP en mode serveur avec logs structurés"""
    global TCP_PORT
    
    bind_ip = "0.0.0.0"
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((bind_ip, TCP_PORT))
        sock.listen(1)
        main_logger.info(f"TCP Listening on {bind_ip}:{TCP_PORT}")
        network_logger.info(f"TCP server started on {bind_ip}:{TCP_PORT}")
        sock.settimeout(1.0)
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                conn, addr = sock.accept()
                main_logger.info(f"TCP Connection from {addr}")
                network_logger.info(f"TCP connection established from {addr}")
                
                with conn:
                    conn.settimeout(1.0)
                    buffer = ""
                    
                    while not stop_event.is_set() and not shutdown_event.is_set():
                        try:
                            data = conn.recv(1024)
                            if not data:
                                network_logger.info(f"TCP connection closed by {addr}")
                                break
                            
                            # LOG réseau détaillé dans fichier
                            raw_data = data.decode('utf-8', errors='ignore')
                            network_logger.debug(f"TCP received {len(data)} bytes from {addr}")
                            
                            buffer += raw_data
                            
                            # Traiter toutes les lignes complètes dans le buffer
                            line_count = 0
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line_count += 1
                                
                                message = clean_nmea_data(line)
                                
                                if message:
                                    pattern_match = REJECTED_PATTERN.match(message)
                                    
                                    if not pattern_match:
                                        # LOG uniquement les trames acceptées
                                        debug_logger.debug(f"TCP message accepted: {message[:50]}...")
                                        emit_nmea_data("TCP", message.strip())
                                    else:
                                        debug_logger.debug(f"TCP message rejected by pattern: {message[:30]}...")
                            
                            # Protection contre buffer trop grand
                            if len(buffer) > 4096:
                                network_logger.warning("TCP buffer overflow, clearing")
                                buffer = ""
                                
                        except socket.timeout:
                            continue
                        except Exception as e:
                            if not shutdown_event.is_set():
                                error_logger.error(f"TCP connection error with {addr}: {e}")
                            break
                            
            except socket.timeout:
                continue
            except Exception as e:
                if not shutdown_event.is_set():
                    error_logger.error(f"TCP accept error: {e}")
                break
                
    except Exception as e:
        error_logger.error(f"TCP bind error on {bind_ip}:{TCP_PORT} - {e}")
        if "10049" in str(e):
            main_logger.error("TCP Windows Error 10049: Invalid address - using 0.0.0.0")
        elif "10048" in str(e):
            main_logger.error("TCP Port already in use - try another port")
        return
    finally:
        try:
            sock.close()
        except:
            pass
            
    main_logger.info("TCP Stopped")
    network_logger.info("TCP server stopped")

def tcp_client(stop_event):
    """Connexion TCP en mode client"""
    global TCP_TARGET_IP, TCP_TARGET_PORT
    
    main_logger.info(f"TCP Client connecting to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
    network_logger.info(f"TCP client mode - target: {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
    
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            # Tentative de connexion
            main_logger.info(f"Attempting TCP connection to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
            sock.connect((TCP_TARGET_IP, TCP_TARGET_PORT))
            main_logger.info(f"TCP Client connected to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
            network_logger.info(f"TCP client connection established")
            
            # Boucle de réception des données
            buffer = ""
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    data = sock.recv(1024).decode('utf-8', errors='ignore')
                    if not data:
                        main_logger.warning("TCP connection closed by server")
                        break
                    
                    buffer += data
                    lines = buffer.split('\n')
                    buffer = lines[-1]  # Garder la dernière ligne incomplète
                    
                    for line in lines[:-1]:
                        message = line.strip()
                        if message and (message.startswith('$') or message.startswith('!')):
                            debug_logger.debug(f"TCP Client received: {message}")
                            emit_nmea_data("TCP", message)
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    error_logger.error(f"TCP client receive error: {e}")
                    break
                    
        except socket.timeout:
            error_logger.error(f"TCP connection timeout to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
        except ConnectionRefusedError:
            error_logger.error(f"TCP connection refused to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
        except Exception as e:
            error_logger.error(f"TCP client error: {e}")
        
        finally:
            try:
                sock.close()
            except:
                pass
        
        # Attendre avant de reconnecter
        main_logger.info("TCP client will retry in 10 seconds...")
        for _ in range(100):  # 10 secondes en boucles de 0.1s
            if stop_event.is_set():
                break
            time.sleep(0.1)

def tcp_client_listener(target_ip, target_port, stop_event):
    """Connexion TCP en mode client vers un GPS"""
    print(f"[TCP-CLIENT] Tentative connexion à {target_ip}:{target_port}")
    
    retry_interval = 10  # Reconnexion toutes les 10 secondes
    
    while not stop_event.is_set() and not shutdown_event.is_set():
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # Timeout connexion
            
            # Connexion au GPS
            sock.connect((target_ip, target_port))
            print(f"[TCP-CLIENT] Connecté à {target_ip}:{target_port}")
            
            sock.settimeout(1.0)  # Timeout lecture
            buffer = ""
            
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    data = sock.recv(1024)
                    if not data:
                        print("[TCP-CLIENT] Connexion fermée par le serveur")
                        break
                        
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Traiter les lignes complètes
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        message = line.strip()
                        
                        if message and not REJECTED_PATTERN.match(message):
                            nmea_logger.info(f"[TCP-CLIENT] {message}")
                            if message and message.strip():
                                emit_nmea_data("TCP", message.strip())
                                
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[TCP-CLIENT] Erreur lecture: {e}")
                    break
                    
        except socket.timeout:
            print(f"[TCP-CLIENT] Timeout connexion à {target_ip}:{target_port}")
        except ConnectionRefusedError:
            if DEBUG:
                print(f"[TCP-CLIENT] Connexion refusée par {target_ip}:{target_port}")
        except Exception as e:
            print(f"[TCP-CLIENT] Erreur connexion: {e}")
        finally:
            if sock:
                sock.close()
        
        # Attendre avant de retry
        print(f"[TCP-CLIENT] Reconnexion dans {retry_interval} secondes...")
        for _ in range(retry_interval * 10):
            if stop_event.is_set():
                break
            time.sleep(0.1)
    
    print("[TCP-CLIENT] Stopped.")


# Function to listen to the serial port and send NMEA data
# Uses a buffer to handle pending data and avoid frame loss
def serial_listener(port, baudrate, stop_event):
    print(f"[SERIAL] Listener starting on {port} @ {baudrate} bps")
    
    # Check that the port exists
    if not port or port == "None":
        print("[SERIAL] No serial port configured")
        return
    
    try:
        # Basic configuration for serial connection
        serial_kwargs = {
            'port': port,
            'baudrate': baudrate,
            'timeout': 0.1
        }
        
        # Additional parameters for Windows (more robust)
        if IS_WINDOWS:
            serial_kwargs.update({
                'bytesize': serial.EIGHTBITS,
                'parity': serial.PARITY_NONE,
                'stopbits': serial.STOPBITS_ONE,
                'xonxoff': False,
                'rtscts': False,
                'dsrdtr': False,
                'write_timeout': 2,
                'inter_byte_timeout': 0.1
            })
        
        print(f"[SERIAL] Attempting to open port {port}...")
        with serial.Serial(**serial_kwargs) as ser:
            print(f"[SERIAL] Port opened successfully: {port} @ {baudrate} bps")
            
            # Small delay to stabilize the connection
            time.sleep(0.5)
            
            # Clear buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            buffer = ""
            consecutive_errors = 0
            
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    # Check if there's pending data
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        if data:
                            consecutive_errors = 0  # Reset error counter
                            buffer += data
                            
                            # Process complete lines
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = clean_nmea_data(line)
                                
                                if line and not REJECTED_PATTERN.match(line):
                                    nmea_logger.info(f"[SERIAL] {line}")
                                    if line and line.strip():
                                        emit_nmea_data("SERIAL", line.strip())
                    else:
                        # Small pause if no data
                        time.sleep(0.01)
                        
                except UnicodeDecodeError:
                    consecutive_errors += 1
                    if consecutive_errors > 10:
                        print("[SERIAL] Too many decoding errors, pausing...")
                        time.sleep(1)
                        consecutive_errors = 0
                    continue
                except Exception as e:
                    consecutive_errors += 1
                    if DEBUG:
                        print(f"[SERIAL] Read error: {e}")
                    if consecutive_errors > 20:
                        print("[SERIAL] Too many errors, stopping listener")
                        break
                    time.sleep(0.1)
                    continue
                    
    except serial.SerialException as e:
        print(f"[ERROR][SERIAL] Cannot open port {port}: {e}")
        if IS_WINDOWS:
            print("[INFO] Possible solutions:")
            print("  1. Check that the COM port exists in Device Manager")
            print("  2. Close any other program using this port")
            print("  3. Reconnect your Bluetooth device")
            print("  4. Try another serial port")
        else:
            print("[INFO] Check serial port access permissions")
            print("  sudo chmod 666 /dev/ttyUSB0  # or appropriate port")
    except Exception as e:
        print(f"[ERROR][SERIAL] Unexpected error: {e}")
    
    print("[SERIAL] Stopped.")

def bluetooth_monitor(stop_event):
    """
    Thread de surveillance Bluetooth qui maintient la connexion GPS automatiquement
    """
    global bluetooth_manager, serial_thread
    print("[BLUETOOTH-MONITOR] Démarrage de la surveillance Bluetooth...")
    
    # S'assurer que bluetooth_manager est initialisé
    if bluetooth_manager is None:
        print("[BLUETOOTH-MONITOR] Erreur: bluetooth_manager non initialisé")
        return
    
    check_counter = 0
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            if ENABLE_SERIAL and IS_LINUX:
                check_counter += 1
                
                # Log périodique pour montrer que le monitoring est actif
                if check_counter % 10 == 1:  # Tous les 10 cycles (10 minutes)
                    print(f"[BLUETOOTH-MONITOR] Cycle {check_counter} - vérification connexion...")
                
                # Vérifier et maintenir la connexion Bluetooth
                port = bluetooth_manager.maintain_connection()
                if port:
                    # Mettre à jour le port série global si nécessaire
                    global SERIAL_PORT
                    current_port = SERIAL_PORT if SERIAL_PORT != "AUTO" else None
                    
                    # En mode AUTO, toujours vérifier si le thread série tourne
                    if SERIAL_PORT == "AUTO" or current_port != port:
                        print(f"[BLUETOOTH-MONITOR] Connexion GPS détectée: {port}")
                        
                        # Arrêter le thread série existant s'il y en a un
                        if serial_thread and serial_thread.is_alive():
                            print("[BLUETOOTH-MONITOR] Arrêt du thread série existant...")
                            serial_stop.set()
                            serial_thread.join(timeout=2)
                        
                        # Attendre un peu pour s'assurer que le port est libéré
                        print("[BLUETOOTH-MONITOR] Attente libération du port...")
                        time.sleep(5)
                        
                        # Démarrer le nouveau thread série
                        print(f"[BLUETOOTH-MONITOR] Démarrage thread série sur {port}...")
                        serial_stop.clear()
                        serial_thread = threading.Thread(target=serial_listener, args=(port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                        serial_thread.start()
                        
                        # Mettre à jour la variable globale pour l'interface web (seulement si pas en mode AUTO)
                        if SERIAL_PORT != "AUTO":
                            SERIAL_PORT = port
                    elif not (serial_thread and serial_thread.is_alive()):
                        # Le port n'a pas changé mais le thread série n'est pas actif
                        print(f"[BLUETOOTH-MONITOR] Redémarrage thread série sur {port}...")
                        serial_stop.clear()
                        serial_thread = threading.Thread(target=serial_listener, args=(port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                        serial_thread.start()
                elif SERIAL_PORT == "AUTO":
                    # En mode AUTO, arrêter le thread série s'il n'y a plus de connexion
                    if serial_thread and serial_thread.is_alive():
                        print("[BLUETOOTH-MONITOR] Aucune connexion GPS - arrêt du thread série")
                        serial_stop.set()
                        serial_thread.join(timeout=2)
            
            # Attendre 60 secondes avant la prochaine vérification
            for _ in range(600):  # 60 secondes en incréments de 0.1s
                if stop_event.is_set():
                    break
                time.sleep(0.1)
                
        except Exception as e:
            print(f"[BLUETOOTH-MONITOR] Erreur: {e}")
            time.sleep(10)  # Pause plus longue en cas d'erreur
    
    # Nettoyer la connexion rfcomm en sortie
    if IS_LINUX:
        bluetooth_manager.cleanup_rfcomm()
    
    print("[BLUETOOTH-MONITOR] Arrêt de la surveillance Bluetooth.")

# === THREAD MANAGEMENT FUNCTION ===
# Remplacer la fonction manage_threads() par cette version avec debug :

def manage_threads():
    global serial_thread, udp_thread, tcp_thread, bluetooth_monitor_thread
    
    main_logger.info(f"Starting threads - UDP:{ENABLE_UDP}, TCP:{ENABLE_TCP}, Serial:{ENABLE_SERIAL}")
    debug_logger.info(f"Thread management - UDP:{ENABLE_UDP}, TCP:{ENABLE_TCP}, Serial:{ENABLE_SERIAL}")
    
    # UDP
    if ENABLE_UDP:
        if udp_thread is None or not udp_thread.is_alive():
            udp_stop.clear()
            
            # Choisir la fonction selon le mode UDP
            if UDP_MODE == "server":
                debug_logger.info(f"Starting UDP server thread on port {UDP_PORT}")
                udp_thread = threading.Thread(target=udp_listener, args=(udp_stop,), daemon=True)
            else:  # mode client
                debug_logger.info(f"Starting UDP client thread to {UDP_TARGET_IP}:{UDP_TARGET_PORT}")
                udp_thread = threading.Thread(target=udp_client_listener, args=(UDP_TARGET_IP, UDP_TARGET_PORT, udp_stop), daemon=True)
            
            udp_thread.start()
            time.sleep(0.5)
            if udp_thread.is_alive():
                main_logger.info("UDP thread started successfully")
                debug_logger.info("UDP thread started successfully")
            else:
                main_logger.error("UDP thread failed to start")
                error_logger.error("UDP thread failed to start")
        else:
            debug_logger.info("UDP thread already active")
    else:
        if udp_thread and udp_thread.is_alive():
            debug_logger.info("Stopping UDP thread")
            udp_stop.set()
            udp_thread = None
            
    # TCP
    if ENABLE_TCP:
        if tcp_thread is None or not tcp_thread.is_alive():
            tcp_stop.clear()
            
            # Choisir la fonction selon le mode TCP
            if TCP_MODE == "server":
                debug_logger.info(f"Starting TCP server thread on port {TCP_PORT}")
                tcp_thread = threading.Thread(target=tcp_listener, args=(tcp_stop,), daemon=True)
            else:  # mode client
                debug_logger.info(f"Starting TCP client thread to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
                tcp_thread = threading.Thread(target=tcp_client, args=(tcp_stop,), daemon=True)
            
            tcp_thread.start()
            time.sleep(0.5)
            if tcp_thread.is_alive():
                main_logger.info("TCP thread started successfully")
                debug_logger.info("TCP thread started successfully")
            else:
                main_logger.error("TCP thread failed to start")
                error_logger.error("TCP thread failed to start")
        else:
            debug_logger.info("TCP thread already active")
    else:
        if tcp_thread and tcp_thread.is_alive():
            debug_logger.info("Stopping TCP thread")
            tcp_stop.set()
            tcp_thread = None

    # SERIAL - seulement si ce n'est pas AUTO ou si AUTO est résolu
    if ENABLE_SERIAL:
        actual_port = SERIAL_PORT
        
        if SERIAL_PORT == "AUTO":
            debug_logger.info(f"[AUTO-DETECT] Mode AUTO - attente de la découverte Bluetooth...")
        else:
            if serial_thread is None or not serial_thread.is_alive():
                debug_logger.info(f"[THREAD-MANAGER] Démarrage thread série sur {actual_port}")
                serial_stop.clear()
                serial_thread = threading.Thread(target=serial_listener, args=(actual_port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                serial_thread.start()
                time.sleep(0.5)
                if serial_thread.is_alive():
                    main_logger.info("SERIAL thread started successfully")
                    debug_logger.info("SERIAL thread started successfully")
                else:
                    main_logger.error("SERIAL thread failed to start")
                    debug_logger.error("SERIAL thread failed to start")
            else:
                debug_logger.info("SERIAL thread already active")
    else:
        if serial_thread and serial_thread.is_alive():
            debug_logger.info("Stopping SERIAL thread")
            serial_stop.set()
            serial_thread = None
    
    # Status final
    debug_logger.info(f"Final Status :")
    debug_logger.info(f"Final status - UDP: {'Active' if udp_thread and udp_thread.is_alive() else 'Inactive'}")
    debug_logger.info(f"Final status - TCP: {'Active' if tcp_thread and tcp_thread.is_alive() else 'Inactive'}")
    debug_logger.info(f"Final status - Serial: {'Active' if serial_thread and serial_thread.is_alive() else 'Inactive'}")

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS on Windows if needed"""
    try:
        # Try to create self-signed certificates if they don't exist
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        
        cert_path = get_resource_path('cert.pem')
        key_path = get_resource_path('key.pem')
        
        print("[SSL] Génération de certificats SSL auto-signés...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "FR"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "France"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "NMEA Server"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Write certificate and key
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print("[SSL] Certificats SSL créés avec succès")
        return True
        
    except ImportError:
        print("[SSL] Module cryptography non disponible - pas de génération de certificat")
        return False
    except Exception as e:
        print(f"[SSL] Erreur lors de la création du certificat: {e}")
        return False

def run_flask_app():
    global http_server
    main_logger.info(f"Starting Flask server on port {HTTPS_PORT}")
    
    # Paths for certificates - compatible with PyInstaller
    cert_path = get_resource_path('cert.pem')
    key_path = get_resource_path('key.pem')
    
    debug_logger.debug(f"Looking for certificates:")
    debug_logger.debug(f"  cert.pem: {cert_path}")
    debug_logger.debug(f"  key.pem: {key_path}")
    
    # Create certificates if they don't exist on Windows
    if IS_WINDOWS and not (os.path.exists(cert_path) and os.path.exists(key_path)):
        main_logger.info("Certificats SSL manquants sur Windows - tentative de création...")
        create_self_signed_cert()
    
    # Check certificate existence
    if os.path.exists(cert_path) and os.path.exists(key_path):
        main_logger.info("SSL certificates found - starting HTTPS")
        try:
            # 🆕 Créer un logger silencieux pour WSGIServer
            import sys
            
            # Rediriger stdout temporairement pour supprimer les logs HTTP
            class NullWriter:
                def write(self, text): pass
                def flush(self): pass
            
            # 🆕 Configuration WSGIServer SANS logs
            http_server = WSGIServer(
                ('0.0.0.0', HTTPS_PORT), 
                app, 
                keyfile=key_path, 
                certfile=cert_path,
                log=NullWriter(),  # Supprimer les logs d'accès
                error_log=NullWriter()  # Supprimer les logs d'erreur
            )
            
            # 🚫 Ne PAS utiliser http_server.set_spawn() qui cause le TypeError

            main_logger.info(f"HTTPS server active on https://localhost:{HTTPS_PORT}")
            main_logger.info(f"Web interface: https://localhost:{HTTPS_PORT}/config.html")
            main_logger.info("Press Ctrl+C to stop the server")
            
            if IS_WINDOWS:
                main_logger.info(f"Alternative HTTP disponible sur http://localhost:{HTTPS_PORT}")
            
            # 🆕 Serveur HTTPS avec gestion SSL simplifiée
            try:
                http_server.serve_forever()
            except KeyboardInterrupt:
                main_logger.info("Keyboard interrupt received")
                raise
            except Exception as e:
                # Filtrer SEULEMENT les erreurs SSL répétitives - laisser passer les vraies erreurs
                error_msg = str(e).lower()
                if any(ssl_keyword in error_msg for ssl_keyword in [
                    'sslv3_alert_certificate_unknown',
                    'certificate_unknown', 
                    'ssl handshake',
                    'wrap_socket_and_handle'
                ]):
                    # Ignorer silencieusement ces erreurs SSL cosmétiques
                    pass
                else:
                    # Pour toutes les autres erreurs, les signaler
                    error_logger.error(f"HTTPS server error: {e}")
                    raise
                
        except KeyboardInterrupt:
            main_logger.info("Keyboard interrupt received")
        except Exception as e:
            if not shutdown_event.is_set() and "ssl" not in str(e).lower():
                error_logger.error(f"HTTPS impossible: {e}")
                main_logger.info("Basculement vers HTTP...")
                run_http_fallback()
    else:
        main_logger.info("SSL certificates missing - starting HTTP")
        run_http_fallback()

def run_http_fallback():
    """Start server in simple HTTP mode"""
    try:
        main_logger.info(f"HTTP fallback server on http://localhost:{HTTPS_PORT}")
        main_logger.info(f"Web interface: http://localhost:{HTTPS_PORT}/config.html")
        if IS_WINDOWS:
            main_logger.info("Mode HTTP - pas d'erreurs SSL sur Windows")
        main_logger.info("Press Ctrl+C to stop the server")
        
        # 🆕 Configuration pour supprimer TOUS les logs HTTP
        import logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=HTTPS_PORT, 
            debug=False,
            allow_unsafe_werkzeug=True,
            log_output=False  # Supprimer les logs HTTP
        )
    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt received")
    except Exception as e:
        if not shutdown_event.is_set():
            error_logger.error(f"Cannot start server: {e}")

# Custom error handler for SSL errors on Windows
def handle_ssl_error(func):
    """Decorator to handle SSL errors gracefully on Windows"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if "ssl" in str(e).lower() or "certificate" in str(e).lower():
                # Silently ignore SSL errors on Windows
                if IS_WINDOWS:
                    return None
                print(f"[SSL-WARNING] {e}")
            else:
                raise e
    return wrapper

# Fonction de test à ajouter temporairement
def test_ports_separately():
    """Test UDP et TCP séparément pour identifier les conflits"""
    import socket
    
    print("[TEST] Test des ports individuellement...")
    
    # Test UDP
    try:
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_sock.bind(('0.0.0.0', UDP_PORT))
        print(f"[TEST] ✅ UDP port {UDP_PORT} disponible")
        udp_sock.close()
    except Exception as e:
        print(f"[TEST] ❌ UDP port {UDP_PORT} problème: {e}")
    
    # Test TCP
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_sock.bind(('0.0.0.0', TCP_PORT))
        tcp_sock.listen(1)
        print(f"[TEST] ✅ TCP port {TCP_PORT} disponible")
        tcp_sock.close()
    except Exception as e:
        print(f"[TEST] ❌ TCP port {TCP_PORT} problème: {e}")

# Appeler cette fonction dans main_thread() avant manage_threads()


def main_thread():
    global SERIAL_PORT, ENABLE_SERIAL, serial_thread
    print(f"[INFO] Configuration loaded from .env:")
    print(f"  - DEBUG: {DEBUG}")
    print(f"  - Serial: {ENABLE_SERIAL} (Port: {SERIAL_PORT})")
    print(f"  - UDP: {ENABLE_UDP} (Mode: {UDP_MODE}, Port: {UDP_PORT})")
    if UDP_MODE == "client":
        print(f"    → Target: {UDP_TARGET_IP}:{UDP_TARGET_PORT}")
    print(f"  - TCP: {ENABLE_TCP} (Mode: {TCP_MODE}, Port: {TCP_PORT})")
    if TCP_MODE == "client":
        print(f"    → Target: {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
    print()
    print("🛑 Pour arrêter le serveur : Ctrl+C (ou Ctrl+Break sur Windows)")
    print()
    
    # Auto-detection of serial port if necessary
    if ENABLE_SERIAL and (not SERIAL_PORT or SERIAL_PORT == "AUTO"):
        detected_port = detect_bluetooth_serial_port()
        if detected_port:
            SERIAL_PORT = detected_port
            print(f"[INFO] Serial port auto-detected: {SERIAL_PORT}")
            
            # Démarrer immédiatement le thread série si un port est détecté
            if serial_thread is None or not serial_thread.is_alive():
                print(f"[INFO] Starting serial thread on detected port: {SERIAL_PORT}")
                serial_stop.clear()
                serial_thread = threading.Thread(target=serial_listener, args=(SERIAL_PORT, SERIAL_BAUDRATE, serial_stop), daemon=True)
                serial_thread.start()
        else:
            print("[INFO] No serial port detected - serial function disabled")
            ENABLE_SERIAL = False
    
    # Test ports separately if enabled
    test_ports_separately()

    # Start threads for UDP, TCP and Serial if enabled
    manage_threads()
    
    # Small pause to let threads start
    time.sleep(0.5)

    try:
        # Launch Flask server
        print(f"[INFO] Launching Flask server on port {HTTPS_PORT}")
        run_flask_app()
    except KeyboardInterrupt:
        print("\n[INFO] Shutdown initiated by user")
    except Exception as e:
        print(f"[ERROR] Server error: {e}")
    finally:
        print("[INFO] Server stopped.")


# === EXISTING FUNCTIONS ===
@app.route('/config.html', methods=['GET'])
def home():
    serial_ports = list_serial_ports()
    return render_template(
        'config.html',
        enable_serial=ENABLE_SERIAL,
        enable_udp=ENABLE_UDP,
        enable_tcp=ENABLE_TCP,
        enable_debug=DEBUG,
        udp_ip=UDP_IP,
        udp_port=UDP_PORT,
        tcp_ip=TCP_IP,
        tcp_port=TCP_PORT,
        udp_mode=UDP_MODE,
        tcp_mode=TCP_MODE,
        udp_target_ip=UDP_TARGET_IP,
        udp_target_port=UDP_TARGET_PORT,
        tcp_target_ip=TCP_TARGET_IP,
        tcp_target_port=TCP_TARGET_PORT,
        serial_ports=serial_ports,
        serial_port=SERIAL_PORT,
        serial_baudrate=SERIAL_BAUDRATE
    )

@app.route('/select_connection', methods=['POST'])
def select_connection():
    global ENABLE_SERIAL, ENABLE_UDP, ENABLE_TCP, DEBUG
    global UDP_IP, UDP_PORT, TCP_IP, TCP_PORT, SERIAL_PORT, SERIAL_BAUDRATE

    ENABLE_SERIAL = 'enable_serial' in request.form
    ENABLE_UDP = 'enable_udp' in request.form
    ENABLE_TCP = 'enable_tcp' in request.form
    DEBUG = 'enable_debug' in request.form

    UDP_IP = request.form.get('udp_ip', UDP_IP)
    try:
        UDP_PORT = int(request.form.get('udp_port', UDP_PORT))
    except ValueError:
        pass
    TCP_IP = request.form.get('tcp_ip', TCP_IP)
    try:
        TCP_PORT = int(request.form.get('tcp_port', TCP_PORT))
    except ValueError:
        pass

    # New: selected serial port
    SERIAL_PORT = request.form.get('serial_port', SERIAL_PORT)
    try:
        SERIAL_BAUDRATE = int(request.form.get('serial_baudrate', SERIAL_BAUDRATE))
    except (ValueError, TypeError):
        pass
    # Restart threads with new configuration
    manage_threads()
    return redirect(url_for('home'))

@app.route('/', methods=['GET'])
def config():
    return render_template('./index.html') #, allowed_types=", ".join(ALLOWED_SENTENCE_TYPES))

# === BLUETOOTH GPS AUTO-MANAGEMENT ===
class BluetoothGPSManager:
    """
    Gestionnaire automatique pour GPS Bluetooth avec auto-découverte et connexion
    """
    def __init__(self):
        self.target_mac = None  # Adresse MAC du GPS trouvé
        self.target_channel = None  # Canal SPP trouvé
        self.rfcomm_device = 0  # Numéro du device rfcomm (0 = /dev/rfcomm0)
        self.is_connected = False
        self.last_scan_time = 0
        self.scan_interval = 60  # Scan toutes les minutes
        self.connection_timeout = 10  # Timeout de connexion
        
    def run_command(self, cmd, timeout=10):
        """Exécute une commande shell avec timeout"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print(f"[BLUETOOTH] Commande timeout: {cmd}")
            return False, "", "Timeout"
        except Exception as e:
            print(f"[BLUETOOTH] Erreur commande: {e}")
            return False, "", str(e)
    
    def scan_bluetooth_devices(self):
        """Scan des appareils Bluetooth à proximité"""
        print("[BLUETOOTH] Scan des appareils Bluetooth...")
        
        # Vérifier que Bluetooth est disponible
        success, stdout, stderr = self.run_command("which hciconfig", 5)
        if not success:
            print("[BLUETOOTH] hciconfig non trouvé - Bluetooth non supporté")
            return []
        
        # Vérifier et activer Bluetooth
        success, stdout, stderr = self.run_command("hciconfig", 5)
        if not success:
            print("[BLUETOOTH] Bluetooth non disponible")
            return []
        
        # Essayer d'activer l'interface Bluetooth
        success, stdout, stderr = self.run_command("sudo hciconfig hci0 up", 5)
        if not success:
            print(f"[BLUETOOTH] Impossible d'activer Bluetooth: {stderr}")
            # Essayer sans sudo
            success, stdout, stderr = self.run_command("hciconfig hci0 up", 5)
            if not success:
                print("[BLUETOOTH] Bluetooth non accessible - vérifiez les permissions")
                return []
        
        # Scan des appareils avec timeout plus long
        print("[BLUETOOTH] Scan en cours... (peut prendre 10-15 secondes)")
        success, stdout, stderr = self.run_command("hcitool scan", 20)
        if not success:
            print(f"[BLUETOOTH] Échec du scan: {stderr}")
            return []
        
        devices = []
        for line in stdout.split('\n'):
            line = line.strip()
            if ':' in line and len(line.split()) >= 2:
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    mac = parts[0].strip()
                    name = parts[1].strip()
                    devices.append((mac, name))
                    print(f"[BLUETOOTH] Trouvé: {mac} - {name}")
        
        print(f"[BLUETOOTH] {len(devices)} appareil(s) détecté(s)")
        return devices
    
    def find_spp_channel(self, mac_address):
        """Trouve le canal SPP pour un appareil donné"""
        print(f"[BLUETOOTH] Recherche canal SPP pour {mac_address}...")
        
        success, stdout, stderr = self.run_command(f"sdptool browse {mac_address}", 10)
        if not success:
            print(f"[BLUETOOTH] Échec browse: {stderr}")
            return None
        
        # Chercher le canal SPP dans la sortie
        lines = stdout.split('\n')
        in_spp_service = False
        
        for i, line in enumerate(lines):
            if 'Serial Port' in line or 'SPP' in line:
                in_spp_service = True
                print(f"[BLUETOOTH] Service Serial Port trouvé")
            elif in_spp_service and 'Channel:' in line:
                try:
                    channel = int(line.split('Channel:')[1].strip())
                    print(f"[BLUETOOTH] Canal SPP trouvé: {channel}")
                    return channel
                except (ValueError, IndexError):
                    continue
            elif in_spp_service and line.strip() == "":
                in_spp_service = False
        
        print("[BLUETOOTH] Aucun canal SPP trouvé")
        return None
    
    def setup_rfcomm(self, mac_address, channel):
        """Configure la connexion rfcomm"""
        print(f"[BLUETOOTH] Configuration rfcomm{self.rfcomm_device} -> {mac_address}:{channel}")
        
        # Libérer d'abord le device rfcomm s'il existe
        self.cleanup_rfcomm()
        
        # Créer la nouvelle connexion
        cmd = f"sudo rfcomm bind {self.rfcomm_device} {mac_address} {channel}"
        success, stdout, stderr = self.run_command(cmd, 10)
        
        if success:
            # Attendre que le device soit créé et stabilisé
            rfcomm_path = f"/dev/rfcomm{self.rfcomm_device}"
            for i in range(10):  # Attendre jusqu'à 5 secondes
                if os.path.exists(rfcomm_path):
                    # Attendre encore un peu pour la stabilisation
                    time.sleep(2)
                    print(f"[BLUETOOTH] rfcomm configuré: {rfcomm_path}")
                    return rfcomm_path
                time.sleep(0.5)
            
            print(f"[BLUETOOTH] Device {rfcomm_path} non créé après timeout")
            return None
        else:
            print(f"[BLUETOOTH] Échec configuration rfcomm: {stderr}")
            return None
    
    def cleanup_rfcomm(self):
        """Nettoie la connexion rfcomm"""
        cmd = f"sudo rfcomm release {self.rfcomm_device}"
        success, stdout, stderr = self.run_command(cmd, 5)
        if success:
            print(f"[BLUETOOTH] rfcomm{self.rfcomm_device} libéré")
        
    def test_gps_connection(self, port_path):
        """Test si le port GPS fonctionne en lisant quelques trames"""
        print(f"[BLUETOOTH] Test connexion GPS sur {port_path}")
        
        # Attendre un peu que le device soit prêt
        time.sleep(2)
        
        ser = None
        try:
            # Test rapide avec gestion explicite de la fermeture
            ser = serial.Serial(port_path, 4800, timeout=5)
            print("[BLUETOOTH] Port ouvert, lecture des données...")
            
            # Test plus court - juste 10 secondes max
            for i in range(10):  # Max 10 tentatives = 50 secondes
                try:
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        print(f"[BLUETOOTH] Données reçues: {line[:80]}...")
                        # Vérifier si c'est une trame NMEA GPS valide
                        if (line.startswith('$GP') or line.startswith('$GN') or 
                            line.startswith('!AI') or line.startswith('$GL')):
                            print(f"[BLUETOOTH] ✓ Trame NMEA GPS valide détectée")
                            # Fermer proprement le port et attendre
                            ser.close()
                            time.sleep(3)  # Attendre 3 secondes pour que le port soit libéré
                            return True
                        elif line.startswith('$'):
                            print(f"[BLUETOOTH] Trame NMEA détectée (autre): {line[:50]}")
                            # Continuer à chercher des trames GPS spécifiques
                except Exception as e:
                    print(f"[BLUETOOTH] Erreur lecture: {e}")
                    continue
            
            print("[BLUETOOTH] Aucune trame NMEA GPS valide reçue")
            return False
            
        except Exception as e:
            print(f"[BLUETOOTH] Erreur test connexion: {e}")
            return False
        finally:
            # S'assurer que le port est fermé dans tous les cas
            if ser and ser.is_open:
                try:
                    ser.close()
                    time.sleep(3)  # Attendre que le port soit vraiment libéré
                except:
                    pass
    
    def auto_discover_and_connect(self):
        """Découverte automatique et connexion au GPS Bluetooth"""
        if not IS_LINUX:
            print("[BLUETOOTH] Auto-découverte disponible uniquement sur Linux")
            return None
            
        print("[BLUETOOTH] === DÉCOUVERTE AUTOMATIQUE GPS ===")
        
        # Scan des appareils
        devices = self.scan_bluetooth_devices()
        if not devices:
            print("[BLUETOOTH] Aucun appareil trouvé")
            return None
        
        # Tester chaque appareil pour GPS/SPP
        for mac, name in devices:
            print(f"[BLUETOOTH] Test appareil: {name} ({mac})")
            
            # Chercher le canal SPP
            channel = self.find_spp_channel(mac)
            if channel is None:
                continue
                
            # Essayer de configurer rfcomm
            rfcomm_path = self.setup_rfcomm(mac, channel)
            if rfcomm_path is None:
                continue
                
            # Tester la connexion GPS
            if self.test_gps_connection(rfcomm_path):
                print(f"[BLUETOOTH] ✅ GPS trouvé: {name} ({mac}) sur canal {channel}")
                self.target_mac = mac
                self.target_channel = channel
                self.is_connected = True
                return rfcomm_path
            else:
                print(f"[BLUETOOTH] ❌ Pas de GPS: {name}")
                self.cleanup_rfcomm()
        
        print("[BLUETOOTH] Aucun GPS Bluetooth trouvé")
        return None
    
    def detect_existing_rfcomm(self):
        """Détecte si un rfcomm est déjà configuré et fonctionnel"""
        print("[BLUETOOTH] Vérification des connexions rfcomm existantes...")
        
        # Vérifier si /dev/rfcomm0 existe
        rfcomm_path = f"/dev/rfcomm{self.rfcomm_device}"
        if os.path.exists(rfcomm_path):
            print(f"[BLUETOOTH] Device {rfcomm_path} trouvé")
            
            # Tester si c'est un GPS fonctionnel
            if self.test_gps_connection(rfcomm_path):
                print(f"[BLUETOOTH] ✅ GPS fonctionnel détecté sur {rfcomm_path}")
                self.is_connected = True
                return rfcomm_path
            else:
                print(f"[BLUETOOTH] ❌ {rfcomm_path} ne répond pas comme un GPS")
        
        return None
    
    def check_connection_status(self):
        """Vérifie l'état de la connexion actuelle"""
        if not self.is_connected:
            return False
            
        rfcomm_path = f"/dev/rfcomm{self.rfcomm_device}"
        
        # Vérifier que le device existe
        if not os.path.exists(rfcomm_path):
            print("[BLUETOOTH] Device rfcomm disparu")
            self.is_connected = False
            return False
        
        # Test plus léger - juste vérifier que le fichier est accessible
        try:
            # Au lieu d'ouvrir le port série, juste vérifier l'accès au fichier
            import stat
            st = os.stat(rfcomm_path)
            if stat.S_ISCHR(st.st_mode):  # Vérifier que c'est un device caractère
                return True
        except Exception as e:
            print(f"[BLUETOOTH] Erreur vérification device: {e}")
            
        print("[BLUETOOTH] Connexion GPS perdue")
        self.is_connected = False
        return False
    
    def maintain_connection(self):
        """Maintient la connexion GPS (appelé périodiquement)"""
        current_time = time.time()
        
        # Si connecté, vérifier l'état moins fréquemment
        if self.is_connected:
            if self.check_connection_status():
                # Connexion OK, pas besoin de rescanner
                return f"/dev/rfcomm{self.rfcomm_device}"
            else:
                print("[BLUETOOTH] Reconnexion nécessaire")
                self.cleanup_rfcomm()
                self.is_connected = False
                # Attendre un peu avant de reconnecter
                time.sleep(5)
        
        # Vérifier d'abord s'il y a une connexion rfcomm existante
        existing_connection = self.detect_existing_rfcomm()
        if existing_connection:
            return existing_connection
        
        # Vérifier si c'est le moment de scanner (seulement si pas connecté)
        if current_time - self.last_scan_time < self.scan_interval:
            return None
            
        self.last_scan_time = current_time
        print("[BLUETOOTH] Tentative de reconnexion automatique...")
        
        # Tentative de (re)connexion
        return self.auto_discover_and_connect()
    

class ConfigWatcher:
    def __init__(self, config_file=".env", callback=None):
        self.config_file = config_file
        self.callback = callback
        self.last_modified = 0
        self.running = True
        
    def start_watching(self):
        """Start watching config file for changes"""
        def watch():
            while self.running:
                try:
                    if os.path.exists(self.config_file):
                        current_modified = os.path.getmtime(self.config_file)
                        if current_modified != self.last_modified:
                            self.last_modified = current_modified
                            if self.callback:
                                print(f"[CONFIG] Configuration file changed, reloading...")
                                self.callback()
                    time.sleep(1)  # Check every second
                except Exception as e:
                    print(f"[CONFIG] Error watching config: {e}")
                    time.sleep(5)
                    
        thread = threading.Thread(target=watch, daemon=True)
        thread.start()
        
    def stop(self):
        self.running = False

# Fonction globale pour recharger la configuration
def reload_configuration():
    """Reload configuration and restart connections"""
    global ENABLE_SERIAL, ENABLE_UDP, ENABLE_TCP, DEBUG
    global UDP_IP, UDP_PORT, TCP_IP, TCP_PORT, SERIAL_PORT, SERIAL_BAUDRATE
    global UDP_MODE, TCP_MODE, UDP_TARGET_IP, UDP_TARGET_PORT, TCP_TARGET_IP, TCP_TARGET_PORT
    
    try:
        print("[CONFIG] Reloading configuration...")
        
        # Stop existing threads
        serial_stop.set()
        udp_stop.set() 
        tcp_stop.set()
        
        # Wait for threads to stop
        time.sleep(2)
        
        # Reload environment variables
        load_dotenv(override=True)
        
        # Update global variables
        ENABLE_SERIAL = os.getenv("ENABLE_SERIAL", "True").lower() == "true"
        ENABLE_UDP = os.getenv("ENABLE_UDP", "True").lower() == "true"
        ENABLE_TCP = os.getenv("ENABLE_TCP", "True").lower() == "true"
        DEBUG = os.getenv("DEBUG", "False").lower() == "true"
        
        UDP_IP = os.getenv("UDP_IP", "0.0.0.0")
        UDP_PORT = int(os.getenv("UDP_PORT", 5005))
        TCP_IP = os.getenv("TCP_IP", "0.0.0.0")
        TCP_PORT = int(os.getenv("TCP_PORT", 5006))
        
        # Charger les nouvelles variables de mode
        UDP_MODE = os.getenv("UDP_MODE", "server")
        TCP_MODE = os.getenv("TCP_MODE", "server")
        UDP_TARGET_IP = os.getenv("UDP_TARGET_IP", "")
        UDP_TARGET_PORT = int(os.getenv("UDP_TARGET_PORT", 50110))
        TCP_TARGET_IP = os.getenv("TCP_TARGET_IP", "")
        TCP_TARGET_PORT = int(os.getenv("TCP_TARGET_PORT", 50110))
        
        SERIAL_PORT = os.getenv("SERIAL_PORT", DEFAULT_SERIAL_PORT).strip()
        SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 4800))
        
        print(f"[CONFIG] New configuration loaded:")
        print(f"  - Serial: {ENABLE_SERIAL} (Port: {SERIAL_PORT})")
        print(f"  - UDP: {ENABLE_UDP} (Port: {UDP_PORT})")
        print(f"  - TCP: {ENABLE_TCP} (Port: {TCP_PORT})")
        
        # Restart connections
        manage_threads()
        
        print("[CONFIG] Configuration reloaded successfully!")
        
    except Exception as e:
        print(f"[CONFIG] Error reloading config: {e}")


def get_current_status():
    """Retourne le statut actuel de toutes les connexions avec debug"""
    global udp_thread, tcp_thread, serial_thread, bluetooth_manager
    
    # 🆕 Vérification sécurisée des threads
    try:
        udp_active = (udp_thread is not None and 
                     hasattr(udp_thread, 'is_alive') and 
                     udp_thread.is_alive() and 
                     ENABLE_UDP)
    except Exception as e:
        if DEBUG:
            print(f"[STATUS-DEBUG] Erreur vérification UDP: {e}")
        udp_active = False
    
    try:
        tcp_active = (tcp_thread is not None and 
                     hasattr(tcp_thread, 'is_alive') and 
                     tcp_thread.is_alive() and 
                     ENABLE_TCP)
    except Exception as e:
        if DEBUG:
            print(f"[STATUS-DEBUG] Erreur vérification TCP: {e}")
        tcp_active = False
    
    try:
        # Vérifier le statut serial/bluetooth
        serial_connected = False
        if ENABLE_SERIAL:
            if serial_thread is not None and hasattr(serial_thread, 'is_alive') and serial_thread.is_alive():
                serial_connected = True
            elif IS_LINUX and bluetooth_manager is not None:
                try:
                    serial_connected = bluetooth_manager.check_connection_status()
                except Exception as bt_error:
                    if DEBUG:
                        print(f"[STATUS-DEBUG] Erreur Bluetooth: {bt_error}")
                    serial_connected = False
    except Exception as e:
        if DEBUG:
            print(f"[STATUS-DEBUG] Erreur vérification Serial: {e}")
        serial_connected = False
    
    # Debug détaillé
    if DEBUG:
        print(f"[STATUS-DEBUG] ENABLE_UDP: {ENABLE_UDP}, UDP thread exists: {udp_thread is not None}")
        print(f"[STATUS-DEBUG] ENABLE_TCP: {ENABLE_TCP}, TCP thread exists: {tcp_thread is not None}")
        print(f"[STATUS-DEBUG] ENABLE_SERIAL: {ENABLE_SERIAL}, Serial thread exists: {serial_thread is not None}")
        
        if udp_thread:
            print(f"[STATUS-DEBUG] UDP thread alive: {udp_thread.is_alive()}")
        if tcp_thread:
            print(f"[STATUS-DEBUG] TCP thread alive: {tcp_thread.is_alive()}")
        if serial_thread:
            print(f"[STATUS-DEBUG] Serial thread alive: {serial_thread.is_alive()}")
    
    # Compter les connexions actives
    connections_active = sum([udp_active, tcp_active, serial_connected])
    
    status = {
        'udp_active': udp_active,
        'tcp_active': tcp_active,
        'serial_connected': serial_connected,
        'connections_active': connections_active,
        'timestamp': time.strftime("%H:%M:%S"),
        'udp_port': UDP_PORT,
        'tcp_port': TCP_PORT,
        # 🆕 Ajout des informations de configuration
        'udp_enabled': ENABLE_UDP,
        'tcp_enabled': ENABLE_TCP,
        'serial_enabled': ENABLE_SERIAL
    }
    
    if DEBUG:
        print(f"[STATUS] Final status - UDP: {udp_active}, TCP: {tcp_active}, Serial: {serial_connected}")
    
    return status


@app.route('/api/config', methods=['POST'])
def api_update_config():
    """Update configuration with immediate reload"""
    global ENABLE_SERIAL, ENABLE_UDP, ENABLE_TCP, DEBUG
    global UDP_IP, UDP_PORT, TCP_IP, TCP_PORT, SERIAL_PORT, SERIAL_BAUDRATE
    global UDP_MODE, TCP_MODE, UDP_TARGET_IP, UDP_TARGET_PORT, TCP_TARGET_IP, TCP_TARGET_PORT
    
    try:
        # Update global variables immediately
        ENABLE_SERIAL = 'enable_serial' in request.form
        ENABLE_UDP = 'enable_udp' in request.form
        ENABLE_TCP = 'enable_tcp' in request.form
        DEBUG = 'enable_debug' in request.form

        # Gestion des modes UDP et TCP
        UDP_MODE = request.form.get('udp_mode', 'server')
        TCP_MODE = request.form.get('tcp_mode', 'server')
        
        # Configuration UDP
        if UDP_MODE == 'server':
            UDP_IP = "0.0.0.0"
            try:
                UDP_PORT = int(request.form.get('udp_port', UDP_PORT))
            except ValueError:
                pass
        else:  # mode client
            UDP_TARGET_IP = request.form.get('udp_target_ip', UDP_TARGET_IP)
            try:
                UDP_TARGET_PORT = int(request.form.get('udp_target_port', UDP_TARGET_PORT))
            except ValueError:
                pass
        
        # Configuration TCP
        if TCP_MODE == 'server':
            TCP_IP = "0.0.0.0"
            try:
                TCP_PORT = int(request.form.get('tcp_port', TCP_PORT))
            except ValueError:
                pass
        else:  # mode client
            TCP_TARGET_IP = request.form.get('tcp_target_ip', TCP_TARGET_IP)
            try:
                TCP_TARGET_PORT = int(request.form.get('tcp_target_port', TCP_TARGET_PORT))
            except ValueError:
                pass

        SERIAL_PORT = request.form.get('serial_port', SERIAL_PORT)
        try:
            SERIAL_BAUDRATE = int(request.form.get('serial_baudrate', SERIAL_BAUDRATE))
        except (ValueError, TypeError):
            pass
        
        # Save to .env file
        config_lines = [
            f'ENABLE_SERIAL={"true" if ENABLE_SERIAL else "false"}',
            f'ENABLE_UDP={"true" if ENABLE_UDP else "false"}',
            f'ENABLE_TCP={"true" if ENABLE_TCP else "false"}',
            f'DEBUG={"true" if DEBUG else "false"}',
            f'UDP_IP={UDP_IP}',
            f'UDP_PORT={UDP_PORT}',
            f'TCP_IP={TCP_IP}',
            f'TCP_PORT={TCP_PORT}',
            f'UDP_MODE={UDP_MODE}',
            f'TCP_MODE={TCP_MODE}',
            f'UDP_TARGET_IP={UDP_TARGET_IP}',
            f'UDP_TARGET_PORT={UDP_TARGET_PORT}',
            f'TCP_TARGET_IP={TCP_TARGET_IP}',
            f'TCP_TARGET_PORT={TCP_TARGET_PORT}',
            f'SERIAL_PORT={SERIAL_PORT}',
            f'SERIAL_BAUDRATE={SERIAL_BAUDRATE}'
        ]
        
        with open('.env', 'w') as f:
            f.write('\n'.join(config_lines))
        
        print(f"[API] Configuration updated:")
        if UDP_MODE == 'server':
            print(f"  - UDP Serveur: {ENABLE_UDP} ({UDP_IP}:{UDP_PORT})")
        else:
            print(f"  - UDP Client: {ENABLE_UDP} → {UDP_TARGET_IP}:{UDP_TARGET_PORT}")
        
        if TCP_MODE == 'server':
            print(f"  - TCP Serveur: {ENABLE_TCP} ({TCP_IP}:{TCP_PORT})")
        else:
            print(f"  - TCP Client: {ENABLE_TCP} → {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
        
        print(f"  - Serial: {ENABLE_SERIAL} ({SERIAL_PORT})")
        
        # Restart threads with new configuration
        manage_threads()
        
        return jsonify({
            'success': True, 
            'message': 'Configuration updated and applied successfully'
        })
        
    except Exception as e:
        print(f"[API] Error updating config: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

# Mettre à jour l'endpoint status pour utiliser les variables globales
@app.route('/api/status')
def api_status():
    """API endpoint pour obtenir le statut des connexions"""
    try:
        status = get_current_status()
        
        # 🆕 Log pour debug
        if DEBUG:
            print(f"[API-STATUS] Retour: {status}")
            
        return jsonify(status)
    except Exception as e:
        print(f"[API-STATUS] Erreur: {e}")
        return jsonify({
            'udp_active': False,
            'tcp_active': False,
            'serial_connected': False,
            'connections_active': 0,
            'udp_enabled': ENABLE_UDP,
            'tcp_enabled': ENABLE_TCP,
            'serial_enabled': ENABLE_SERIAL,
            'error': str(e)
        }), 500

@app.route('/api/nmea_history')
def api_nmea_history():
    """Récupérer l'historique des données NMEA"""
    return jsonify({
        'success': True,
        'data': last_nmea_data[-20:],  # Les 20 dernières
        'count': len(last_nmea_data)
    })

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Gérer les nouvelles connexions WebSocket"""
    print(f"[WEBSOCKET] Client connecté: {request.sid}")
    
    # Envoyer les dernières données NMEA au client qui se connecte
    # Format simple pour compatibilité avec le plugin Windy
    for formatted_data in last_nmea_data[-10:]:  # Les 10 dernières
        # Extraire la trame NMEA pure du message formaté
        if '] ' in formatted_data:
            # Format: [timestamp][source] message
            nmea_message = formatted_data.split('] ', 2)[-1] if '] ' in formatted_data else formatted_data
        else:
            nmea_message = formatted_data
        
        # Envoyer la trame NMEA pure pour le plugin Windy
        socketio.emit('nmea_data', nmea_message, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    """Gérer les déconnexions WebSocket"""
    print(f"[WEBSOCKET] Client déconnecté: {request.sid}")

@socketio.on('request_status')
def handle_request_status():
    """Gérer les demandes de statut via WebSocket"""
    try:
        status = get_current_status()
        emit('status_update', status)
        
        if DEBUG:
            print(f"[WEBSOCKET] Status envoyé: {status}")
            
    except Exception as e:
        if DEBUG:
            print(f"[WEBSOCKET] Erreur envoi status: {e}")
        emit('status_update', {
            'udp_active': False,
            'tcp_active': False,
            'serial_connected': False,
            'connections_active': 0,
            'error': str(e)
        })

# Initialiser le gestionnaire Bluetooth
if bluetooth_manager is None:
    bluetooth_manager = BluetoothGPSManager()

# Initialiser le watcher de configuration
config_watcher = ConfigWatcher(".env", reload_configuration)

# Corriger la partie main
if __name__ == "__main__":
    # Démarrer le watcher de configuration
    config_watcher.start_watching()
    
    try:
        print("[MAIN] Starting NMEA Server...")
        main_thread()  # Utiliser la fonction main_thread() existante
    except KeyboardInterrupt:
        print("[MAIN] Received interrupt signal")
    finally:
        print("[MAIN] Stopping config watcher...")
        config_watcher.stop()
        bluetooth_manager.cleanup_rfcomm()
