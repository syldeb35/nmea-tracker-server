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
#import subprocess
#import ssl
import time  # Required import
from flask import Flask, Response, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import ssl

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

# === LOG CONFIGURATION ===
# Disable HTTP logs (werkzeug). Hides GET / POST requests (DEBUG, ERROR, WARNING)
# logging.getLogger('werkzeug').setLevel(logging.ERROR)

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

# === SIMPLE BLUETOOTH SERIAL PORT DETECTION ===
def detect_bluetooth_serial_port():
    """
    Attempts to automatically detect an active Bluetooth serial port.
    Compatible with Windows, macOS, Linux.
    Returns the port name (e.g. /dev/rfcomm0 or COM4), or None.
    """
    print("[AUTO-DETECT] Searching for serial ports...")
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        print("[AUTO-DETECT] No serial ports detected")
        return None
    
    print(f"[AUTO-DETECT] {len(ports)} serial port(s) found:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")
    
    # Patterns adapted according to OS
    if IS_WINDOWS:
        # Broader search on Windows
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
                print(f"[AUTO-DETECT] Serial port detected: {port_name} ({desc})")
                return port_name
    # If nothing found, return first available port on Windows
    if IS_WINDOWS and ports:
        first_port = ports[0].device
        print(f"[AUTO-DETECT] No Bluetooth port, using first port: {first_port}")
        return first_port
    
    print("[AUTO-DETECT] No Bluetooth serial port detected.")
    return None

def list_serial_ports():
    """Returns the list of available serial ports (name and description)."""
    ports = list(serial.tools.list_ports.comports())
    return [(p.device, p.description) for p in ports]
    
        
# === FLAGS AND THREADS FOR DYNAMIC MANAGEMENT ===
serial_thread = None
udp_thread = None
tcp_thread = None
serial_stop = threading.Event()
udp_stop = threading.Event()
tcp_stop = threading.Event()

# === MODIFIED FUNCTIONS TO SUPPORT STOPPING ===
def udp_listener(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f"[UDP] Listening on {UDP_IP}:{UDP_PORT}")
    sock.settimeout(1.0)
    while not stop_event.is_set():
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
    sock.close()
    print("[UDP] Stopped.")

def tcp_listener(stop_event):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(1)
    print(f"[TCP] Listening on {TCP_IP}:{TCP_PORT}")
    sock.settimeout(1.0)
    while not stop_event.is_set():
        try:
            conn, addr = sock.accept()
            print(f"[TCP] Connection from {addr}")
            with conn:
                conn.settimeout(1.0)
                while not stop_event.is_set():
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
        except socket.timeout:
            continue
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
            
            while not stop_event.is_set():
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


# === THREAD MANAGEMENT FUNCTION ===
def manage_threads():
    global serial_thread, udp_thread, tcp_thread
    # SERIAL
    if ENABLE_SERIAL:
        if serial_thread is None or not serial_thread.is_alive():
            serial_stop.clear()
            serial_thread = threading.Thread(target=serial_listener, args=(SERIAL_PORT, SERIAL_BAUDRATE, serial_stop), daemon=True)
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

def run_flask_app():
    print(f"[INFO] Starting Flask server on port {HTTPS_PORT}")
    
    # Absolute paths for certificates
    cert_path = os.path.abspath('./cert.pem')
    key_path = os.path.abspath('./key.pem')
    
    # Check certificate existence
    if os.path.exists(cert_path) and os.path.exists(key_path):
        print("[INFO] SSL certificates found - starting HTTPS")
        try:
            # Suppress verbose SSL logs
            import logging
            logging.getLogger('gevent.ssl').setLevel(logging.WARNING)
            
            http_server = WSGIServer(
                ('0.0.0.0', HTTPS_PORT), 
                app, 
                keyfile=key_path, 
                certfile=cert_path,
                log=None  # Suppress SSL logs
            )
            print(f"[INFO] HTTPS server active on https://localhost:{HTTPS_PORT}")
            print(f"[INFO] Web interface: https://localhost:{HTTPS_PORT}/config.html")
            http_server.serve_forever()
        except Exception as e:
            print(f"[ERROR] HTTPS impossible: {e}")
            run_http_fallback()
    else:
        print(f"[INFO] SSL certificates missing - starting HTTP")
        run_http_fallback()

def run_http_fallback():
    """Start server in simple HTTP mode"""
    try:
        print(f"[INFO] HTTP server active on http://localhost:{HTTPS_PORT}")
        print(f"[INFO] Web interface: http://localhost:{HTTPS_PORT}/config.html")
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=HTTPS_PORT, 
            debug=False,  # Disable verbose logs
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        print(f"[ERROR] Cannot start server: {e}")

def main_thread():
    global SERIAL_PORT, ENABLE_SERIAL
    print("[INFO] Starting NMEA server...")
    print(f"[INFO] Configuration:")
    print(f"  - Serial: {ENABLE_SERIAL} (Port: {SERIAL_PORT})")
    print(f"  - UDP: {ENABLE_UDP} (Port: {UDP_PORT})")
    print(f"  - TCP: {ENABLE_TCP} (Port: {TCP_PORT})")
    print(f"  - Debug: {DEBUG}")
    
    # Auto-detection of serial port if necessary
    if ENABLE_SERIAL and (not SERIAL_PORT or SERIAL_PORT == "AUTO"):
        detected_port = detect_bluetooth_serial_port()
        if detected_port:
            SERIAL_PORT = detected_port
            print(f"[INFO] Serial port auto-detected: {SERIAL_PORT}")
        else:
            print("[INFO] No serial port detected - serial function disabled")
            ENABLE_SERIAL = False
    
    # Start threads for UDP, TCP and Serial if enabled
    manage_threads()
    
    # Small pause to let threads start
    time.sleep(0.5)

    # Launch Flask server
    print(f"[INFO] Launching Flask server on port {HTTPS_PORT}")
    run_flask_app()


# === FLASK ROUTES ===
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


if __name__ == '__main__':
    main_thread()
    
    print(f"[INFO] SocketIO async mode: {socketio.async_mode}")

    print(f"[HTTPS] Secure WebSocket server on https://0.0.0.0:{HTTPS_PORT}")
