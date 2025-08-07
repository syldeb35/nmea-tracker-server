#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# NMEA Server for Windy Plugin - Enhanced Version with System Tray Support


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

# System tray imports (will be conditionally used)
SYSTEM_TRAY_AVAILABLE = False
try:
    import pystray
    from PIL import Image
    import tkinter as tk
    from tkinter import messagebox
    import tkinter.messagebox
    SYSTEM_TRAY_AVAILABLE = True
    print("[INFO] System tray support available")
except ImportError as e:
    print(f"[INFO] System tray not available: {e}")
    print("[INFO] Running in console mode")

# Operating system detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Check if we should run in system tray mode
RUN_AS_TRAY = "--tray" in sys.argv or (
    len(sys.argv) == 1 and 
    SYSTEM_TRAY_AVAILABLE and 
    IS_WINDOWS and 
    not os.environ.get('PYTEST_CURRENT_TEST')  # Don't use tray in tests
)

# Conditional stderr redirection (safer on Windows)
if not IS_WINDOWS or RUN_AS_TRAY:
    if not RUN_AS_TRAY:  # Only redirect if not in tray mode
        sys.stderr = open(os.devnull, 'w')  # Only on Linux or specific cases
else:
    print("[INFO] Windows console mode detected - stderr not redirected")

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

# Variables globales pour les données NMEA en temps réel
last_nmea_data = []  # Buffer des dernières données NMEA
max_nmea_buffer = 50  # Garder les 50 dernières lignes

# System tray global variables
tray_icon = None
tray_app_running = False
server_thread = None

# === NMEA DATA EMISSION FUNCTION ===
def emit_nmea_data(source, message):
    """Émet les données NMEA via WebSocket et les stocke"""
    global last_nmea_data
    
    try:
        timestamp = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
        formatted_message = f"[{timestamp}][{source}] {message}"
        
        # Ajouter au buffer avec limite
        last_nmea_data.append(formatted_message)
        if len(last_nmea_data) > max_nmea_buffer:
            last_nmea_data.pop(0)
        
        # Émettre via WebSocket si disponible
        try:
            socketio.emit('nmea_data', {
                'raw': message,
                'source': source,
                'message': message,
                'timestamp': timestamp,
                'formatted': formatted_message
            })
        except Exception as ws_error:
            # Si WebSocket échoue, continuer sans erreur
            if 'DEBUG' in globals() and DEBUG:
                print(f"[WEBSOCKET] Erreur émission: {ws_error}")
                
    except Exception as e:
        print(f"[EMIT] Erreur lors de l'émission NMEA: {e}")

# === SYSTEM TRAY FUNCTIONS ===
def create_tray_icon():
    """Create system tray icon"""
    try:
        # Create a simple icon
        image = Image.new('RGB', (32, 32), color='blue')
        return image
    except Exception as e:
        print(f"[TRAY] Error creating icon: {e}")
        return None

def show_about():
    """Show about dialog"""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide main window
        messagebox.showinfo(
            "About NMEA Tracker Server",
            "NMEA Tracker Server v2.0\n\n"
            "📡 NMEA data server and web interface\n"
            f"🌐 Web interface: https://localhost:{HTTPS_PORT}\n"
            f"⚙️ Configuration: https://localhost:{HTTPS_PORT}/config.html\n"
            f"🔒 WebSocket: wss://localhost:{HTTPS_PORT} (Windy compatible)\n\n"
            "Status: Server is running in system tray"
        )
        root.destroy()
    except Exception as e:
        print(f"[TRAY] Error showing about: {e}")

def show_config():
    """Open configuration page in browser"""
    try:
        import webbrowser
        webbrowser.open(f"https://localhost:{HTTPS_PORT}/config.html")
    except Exception as e:
        print(f"[TRAY] Error opening config: {e}")

def show_web_interface():
    """Open web interface in browser"""
    try:
        import webbrowser
        webbrowser.open(f"https://localhost:{HTTPS_PORT}/")
    except Exception as e:
        print(f"[TRAY] Error opening web interface: {e}")

def quit_tray_app(icon=None, item=None):
    """Quit the tray application"""
    global tray_app_running
    print("[TRAY] Shutting down...")
    tray_app_running = False
    
    # Stop the server
    shutdown_event.set()
    
    # Stop the tray icon
    if icon:
        icon.stop()
    
    # Exit the application
    os._exit(0)

def setup_tray():
    """Setup system tray"""
    global tray_icon
    
    if not SYSTEM_TRAY_AVAILABLE:
        print("[TRAY] System tray not available")
        return None
    
    try:
        icon_image = create_tray_icon()
        if not icon_image:
            return None
        
        menu = pystray.Menu(
            pystray.MenuItem("NMEA Tracker Server", show_about, default=True),
            pystray.MenuItem.SEPARATOR,
            pystray.MenuItem("🌐 Web Interface", show_web_interface),
            pystray.MenuItem("⚙️ Configuration", show_config),
            pystray.MenuItem.SEPARATOR,
            pystray.MenuItem("❌ Quit", quit_tray_app)
        )
        
        tray_icon = pystray.Icon(
            name="NMEA Tracker Server",
            icon=icon_image,
            title="NMEA Tracker Server",
            menu=menu
        )
        
        print("[TRAY] System tray setup complete")
        return tray_icon
        
    except Exception as e:
        print(f"[TRAY] Error setting up tray: {e}")
        return None

def run_tray():
    """Run the system tray"""
    global tray_app_running
    
    if not SYSTEM_TRAY_AVAILABLE:
        print("[TRAY] System tray not available, running in console mode")
        return False
    
    try:
        tray = setup_tray()
        if tray:
            tray_app_running = True
            print("[TRAY] Starting system tray...")
            tray.run()  # This blocks
            return True
        else:
            print("[TRAY] Failed to setup tray")
            return False
    except Exception as e:
        print(f"[TRAY] Error running tray: {e}")
        return False

# === PYINSTALLER RESOURCE PATH HELPER ===
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# === ENVIRONMENT CONFIG LOADING ADAPTED TO SYSTEM ===
# Default serial port according to OS
DEFAULT_SERIAL_PORT = "COM5" if IS_WINDOWS else "/dev/rfcomm0"
SERIAL_PORT = os.getenv("SERIAL_PORT", DEFAULT_SERIAL_PORT).strip()
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 4800))
ENABLE_SERIAL = os.getenv("ENABLE_SERIAL", "True").lower() == "true"
ENABLE_UDP = os.getenv("ENABLE_UDP", "True").lower() == "true"
ENABLE_TCP = os.getenv("ENABLE_TCP", "True").lower() == "true"

print(f"[INFO] System detected: {platform.system()}")
print(f"[INFO] Default serial port: {SERIAL_PORT}")
if RUN_AS_TRAY:
    print("[INFO] Running in system tray mode")
else:
    print("[INFO] Running in console mode")

# === LOG CONFIGURATION ===
# Disable HTTP logs (werkzeug). Hides GET / POST requests (DEBUG, ERROR, WARNING)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL + 1)
logging.getLogger('werkzeug.serving').setLevel(logging.CRITICAL + 1)
logging.getLogger('flask').setLevel(logging.ERROR)

# === SILENCE SOCKETIO ET ENGINEIO LOGS ===
logging.getLogger('socketio').setLevel(logging.CRITICAL + 1)
logging.getLogger('socketio.server').setLevel(logging.CRITICAL + 1)  
logging.getLogger('engineio').setLevel(logging.CRITICAL + 1)
logging.getLogger('engineio.server').setLevel(logging.CRITICAL + 1)

# Variables pour capturer et filtrer les logs HTTP
class HTTPLogFilter:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout
        self.suppress_http = True
        
    def write(self, text):
        # Supprimer les logs HTTP de routine si en mode tray
        if RUN_AS_TRAY and self.suppress_http:
            http_patterns = [
                '- - [',  # Format standard Apache/Werkzeug
                'GET /',
                'POST /',
                'HTTP/1.1" 200',
                'HTTP/1.1" 304',
                '::1 - -',
                '127.0.0.1 - -'
            ]
            if any(pattern in text for pattern in http_patterns):
                return
        
        if hasattr(self.original_stdout, 'write'):
            self.original_stdout.write(text)
            
    def flush(self):
        if hasattr(self.original_stdout, 'flush'):
            self.original_stdout.flush()
            
    def fileno(self):
        if hasattr(self.original_stdout, 'fileno'):
            return self.original_stdout.fileno()
        return 1

# Appliquer le filtre en mode tray seulement
if RUN_AS_TRAY:
    sys.stdout = HTTPLogFilter(sys.stdout)

# Créer le répertoire de logs
os.makedirs("logs", exist_ok=True)

# Formatter commun pour tous les logs - SANS caractères spéciaux
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

# Logger pour trames NMEA
nmea_logger = logging.getLogger("nmea_data")
nmea_logger.setLevel(logging.INFO)
nmea_handler = RotatingFileHandler("logs/nmea_data.log", maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
nmea_handler.setFormatter(file_formatter)
nmea_logger.addHandler(nmea_handler)

# Logger pour debug général
debug_logger = logging.getLogger("debug")
debug_logger.setLevel(logging.DEBUG)
debug_handler = RotatingFileHandler("logs/debug.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
debug_handler.setFormatter(file_formatter)
debug_logger.addHandler(debug_handler)

# Logger pour connexions réseau
network_logger = logging.getLogger("network")
network_logger.setLevel(logging.INFO)
network_handler = RotatingFileHandler("logs/network.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
network_handler.setFormatter(file_formatter)
network_logger.addHandler(network_handler)

# Logger pour erreurs système
error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
error_handler = RotatingFileHandler("logs/errors.log", maxBytes=1024*1024, backupCount=5, encoding='utf-8')
error_handler.setFormatter(file_formatter)
error_logger.addHandler(error_handler)

# Logger principal
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)
main_file_handler = RotatingFileHandler("logs/main.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
main_file_handler.setFormatter(file_formatter)
main_logger.addHandler(main_file_handler)

# Console handler seulement si pas en mode tray
if not RUN_AS_TRAY:
    main_console_handler = logging.StreamHandler()
    main_console_handler.setFormatter(console_formatter)
    main_logger.addHandler(main_console_handler)

# === FLASK SERVER ===
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'nmea_server_secret_2024'
cors = CORS(app)

# Socket.IO with Gevent
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# === GLOBAL VARIABLES AND THREAD MANAGEMENT ===
shutdown_event = threading.Event()

# Thread variables - globals for proper thread management
serial_thread = None
udp_thread = None
tcp_thread = None
bluetooth_monitor_thread = None

# Stop events for each thread
serial_stop = threading.Event()
udp_stop = threading.Event()
tcp_stop = threading.Event()

# === UTILITY FUNCTIONS ===
def clean_nmea_data(data):
    """Nettoie les données NMEA des préfixes de répéteur"""
    # Supprimer les préfixes de répéteur comme $AMGPGGA ou $P1GPGGA
    data = re.sub(r'^\$[A-Z0-9]{2,6}\$', '$', data)
    # Supprimer les multiples $ consécutifs
    data = re.sub(r'\$+', '$', data)
    # Supprimer les caractères de contrôle
    data = re.sub(r'[\r\n\x00-\x1F]', '', data)
    return data.strip()

def list_serial_ports():
    """Returns the list of available serial ports (name and description)."""
    try:
        ports = list(serial.tools.list_ports.comports())
        return [(p.device, p.description) for p in ports]
    except Exception as e:
        print(f"[SERIAL] Error listing ports: {e}")
        return []

def detect_bluetooth_serial_port():
    """Auto-detect Bluetooth serial port (Linux/Windows)"""
    detected_port = None
    
    if IS_LINUX:
        # Check rfcomm ports on Linux
        for i in range(0, 5):
            test_port = f"/dev/rfcomm{i}"
            if os.path.exists(test_port):
                print(f"[BLUETOOTH] Found Bluetooth port: {test_port}")
                detected_port = test_port
                break
    
    elif IS_WINDOWS:
        # Auto-detect on Windows by testing common COM ports
        ports_to_test = [f"COM{i}" for i in range(1, 21)]  # Test COM1 to COM20
        
        for port in ports_to_test:
            try:
                # Try to open the port briefly to see if it exists
                with serial.Serial(port, 4800, timeout=0.1) as ser:
                    print(f"[BLUETOOTH] Found working serial port: {port}")
                    detected_port = port
                    break
            except (OSError, serial.SerialException):
                continue  # Port not available
    
    return detected_port

# === NETWORK LISTENERS ===
def udp_listener(stop_event):
    """Écoute UDP en mode serveur"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind((UDP_IP, UDP_PORT))
        
        network_logger.info(f"UDP server listening on {UDP_IP}:{UDP_PORT}")
        if not RUN_AS_TRAY:
            print(f"[UDP] Listening on {UDP_IP}:{UDP_PORT}")
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore').strip()
                
                if message and not REJECTED_PATTERN.match(message):
                    cleaned_message = clean_nmea_data(message)
                    if cleaned_message:
                        nmea_logger.info(f"[UDP] {cleaned_message}")
                        emit_nmea_data("UDP", cleaned_message)
                        
            except socket.timeout:
                continue
            except socket.error as e:
                if not stop_event.is_set():
                    error_logger.error(f"UDP socket error: {e}")
                break
                
    except Exception as e:
        error_logger.error(f"UDP listener error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
        network_logger.info("UDP listener stopped")

def udp_client_listener(target_ip, target_port, stop_event):
    """Écoute UDP en mode client (connexion vers un serveur externe)"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1.0)
        
        network_logger.info(f"UDP client connecting to {target_ip}:{target_port}")
        if not RUN_AS_TRAY:
            print(f"[UDP] Client mode - connecting to {target_ip}:{target_port}")
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                # En mode client, on peut soit envoyer des données soit écouter
                # Pour l'instant, on écoute sur un port local et retransmet
                sock.bind(('0.0.0.0', 0))  # Bind sur un port aléatoire
                data, addr = sock.recvfrom(1024)
                message = data.decode('utf-8', errors='ignore').strip()
                
                if message and not REJECTED_PATTERN.match(message):
                    cleaned_message = clean_nmea_data(message)
                    if cleaned_message:
                        # Retransmettre vers le serveur cible
                        sock.sendto(cleaned_message.encode(), (target_ip, target_port))
                        nmea_logger.info(f"[UDP-CLIENT] Forwarded: {cleaned_message}")
                        emit_nmea_data("UDP-CLIENT", cleaned_message)
                        
            except socket.timeout:
                continue
            except socket.error as e:
                if not stop_event.is_set():
                    error_logger.error(f"UDP client error: {e}")
                break
                
    except Exception as e:
        error_logger.error(f"UDP client error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
        network_logger.info("UDP client stopped")

def tcp_listener(stop_event):
    """Écoute TCP en mode serveur"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        sock.bind((TCP_IP, TCP_PORT))
        sock.listen(5)
        
        network_logger.info(f"TCP server listening on {TCP_IP}:{TCP_PORT}")
        if not RUN_AS_TRAY:
            print(f"[TCP] Listening on {TCP_IP}:{TCP_PORT}")
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                conn, addr = sock.accept()
                network_logger.info(f"TCP connection from {addr}")
                
                with conn:
                    conn.settimeout(1.0)
                    buffer = ""
                    
                    while not stop_event.is_set() and not shutdown_event.is_set():
                        try:
                            data = conn.recv(1024)
                            if not data:
                                break
                                
                            raw_data = data.decode('utf-8', errors='ignore')
                            buffer += raw_data
                            
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                message = clean_nmea_data(line)
                                
                                if message and not REJECTED_PATTERN.match(message):
                                    nmea_logger.info(f"[TCP] {message}")
                                    emit_nmea_data("TCP", message)
                                    
                        except socket.timeout:
                            continue
                        except socket.error:
                            break
                            
            except socket.timeout:
                continue
            except socket.error as e:
                if not stop_event.is_set():
                    error_logger.error(f"TCP accept error: {e}")
                continue
                
    except Exception as e:
        error_logger.error(f"TCP listener error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
        network_logger.info("TCP listener stopped")

def tcp_client(stop_event):
    """TCP client mode - connexion vers un serveur externe"""
    try:
        network_logger.info(f"TCP client connecting to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
        if not RUN_AS_TRAY:
            print(f"[TCP] Client mode - connecting to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                sock.connect((TCP_TARGET_IP, TCP_TARGET_PORT))
                
                network_logger.info(f"TCP client connected to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
                buffer = ""
                
                while not stop_event.is_set() and not shutdown_event.is_set():
                    try:
                        data = sock.recv(1024)
                        if not data:
                            break
                            
                        raw_data = data.decode('utf-8', errors='ignore')
                        buffer += raw_data
                        
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            message = clean_nmea_data(line)
                            
                            if message and not REJECTED_PATTERN.match(message):
                                nmea_logger.info(f"[TCP-CLIENT] {message}")
                                emit_nmea_data("TCP-CLIENT", message)
                                
                    except socket.timeout:
                        continue
                    except socket.error:
                        break
                        
            except (socket.error, ConnectionRefusedError) as e:
                error_logger.warning(f"TCP client connection failed: {e}")
                time.sleep(5)  # Retry after 5 seconds
                continue
            finally:
                try:
                    sock.close()
                except:
                    pass
                    
    except Exception as e:
        error_logger.error(f"TCP client error: {e}")
    finally:
        network_logger.info("TCP client stopped")

def serial_listener(port, baudrate, stop_event):
    """Écoute série/Bluetooth avec gestion des erreurs"""
    consecutive_errors = 0
    max_errors = 20
    
    try:
        # Configuration série adaptée au système
        serial_kwargs = {
            'port': port,
            'baudrate': baudrate,
            'timeout': 1.0,
            'parity': serial.PARITY_NONE,
            'stopbits': serial.STOPBITS_ONE,
            'bytesize': serial.EIGHTBITS,
            'xonxoff': False,
            'rtscts': False,
            'dsrdtr': False
        }
        
        # Options Windows spécifiques
        if IS_WINDOWS:
            serial_kwargs['write_timeout'] = 1.0
        
        with serial.Serial(**serial_kwargs) as ser:
            network_logger.info(f"Serial port opened: {port} @ {baudrate} bps")
            if not RUN_AS_TRAY:
                print(f"[SERIAL] Port opened successfully: {port} @ {baudrate} bps")
            
            time.sleep(0.5)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            buffer = ""
            consecutive_errors = 0
            
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        if data:
                            consecutive_errors = 0
                            buffer += data
                            
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = clean_nmea_data(line)
                                
                                if line and not REJECTED_PATTERN.match(line):
                                    nmea_logger.info(f"[SERIAL] {line}")
                                    emit_nmea_data("SERIAL", line)
                    else:
                        time.sleep(0.01)
                        
                except UnicodeDecodeError:
                    consecutive_errors += 1
                    if consecutive_errors > 10:
                        error_logger.warning("Serial: Too many decoding errors, pausing...")
                        time.sleep(1)
                        consecutive_errors = 0
                    continue
                except Exception as e:
                    consecutive_errors += 1
                    error_logger.error(f"Serial read error: {e}")
                    if consecutive_errors > max_errors:
                        error_logger.error("Serial: Too many errors, stopping listener")
                        break
                    time.sleep(0.1)
                    continue
                    
    except serial.SerialException as e:
        error_logger.error(f"Cannot open serial port {port}: {e}")
        if IS_WINDOWS and not RUN_AS_TRAY:
            print(f"[ERROR][SERIAL] Cannot open port {port}: {e}")
            print("[INFO] Tip: Check if the device is connected and the port is correct")
            print("[INFO] Available ports:")
            for port_info in list_serial_ports():
                print(f"  - {port_info[0]}: {port_info[1]}")
    except Exception as e:
        error_logger.error(f"Serial listener unexpected error: {e}")
    finally:
        network_logger.info(f"Serial listener stopped for port {port}")

# === THREAD MANAGEMENT ===
def manage_threads():
    """Gère les threads UDP, TCP et série selon la configuration"""
    global serial_thread, udp_thread, tcp_thread
    
    main_logger.info(f"Starting threads - UDP:{ENABLE_UDP}, TCP:{ENABLE_TCP}, Serial:{ENABLE_SERIAL}")
    debug_logger.info(f"Thread management - UDP:{ENABLE_UDP}, TCP:{ENABLE_TCP}, Serial:{ENABLE_SERIAL}")
    
    # UDP
    if ENABLE_UDP:
        if udp_thread is None or not udp_thread.is_alive():
            udp_stop.clear()
            
            if UDP_MODE == "server":
                debug_logger.info(f"Starting UDP server thread on port {UDP_PORT}")
                udp_thread = threading.Thread(target=udp_listener, args=(udp_stop,), daemon=True)
            else:
                debug_logger.info(f"Starting UDP client thread to {UDP_TARGET_IP}:{UDP_TARGET_PORT}")
                udp_thread = threading.Thread(target=udp_client_listener, args=(UDP_TARGET_IP, UDP_TARGET_PORT, udp_stop), daemon=True)
            
            udp_thread.start()
            time.sleep(0.5)
            if udp_thread.is_alive():
                main_logger.info("UDP thread started successfully")
            else:
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
            
            if TCP_MODE == "server":
                debug_logger.info(f"Starting TCP server thread on port {TCP_PORT}")
                tcp_thread = threading.Thread(target=tcp_listener, args=(tcp_stop,), daemon=True)
            else:
                debug_logger.info(f"Starting TCP client thread to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
                tcp_thread = threading.Thread(target=tcp_client, args=(tcp_stop,), daemon=True)
            
            tcp_thread.start()
            time.sleep(0.5)
            if tcp_thread.is_alive():
                main_logger.info("TCP thread started successfully")
            else:
                error_logger.error("TCP thread failed to start")
        else:
            debug_logger.info("TCP thread already active")
    else:
        if tcp_thread and tcp_thread.is_alive():
            debug_logger.info("Stopping TCP thread")
            tcp_stop.set()
            tcp_thread = None
    
    # Serial
    if ENABLE_SERIAL and SERIAL_PORT and SERIAL_PORT != "AUTO":
        if serial_thread is None or not serial_thread.is_alive():
            debug_logger.info(f"Starting serial thread on port {SERIAL_PORT}")
            serial_stop.clear()
            serial_thread = threading.Thread(target=serial_listener, args=(SERIAL_PORT, SERIAL_BAUDRATE, serial_stop), daemon=True)
            serial_thread.start()
            time.sleep(0.5)
            if serial_thread.is_alive():
                main_logger.info("Serial thread started successfully")
            else:
                error_logger.error("Serial thread failed to start")
        else:
            debug_logger.info("Serial thread already active")
    else:
        if serial_thread and serial_thread.is_alive():
            debug_logger.info("Stopping Serial thread")
            serial_stop.set()
            serial_thread = None
    
    # Status final
    debug_logger.info(f"Final status - UDP: {'Active' if udp_thread and udp_thread.is_alive() else 'Inactive'}")
    debug_logger.info(f"Final status - TCP: {'Active' if tcp_thread and tcp_thread.is_alive() else 'Inactive'}")
    debug_logger.info(f"Final status - Serial: {'Active' if serial_thread and serial_thread.is_alive() else 'Inactive'}")

# === FLASK ROUTES ===
@app.route('/')
def config():
    return render_template('./index.html')

@app.route('/config.html')
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

@app.route('/api/nmea/latest')
def get_latest_nmea():
    """API endpoint pour obtenir les dernières données NMEA"""
    return jsonify({
        'count': len(last_nmea_data),
        'data': last_nmea_data[-10:] if len(last_nmea_data) > 10 else last_nmea_data
    })

@app.route('/select_connection', methods=['POST'])
def select_connection():
    """Update connection settings (legacy route)"""
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

    SERIAL_PORT = request.form.get('serial_port', SERIAL_PORT)
    try:
        SERIAL_BAUDRATE = int(request.form.get('serial_baudrate', SERIAL_BAUDRATE))
    except (ValueError, TypeError):
        pass
    
    # Restart threads with new configuration
    manage_threads()
    return redirect(url_for('home'))

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
        
        if not RUN_AS_TRAY:
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
        
        main_logger.info("Configuration updated via API")
        
        # Restart threads with new configuration
        manage_threads()
        
        return jsonify({
            'success': True, 
            'message': 'Configuration updated and applied successfully'
        })
        
    except Exception as e:
        error_logger.error(f"API config update error: {e}")
        if not RUN_AS_TRAY:
            print(f"[API] Error updating config: {e}")
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/status')
def api_status():
    """API endpoint pour obtenir le statut des connexions"""
    try:
        # Get thread status
        udp_active = udp_thread and udp_thread.is_alive()
        tcp_active = tcp_thread and tcp_thread.is_alive()
        serial_connected = serial_thread and serial_thread.is_alive()
        
        connections_active = sum([udp_active, tcp_active, serial_connected])
        
        status = {
            'udp_active': udp_active,
            'tcp_active': tcp_active,
            'serial_connected': serial_connected,
            'connections_active': connections_active,
            'udp_enabled': ENABLE_UDP,
            'tcp_enabled': ENABLE_TCP,
            'serial_enabled': ENABLE_SERIAL,
            'udp_mode': UDP_MODE,
            'tcp_mode': TCP_MODE
        }
        
        debug_logger.debug(f"Status API response: {status}")
        return jsonify(status)
        
    except Exception as e:
        error_logger.error(f"Status API error: {e}")
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
    """API endpoint pour obtenir l'historique NMEA"""
    try:
        return jsonify({
            'history': last_nmea_data,
            'count': len(last_nmea_data)
        })
    except Exception as e:
        error_logger.error(f"NMEA history API error: {e}")
        return jsonify({
            'history': [],
            'count': 0,
            'error': str(e)
        }), 500

@socketio.on('connect')
def handle_connect():
    """Gère les nouvelles connexions WebSocket"""
    debug_logger.info("WebSocket client connected")
    if last_nmea_data:
        emit('nmea_history', last_nmea_data[-10:])

@socketio.on('disconnect')
def handle_disconnect():
    """Gère les déconnexions WebSocket"""
    debug_logger.info("WebSocket client disconnected")

# === FLASK SERVER RUNNER ===
def run_flask_app():
    """Lance l'application Flask avec HTTPS obligatoire pour Windy Plugin"""
    try:
        cert_path = get_resource_path("cert.pem")
        key_path = get_resource_path("key.pem")
        
        # Vérifier l'existence des certificats
        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            error_msg = "SSL certificates missing - HTTPS required for Windy Plugin"
            error_logger.error(error_msg)
            if not RUN_AS_TRAY:
                print(f"[ERROR] {error_msg}")
                print(f"[ERROR] cert.pem or key.pem not found")
                print(f"[ERROR] Plugin Windy requires HTTPS/WSS connection")
            return
        
        if not RUN_AS_TRAY:
            print(f"[INFO] Starting HTTPS server on port {HTTPS_PORT}")
            print(f"[INFO] Web interface: https://localhost:{HTTPS_PORT}")
            print(f"[INFO] WebSocket: wss://localhost:{HTTPS_PORT}")
            print(f"[INFO] Plugin Windy compatible mode")
        
        main_logger.info(f"HTTPS server starting on port {HTTPS_PORT}")
        
        # Configuration SSL plus permissive pour les certificats auto-signés
        import ssl
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(cert_path, key_path)
        
        # Options SSL plus flexibles pour accepter les connexions locales
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Serveur HTTPS avec configuration SSL optimisée
        server = WSGIServer(
            ('0.0.0.0', HTTPS_PORT), 
            app,
            ssl_context=ssl_context,
            log=None,  # Disable default logging
            handler_class=None
        )
        
        if not RUN_AS_TRAY:
            print(f"[INFO] HTTPS server ready - accepting self-signed certificates")
        
        server.serve_forever()
        
    except Exception as e:
        error_logger.error(f"HTTPS server error: {e}")
        if not RUN_AS_TRAY:
            print(f"[ERROR] HTTPS server failed: {e}")
            print(f"[ERROR] Cannot start HTTPS - Plugin Windy won't work without SSL")
            print(f"[ERROR] Check certificates: cert.pem and key.pem")
        
        # En cas d'échec, essayer de regénérer les certificats
        regenerate_certificates()

def regenerate_certificates():
    """Tente de regénérer des certificats SSL"""
    try:
        if not RUN_AS_TRAY:
            print("[INFO] Attempting to regenerate SSL certificates...")
        
        # Essayer d'exécuter la génération de certificats
        import subprocess
        
        # Commande pour générer des certificats auto-signés
        cmd = [
            'openssl', 'req', '-x509', '-newkey', 'rsa:4096', 
            '-keyout', 'key.pem', '-out', 'cert.pem', 
            '-days', '365', '-nodes', '-subj', '/CN=localhost'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            if not RUN_AS_TRAY:
                print("[INFO] SSL certificates regenerated successfully")
            main_logger.info("SSL certificates regenerated")
            # Essayer de redémarrer le serveur
            run_flask_app()
        else:
            if not RUN_AS_TRAY:
                print(f"[ERROR] Failed to regenerate certificates: {result.stderr}")
                print("[INFO] Please install OpenSSL or provide valid certificates")
            
    except Exception as e:
        error_logger.error(f"Certificate regeneration failed: {e}")
        if not RUN_AS_TRAY:
            print(f"[ERROR] Certificate regeneration failed: {e}")

# === MAIN FUNCTION ===
def main_thread():
    """Thread principal du serveur"""
    global SERIAL_PORT, ENABLE_SERIAL, serial_thread
    
    if not RUN_AS_TRAY:
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
    
    main_logger.info(f"NMEA Server starting - Mode: {'Tray' if RUN_AS_TRAY else 'Console'}")
    
    # Auto-detection of serial port if necessary
    if ENABLE_SERIAL and (not SERIAL_PORT or SERIAL_PORT == "AUTO"):
        detected_port = detect_bluetooth_serial_port()
        if detected_port:
            SERIAL_PORT = detected_port
            if not RUN_AS_TRAY:
                print(f"[INFO] Serial port auto-detected: {SERIAL_PORT}")
            main_logger.info(f"Serial port auto-detected: {SERIAL_PORT}")
            
            if serial_thread is None or not serial_thread.is_alive():
                serial_stop.clear()
                serial_thread = threading.Thread(target=serial_listener, args=(SERIAL_PORT, SERIAL_BAUDRATE, serial_stop), daemon=True)
                serial_thread.start()
        else:
            if not RUN_AS_TRAY:
                print("[INFO] No serial port detected - serial function disabled")
            main_logger.info("No serial port detected - serial function disabled")
            ENABLE_SERIAL = False
    
    # Start network threads
    manage_threads()
    time.sleep(0.5)

    try:
        if not RUN_AS_TRAY:
            print(f"[INFO] Launching Flask server on port {HTTPS_PORT}")
        run_flask_app()
    except KeyboardInterrupt:
        if not RUN_AS_TRAY:
            print("\n[INFO] Shutdown initiated by user")
        main_logger.info("Shutdown initiated by user")
    except Exception as e:
        error_logger.error(f"Server error: {e}")
        if not RUN_AS_TRAY:
            print(f"[ERROR] Server error: {e}")
    finally:
        main_logger.info("Server stopped")
        if not RUN_AS_TRAY:
            print("[INFO] Server stopped.")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n[INFO] Received signal {signum}, shutting down...")
    shutdown_event.set()
    if tray_icon:
        tray_icon.stop()
    os._exit(0)

# === MAIN ENTRY POINT ===
if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Handle command line arguments
    if "--console" in sys.argv:
        # Force console mode
        print("[INFO] Console mode forced by --console argument")
        main_thread()
    elif RUN_AS_TRAY:
        # Run in system tray mode
        print("[INFO] Starting in system tray mode...")
        print("[INFO] Use --console to force console mode")
        
        # Start server in background thread
        server_thread = threading.Thread(target=main_thread, daemon=True)
        server_thread.start()
        
        # Wait a bit for server to start
        time.sleep(2)
        
        # Run system tray (this blocks)
        success = run_tray()
        if not success:
            print("[INFO] System tray failed, falling back to console mode")
            main_thread()
    else:
        # Console mode
        print("[INFO] Running in console mode")
        print("[INFO] Use --tray to force system tray mode")
        main_thread()
