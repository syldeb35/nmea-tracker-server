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
from flask import Flask, Response, render_template, request, redirect, url_for
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
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
TCP_IP = "0.0.0.0"
TCP_PORT = 5006
HTTPS_PORT = 5000
REJECTED_PATTERN = re.compile(r'^\$([A-Z][A-Z])(GS[A-Z]|XDR|AMAID|AMCLK|AMSA|SGR|MMB|MDA)')

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

# === LOG CONFIGURATION ===
# Disable HTTP logs (werkzeug). Hides GET / POST requests (DEBUG, ERROR, WARNING)
# logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Disable SSL error logs on Windows to avoid certificate warnings
if IS_WINDOWS:
    import logging
    # Suppress SSL errors and gevent SSL warnings
    logging.getLogger('gevent.ssl').setLevel(logging.CRITICAL)
    logging.getLogger('ssl').setLevel(logging.CRITICAL)
    # Suppress certificate verification warnings if urllib3 is available
    try:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    except ImportError:
        pass  # urllib3 not available, ignore

# Logger for NMEA frames only
nmea_logger = logging.getLogger("nmea")
nmea_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(message)s')
os.makedirs("logs", exist_ok=True)  # Create logs folder if it doesn't exist
file_handler = RotatingFileHandler(
    "logs/nmea.log",            # main log file
    maxBytes=1024 * 1024,    # 1 MB max
    backupCount=3          # keep up to 3 old files (nmea.log.1, .2, .3)
)
file_handler.setFormatter(log_formatter)
nmea_logger.addHandler(file_handler)

# === FLASK SERVER ===
app = Flask(__name__)
# socketio = SocketIO(app, cors_allowed_origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')
CORS(app)  # Allow all origins (wildcard origin *)

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

# === MODIFIED FUNCTIONS TO SUPPORT STOPPING ===
def udp_listener(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[UDP] Listening on {UDP_IP}:{UDP_PORT}")
    sock.settimeout(1.0)
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8', errors='ignore').strip()
            if not REJECTED_PATTERN.match(message):
                if DEBUG:
                    print(f"[NMEA][UDP]{message}")
                nmea_logger.info(f"[NMEA][UDP] {message}")
                socketio.emit('nmea_data', message)
        except socket.timeout:
            continue
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[UDP] Error: {e}")
            break
    sock.close()
    print("[UDP] Stopped.")

def tcp_listener(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(1)
    print(f"[TCP] Listening on {TCP_IP}:{TCP_PORT}")
    sock.settimeout(1.0)
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            conn, addr = sock.accept()
            print(f"[TCP] Connection from {addr}")
            with conn:
                conn.settimeout(1.0)
                while not stop_event.is_set() and not shutdown_event.is_set():
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        message = data.decode('utf-8', errors='ignore').strip()
                        if not REJECTED_PATTERN.match(message):
                            if DEBUG:
                                print(f"[NMEA][TCP]{message}")
                            nmea_logger.info(f"[NMEA][TCP] {message}")
                            socketio.emit('nmea_data', message)
                    except socket.timeout:
                        continue
                    except Exception as e:
                        if not shutdown_event.is_set():
                            print(f"[TCP] Connection error: {e}")
                        break
        except socket.timeout:
            continue
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[TCP] Error: {e}")
            break
    sock.close()
    print("[TCP] Stopped.")

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
                                line = line.strip()
                                
                                if line and not REJECTED_PATTERN.match(line):
                                    if DEBUG:
                                        print(f"[NMEA][SERIAL] {line}")
                                    nmea_logger.info(f"[SERIAL] {line}")
                                    socketio.emit('nmea_data', line)
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
def manage_threads():
    global serial_thread, udp_thread, tcp_thread, bluetooth_monitor_thread
    
    # BLUETOOTH MONITOR (uniquement sur Linux)
    if IS_LINUX and ENABLE_SERIAL:
        if bluetooth_monitor_thread is None or not bluetooth_monitor_thread.is_alive():
            bluetooth_monitor_stop.clear()
            bluetooth_monitor_thread = threading.Thread(target=bluetooth_monitor, args=(bluetooth_monitor_stop,), daemon=True)
            bluetooth_monitor_thread.start()
            print("[BLUETOOTH-MONITOR] Thread de surveillance démarré")
    else:
        if bluetooth_monitor_thread and bluetooth_monitor_thread.is_alive():
            bluetooth_monitor_stop.set()
            bluetooth_monitor_thread = None
    
    # SERIAL - seulement si ce n'est pas AUTO ou si AUTO est résolu
    if ENABLE_SERIAL:
        actual_port = SERIAL_PORT
        
        # Si mode AUTO, ne démarrer le thread série que si une connexion Bluetooth est établie
        if SERIAL_PORT == "AUTO":
            # Ne pas démarrer le thread série maintenant - le bluetooth monitor s'en chargera
            print("[AUTO-DETECT] Mode AUTO - attente de la découverte Bluetooth...")
        else:
            # Port spécifique fourni - démarrer le thread série
            if serial_thread is None or not serial_thread.is_alive():
                print(f"[THREAD-MANAGER] Démarrage thread série sur {actual_port}")
                serial_stop.clear()
                serial_thread = threading.Thread(target=serial_listener, args=(actual_port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                serial_thread.start()
    else:
        if serial_thread and serial_thread.is_alive():
            serial_stop.set()
            serial_thread = None
            
    # UDP
    if ENABLE_UDP:
        if udp_thread is None or not udp_thread.is_alive():
            udp_stop.clear()
            udp_thread = threading.Thread(target=udp_listener, args=(udp_stop,), daemon=True)
            udp_thread.start()
    else:
        if udp_thread and udp_thread.is_alive():
            udp_stop.set()
            udp_thread = None
    # TCP
    if ENABLE_TCP:
        if tcp_thread is None or not tcp_thread.is_alive():
            tcp_stop.clear()
            tcp_thread = threading.Thread(target=tcp_listener, args=(tcp_stop,), daemon=True)
            tcp_thread.start()
    else:
        if tcp_thread and tcp_thread.is_alive():
            tcp_stop.set()
            tcp_thread = None

def create_self_signed_cert():
    """Create a self-signed certificate for HTTPS on Windows if needed"""
    try:
        # Try to create self-signed certificates if they don't exist
        import datetime
        import ipaddress
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
    print(f"[INFO] Starting Flask server on port {HTTPS_PORT}")
    
    # Paths for certificates - compatible with PyInstaller
    cert_path = get_resource_path('cert.pem')
    key_path = get_resource_path('key.pem')
    
    print(f"[DEBUG] Looking for certificates:")
    print(f"[DEBUG]   cert.pem: {cert_path}")
    print(f"[DEBUG]   key.pem: {key_path}")
    
    # Create certificates if they don't exist on Windows
    if IS_WINDOWS and not (os.path.exists(cert_path) and os.path.exists(key_path)):
        print("[INFO] Certificats SSL manquants sur Windows - tentative de création...")
        create_self_signed_cert()
    
    # Check certificate existence
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("[INFO] SSL certificates found - starting HTTPS")
        try:
            # Suppress verbose SSL logs
            import logging
            logging.getLogger('gevent.ssl').setLevel(logging.ERROR)  # Plus strict pour masquer les erreurs SSL
            
            # Configuration SSL plus robuste pour Windows
            ssl_context = None
            if IS_WINDOWS:
                try:
                    import ssl
                    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    ssl_context.load_cert_chain(cert_path, key_path)
                    # Paramètres SSL plus tolérants pour Windows
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    print("[INFO] Configuration SSL Windows activée")
                except Exception as ssl_error:
                    print(f"[WARNING] Impossible de configurer SSL context: {ssl_error}")
                    ssl_context = None
            
            if ssl_context:
                # Utilisation du contexte SSL personnalisé
                http_server = WSGIServer(
                    ('0.0.0.0', HTTPS_PORT), 
                    app,
                    ssl_context=ssl_context,
                    log=None,  # Suppress SSL logs
                    error_log=None  # Suppress error logs
                )
            else:
                # Fallback : méthode traditionnelle
                http_server = WSGIServer(
                    ('0.0.0.0', HTTPS_PORT), 
                    app, 
                    keyfile=key_path, 
                    certfile=cert_path,
                    log=None,  # Suppress SSL logs
                    error_log=None  # Suppress error logs
                )
            
            print(f"[INFO] HTTPS server active on https://localhost:{HTTPS_PORT}")
            print(f"[INFO] Web interface: https://localhost:{HTTPS_PORT}/config.html")
            print("[INFO] Press Ctrl+C to stop the server")
            
            if IS_WINDOWS:
                print("[INFO] Note: Sur Windows, ignorez les erreurs SSL occasionnelles")
                print("[INFO] Alternative HTTP disponible sur http://localhost:{HTTPS_PORT}")
            
            http_server.serve_forever()
            
        except KeyboardInterrupt:
            print("\n[INFO] Keyboard interrupt received")
        except Exception as e:
            if not shutdown_event.is_set():
                print(f"[ERROR] HTTPS impossible: {e}")
                print("[INFO] Basculement vers HTTP...")
                run_http_fallback()
    else:
        print(f"[INFO] SSL certificates missing - starting HTTP")
        run_http_fallback()

def run_http_fallback():
    """Start server in simple HTTP mode"""
    try:
        print(f"[INFO] HTTP server active on http://localhost:{HTTPS_PORT}")
        print(f"[INFO] Web interface: http://localhost:{HTTPS_PORT}/config.html")
        if IS_WINDOWS:
            print("[INFO] Mode HTTP - pas d'erreurs SSL sur Windows")
        print("[INFO] Press Ctrl+C to stop the server")
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=HTTPS_PORT, 
            debug=False,  # Disable verbose logs
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n[INFO] Keyboard interrupt received")
    except Exception as e:
        if not shutdown_event.is_set():
            print(f"[ERROR] Cannot start server: {e}")

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

def main_thread():
    global SERIAL_PORT, ENABLE_SERIAL, serial_thread
    print("[INFO] Starting NMEA server...")
    print(f"[INFO] Configuration:")
    print(f"  - Serial: {ENABLE_SERIAL} (Port: {SERIAL_PORT})")
    print(f"  - UDP: {ENABLE_UDP} (Port: {UDP_PORT})")
    print(f"  - TCP: {ENABLE_TCP} (Port: {TCP_PORT})")
    print(f"  - Debug: {DEBUG}")
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

# Instance globale du gestionnaire Bluetooth
bluetooth_manager = BluetoothGPSManager()

if __name__ == '__main__':
    main_thread()
    print(f"[INFO] SocketIO async mode: {socketio.async_mode}")
    print(f"[HTTPS] Secure WebSocket server on https://0.0.0.0:{HTTPS_PORT}")
