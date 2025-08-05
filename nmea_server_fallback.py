#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMEA Server Fallback - Version sans gevent pour compatibilité Python 3.13+
Version simplifiée du serveur NMEA utilisant Flask standard au lieu de gevent
"""

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
import time
import datetime
import ipaddress
import warnings
from flask import Flask, Response, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit

# Import CORS optionnel pour compatibilité maximale
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("[WARNING] flask_cors non disponible - CORS désactivé")

from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Operating system detection
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

print("[FALLBACK] NMEA Server Fallback - Version sans gevent")

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
UDP_MODE = os.getenv("UDP_MODE", "server")
TCP_MODE = os.getenv("TCP_MODE", "server")
UDP_TARGET_IP = os.getenv("UDP_TARGET_IP", "")
UDP_TARGET_PORT = int(os.getenv("UDP_TARGET_PORT", "50110"))
TCP_TARGET_IP = os.getenv("TCP_TARGET_IP", "")
TCP_TARGET_PORT = int(os.getenv("TCP_TARGET_PORT", "50110"))
REJECTED_PATTERN = re.compile(r'^\$([A-Z][A-Z])(GS[A-Z]|XDR|AMAID|AMCLK|AMSA|SGR|MMB|MDA)')

# Variables globales pour les données NMEA en temps réel
last_nmea_data = []
max_nmea_buffer = 50

# Default serial port according to OS
DEFAULT_SERIAL_PORT = "COM5" if IS_WINDOWS else "AUTO"
SERIAL_PORT = os.getenv("SERIAL_PORT", DEFAULT_SERIAL_PORT).strip()
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 4800))
ENABLE_SERIAL = os.getenv("ENABLE_SERIAL", "True").lower() == "true"
ENABLE_UDP = os.getenv("ENABLE_UDP", "True").lower() == "true"
ENABLE_TCP = os.getenv("ENABLE_TCP", "True").lower() == "true"

# === LOG CONFIGURATION ===
logging.getLogger('werkzeug').setLevel(logging.CRITICAL + 1)
logging.getLogger('werkzeug.serving').setLevel(logging.CRITICAL + 1)
logging.getLogger('flask').setLevel(logging.ERROR)

# Système de logs
os.makedirs("logs", exist_ok=True)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

# Loggers
nmea_logger = logging.getLogger("nmea_data")
nmea_logger.setLevel(logging.INFO)
nmea_handler = RotatingFileHandler("logs/nmea_data.log", maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
nmea_handler.setFormatter(file_formatter)
nmea_logger.addHandler(nmea_handler)

debug_logger = logging.getLogger("debug")
debug_logger.setLevel(logging.DEBUG)
debug_handler = RotatingFileHandler("logs/debug.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
debug_handler.setFormatter(file_formatter)
debug_logger.addHandler(debug_handler)

main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)
main_file_handler = RotatingFileHandler("logs/main.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
main_file_handler.setFormatter(file_formatter)
main_logger.addHandler(main_file_handler)

main_console_handler = logging.StreamHandler()
main_console_handler.setFormatter(console_formatter)
main_logger.addHandler(main_console_handler)

# === FLASK SERVER (sans gevent) ===
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')  # Threading au lieu de gevent

# Activer CORS seulement si disponible
if CORS_AVAILABLE:
    CORS(app)
    print("[INFO] CORS activé")
else:
    print("[WARNING] CORS non configuré - connexions cross-origin limitées")

# === SHUTDOWN MANAGEMENT ===
shutdown_event = threading.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals (Ctrl+C, SIGTERM, etc.)"""
    print(f"\n[INFO] Signal {signum} received - shutting down gracefully...")
    shutdown_event.set()
    
    # Stop all threads
    serial_stop.set()
    udp_stop.set()
    tcp_stop.set()
    
    print("[INFO] Shutdown complete.")
    sys.exit(0)

def cleanup_on_exit():
    """Cleanup function called on normal exit"""
    if not shutdown_event.is_set():
        shutdown_event.set()
        serial_stop.set()
        udp_stop.set()
        tcp_stop.set()
        print("[INFO] Cleanup completed.")

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
if not IS_WINDOWS:
    signal.signal(signal.SIGHUP, signal_handler)

atexit.register(cleanup_on_exit)

# === THREAD FLAGS ===
serial_thread = None
udp_thread = None
tcp_thread = None
serial_stop = threading.Event()
udp_stop = threading.Event()
tcp_stop = threading.Event()

# === NMEA DATA EMISSION ===
def emit_nmea_data(source, message):
    """Émet les données NMEA via WebSocket et les stocke"""
    global last_nmea_data
    
    try:
        if source is None or source == "":
            source = "UNKNOWN"
        if message is None or message == "":
            return
            
        message = str(message).strip()
        if not message or message == "undefined":
            return
        
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}][{source}] {message}"
        
        last_nmea_data.append(formatted_message)
        if len(last_nmea_data) > max_nmea_buffer:
            last_nmea_data.pop(0)
        
        nmea_logger.info(f"{source}: {message}")
        
        if DEBUG:
            debug_logger.debug(f"EMIT {source}: {message[:50]}...")
            
        try:
            socketio.emit('nmea_data', message)
        except Exception as windy_error:
            main_logger.error(f"Erreur émission Windy: {windy_error}")
        
        try:
            web_data = {
                'source': source,
                'message': message,
                'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
            }
            socketio.emit('nmea_data_web', web_data)
        except Exception as ws_error:
            main_logger.error(f"Erreur émission WebSocket: {ws_error}")
                
    except Exception as e:
        main_logger.error(f"Erreur lors de l'émission NMEA: {e}")

# === UTILITY FUNCTIONS ===
def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def clean_nmea_data(data):
    """Nettoie les données NMEA des préfixes de répéteur"""
    data = re.sub(r'^\$[A-Z0-9]{2,6}\$', '$', data)
    data = re.sub(r'\$+', '$', data)
    data = re.sub(r'[\r\n\x00-\x1F]', '', data)
    return data.strip()

def list_serial_ports():
    """Returns the list of available serial ports (name and description)."""
    ports = list(serial.tools.list_ports.comports())
    return [(p.device, p.description) for p in ports]

# === NETWORK LISTENERS (simplifiés, sans gevent) ===
def udp_listener(stop_event):
    """UDP listener standard"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(("0.0.0.0", UDP_PORT))
        main_logger.info(f"UDP Listening on 0.0.0.0:{UDP_PORT}")
        sock.settimeout(1.0)
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                message = clean_nmea_data(data.decode('utf-8', errors='ignore'))
                if not REJECTED_PATTERN.match(message):
                    if message and message.strip():
                        emit_nmea_data("UDP", message.strip())
            except socket.timeout:
                continue
            except Exception as e:
                if not shutdown_event.is_set():
                    main_logger.error(f"UDP Error: {e}")
                break
                
    except Exception as e:
        main_logger.error(f"UDP Bind error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
    
    main_logger.info("UDP Stopped")

def tcp_listener(stop_event):
    """TCP listener standard"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind(("0.0.0.0", TCP_PORT))
        sock.listen(1)
        main_logger.info(f"TCP Listening on 0.0.0.0:{TCP_PORT}")
        sock.settimeout(1.0)
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                conn, addr = sock.accept()
                main_logger.info(f"TCP Connection from {addr}")
                
                with conn:
                    conn.settimeout(1.0)
                    buffer = ""
                    
                    while not stop_event.is_set() and not shutdown_event.is_set():
                        try:
                            data = conn.recv(1024)
                            if not data:
                                break
                            
                            buffer += data.decode('utf-8', errors='ignore')
                            
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                message = clean_nmea_data(line)
                                
                                if message and not REJECTED_PATTERN.match(message):
                                    emit_nmea_data("TCP", message.strip())
                            
                            if len(buffer) > 4096:
                                buffer = ""
                                
                        except socket.timeout:
                            continue
                        except Exception as e:
                            if not shutdown_event.is_set():
                                main_logger.error(f"TCP connection error: {e}")
                            break
                            
            except socket.timeout:
                continue
            except Exception as e:
                if not shutdown_event.is_set():
                    main_logger.error(f"TCP accept error: {e}")
                break
                
    except Exception as e:
        main_logger.error(f"TCP bind error: {e}")
    finally:
        try:
            sock.close()
        except:
            pass
    
    main_logger.info("TCP Stopped")

def serial_listener(port, baudrate, stop_event):
    """Serial listener standard"""
    main_logger.info(f"Serial Listener starting on {port} @ {baudrate} bps")
    
    if not port or port == "None":
        main_logger.info("No serial port configured")
        return
    
    try:
        serial_kwargs = {
            'port': port,
            'baudrate': baudrate,
            'timeout': 0.1
        }
        
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
        
        with serial.Serial(**serial_kwargs) as ser:
            main_logger.info(f"Serial port opened: {port}")
            time.sleep(0.5)
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            buffer = ""
            
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    if ser.in_waiting > 0:
                        data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                        if data:
                            buffer += data
                            
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line = clean_nmea_data(line)
                                
                                if line and not REJECTED_PATTERN.match(line):
                                    if line and line.strip():
                                        emit_nmea_data("SERIAL", line.strip())
                    else:
                        time.sleep(0.01)
                        
                except Exception as e:
                    if DEBUG:
                        main_logger.error(f"Serial read error: {e}")
                    time.sleep(0.1)
                    continue
                    
    except serial.SerialException as e:
        main_logger.error(f"Cannot open serial port {port}: {e}")
    except Exception as e:
        main_logger.error(f"Serial unexpected error: {e}")
    
    main_logger.info("Serial Stopped")

# === THREAD MANAGEMENT ===
def manage_threads():
    global serial_thread, udp_thread, tcp_thread
    
    main_logger.info(f"Starting threads - UDP:{ENABLE_UDP}, TCP:{ENABLE_TCP}, Serial:{ENABLE_SERIAL}")
    
    # UDP
    if ENABLE_UDP:
        if udp_thread is None or not udp_thread.is_alive():
            udp_stop.clear()
            udp_thread = threading.Thread(target=udp_listener, args=(udp_stop,), daemon=True)
            udp_thread.start()
            main_logger.info("UDP thread started")
    
    # TCP
    if ENABLE_TCP:
        if tcp_thread is None or not tcp_thread.is_alive():
            tcp_stop.clear()
            tcp_thread = threading.Thread(target=tcp_listener, args=(tcp_stop,), daemon=True)
            tcp_thread.start()
            main_logger.info("TCP thread started")
    
    # Serial
    if ENABLE_SERIAL and SERIAL_PORT and SERIAL_PORT != "AUTO":
        if serial_thread is None or not serial_thread.is_alive():
            serial_stop.clear()
            serial_thread = threading.Thread(target=serial_listener, args=(SERIAL_PORT, SERIAL_BAUDRATE, serial_stop), daemon=True)
            serial_thread.start()
            main_logger.info("Serial thread started")

# === FLASK APP ===
def run_flask_app():
    """Lancer le serveur Flask en mode HTTP simple"""
    main_logger.info(f"Starting HTTP server on port {HTTPS_PORT}")
    main_logger.info(f"Web interface: http://localhost:{HTTPS_PORT}/config.html")
    main_logger.info("Press Ctrl+C to stop the server")
    
    try:
        # Configuration pour supprimer les logs HTTP
        log = logging.getLogger('werkzeug')
        log.disabled = True
        
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=HTTPS_PORT, 
            debug=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        main_logger.info("Keyboard interrupt received")
    except Exception as e:
        if not shutdown_event.is_set():
            main_logger.error(f"Cannot start server: {e}")

# === MAIN THREAD ===
def main_thread():
    global SERIAL_PORT, ENABLE_SERIAL
    
    main_logger.info("NMEA Server Fallback (sans gevent) démarré")
    main_logger.info(f"Configuration:")
    main_logger.info(f"  - DEBUG: {DEBUG}")
    main_logger.info(f"  - Serial: {ENABLE_SERIAL} (Port: {SERIAL_PORT})")
    main_logger.info(f"  - UDP: {ENABLE_UDP} (Port: {UDP_PORT})")
    main_logger.info(f"  - TCP: {ENABLE_TCP} (Port: {TCP_PORT})")
    
    # Auto-detection du port série si nécessaire
    if ENABLE_SERIAL and (not SERIAL_PORT or SERIAL_PORT == "AUTO"):
        # Détection simplifiée pour le fallback
        ports = list(serial.tools.list_ports.comports())
        if ports:
            SERIAL_PORT = ports[0].device
            main_logger.info(f"Serial port auto-detected: {SERIAL_PORT}")
        else:
            main_logger.info("No serial port detected - serial disabled")
            ENABLE_SERIAL = False
    
    # Démarrer les threads
    manage_threads()
    time.sleep(0.5)
    
    try:
        run_flask_app()
    except KeyboardInterrupt:
        main_logger.info("Shutdown initiated by user")
    except Exception as e:
        main_logger.error(f"Server error: {e}")
    finally:
        main_logger.info("Server stopped")

# === FLASK ROUTES (basiques pour compatibilité) ===
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

@app.route('/', methods=['GET'])
def config():
    return render_template('./index.html')

if __name__ == "__main__":
    main_thread()
