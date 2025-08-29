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

# === SERVICE MODE I/O REDIRECTION ===
# When running without console (service mode), redirect all I/O to files
def setup_service_mode_io():
    """Setup I/O redirection for console-less execution"""
    try:
        # Check if we're running without a console (PyInstaller with console=False)
        import ctypes
        if IS_WINDOWS:
            kernel32 = ctypes.windll.kernel32
            if kernel32.GetConsoleWindow() == 0:
                # No console window - redirect all I/O to files
                os.makedirs("logs", exist_ok=True)
                
                # Redirect stdout to log file
                stdout_log = open("logs/stdout.log", "a", encoding='utf-8', buffering=1)
                sys.stdout = stdout_log
                
                # Redirect stderr to log file
                stderr_log = open("logs/stderr.log", "a", encoding='utf-8', buffering=1)
                sys.stderr = stderr_log
                
                return True  # Service mode detected
        
        # On Linux, check if stderr/stdout are available
        if not IS_WINDOWS:
            try:
                sys.stdout.fileno()
                sys.stderr.fileno()
            except (AttributeError, OSError):
                # No console available - redirect to files
                os.makedirs("logs", exist_ok=True)
                sys.stdout = open("logs/stdout.log", "a", encoding='utf-8', buffering=1)
                sys.stderr = open("logs/stderr.log", "a", encoding='utf-8', buffering=1)
                return True
        
        return False  # Console mode
        
    except Exception:
        # Fallback: if detection fails, assume console mode
        return False

# Apply service mode I/O redirection
SERVICE_MODE = setup_service_mode_io()
if SERVICE_MODE:
    print(f"[{datetime.datetime.now()}] Service mode detected - I/O redirected to logs/")
else:
    print("[INFO] Console mode detected - normal I/O")

# Load environment variables from .env file
load_dotenv()

# === GLOBAL VARIABLES ===
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
UDP_IP = os.getenv("UDP_IP", "0.0.0.0")
UDP_PORT = int(os.getenv("UDP_PORT", "5005"))
TCP_IP = os.getenv("TCP_IP", "0.0.0.0")
TCP_PORT = int(os.getenv("TCP_PORT", "5006"))
HTTPS_PORT = int(os.getenv("HTTPS_PORT", "5000"))

UDP_MODE = os.getenv("UDP_MODE", "server")  # "server" or "client"
TCP_MODE = os.getenv("TCP_MODE", "client")  # "server" or "client" - default client to avoid port conflicts
UDP_TARGET_IP = os.getenv("UDP_TARGET_IP", "")
UDP_TARGET_PORT = int(os.getenv("UDP_TARGET_PORT", "50110"))
TCP_TARGET_IP = os.getenv("TCP_TARGET_IP", "")
TCP_TARGET_PORT = int(os.getenv("TCP_TARGET_PORT", "50110"))
REJECTED_PATTERN = re.compile(r'^\$([A-Z][A-Z])(GS[A-Z]|XDR|AMAID|AMCLK|AMSA|SGR|MMB|MDA)')

# Global variables for real-time NMEA data
last_nmea_data = []  # Buffer for latest NMEA data
max_nmea_buffer = 50  # Keep the last 50 lines

# Variables for rate limiting (avoid server flooding)
last_emit_time = 0
emit_counter = 0
emit_rate_limit = 1000  # Max 1000 messages per second (increased for maritime systems)

# === MARINETRAFFIC $AIVDO UDP FORWARDER ===
MARINETRAFFIC_IP = os.getenv("MARINETRAFFIC_IP", "127.0.0.1")
MARINETRAFFIC_PORT = int(os.getenv("MARINETRAFFIC_PORT", "12345"))
MARINETRAFFIC_ID = os.getenv("MARINETRAFFIC_ID", "")

def send_aivdo_to_marine_traffic(aivdo_sentence):
    """Send $AIVDO sentence to MarineTraffic server as required."""
    try:
        # MarineTraffic expects: <ID>$AIVDO....\r\n
        if not aivdo_sentence.startswith("$AIVDO"):
            return
        # Compose message: prepend ID, append CRLF
        msg = f"{MARINETRAFFIC_ID}{aivdo_sentence}\r\n"
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg.encode("ascii", errors="ignore"), (MARINETRAFFIC_IP, MARINETRAFFIC_PORT))
        sock.close()
        network_logger.info(f"Sent $AIVDO to MarineTraffic: {msg.strip()}")
    except Exception as e:
        error_logger.error(f"Failed to send $AIVDO to MarineTraffic: {e}")

# === NMEA DATA EMISSION FUNCTION ===
# Emit NMEA data via WebSocket and store it in buffer

def emit_nmea_data(source, message):
    """Emits NMEA data via WebSocket and stores it"""
    global last_nmea_data, last_emit_time, emit_counter
    
    try:
        # Rate limiting to avoid server flooding
        current_time = time.time()
        if current_time - last_emit_time >= 1.0:
            # Reset counter every second
            last_emit_time = current_time
            emit_counter = 0
        
        emit_counter += 1
        if emit_counter > emit_rate_limit:
            # Skip emission if rate limit exceeded
            debug_logger.debug(f"Rate limit exceeded, skipping {source}: {message[:30]}...")
            return
        
        # Input parameter validation
        if source is None or source == "":
            source = "UNKNOWN"
        if message is None or message == "":
            debug_logger.debug("Empty NMEA message - ignored")
            return
            
        # Clean the message
        message = str(message).strip()
        if not message or message == "undefined":
            debug_logger.debug(f"Invalid message ignored: '{message}'")
            return
        

        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}][{source}] {message}"

        # Add to buffer
        last_nmea_data.append(formatted_message)
        if len(last_nmea_data) > max_nmea_buffer:
            last_nmea_data.pop(0)

        # LOG NMEA to file instead of console
        # nmea_logger.info(f"{source}: {message}")

        # Forward $AIVDO sentences to MarineTraffic
        if message.startswith("$AIVDO"):
            send_aivdo_to_marine_traffic(message)

        # DEBUG only if enabled AND in verbose mode
        # if DEBUG:
        #     debug_logger.debug(f"EMIT {source}: {message[:50]}...")

        # Emit for Windy Plugin (pure NMEA string) - NON-BLOCKING with circuit breaker
        try:
            # Only emit if we have connected clients and circuit breaker allows it
            if connected_clients and socketio_circuit_breaker.can_emit():
                # Use threading with timeout to prevent hanging
                def emit_windy():
                    try:
                        # Remove timeout parameter that causes errors
                        socketio.emit('nmea_data', message)
                        socketio_circuit_breaker.record_success()
                    except Exception as emit_error:
                        socketio_circuit_breaker.record_failure()
                        # Log only in debug mode to prevent spam
                        if DEBUG:
                            debug_logger.debug(f"SocketIO emit error: {emit_error}")
                        pass  # Silent fail to prevent server freeze
                
                # Run emission in background thread with daemon=True and timeout
                import threading
                emit_thread = threading.Thread(target=emit_windy, daemon=True)
                emit_thread.start()
                # Don't wait for thread - let it run in background
            
        except Exception as windy_error:
            socketio_circuit_breaker.record_failure()
            # Only log errors in debug mode to prevent log spam
            if DEBUG:
                error_logger.error(f"Windy emission error: {windy_error}")

        # Emit for web interface with source information - NON-BLOCKING with circuit breaker
        try:
            # Only emit if we have connected clients and circuit breaker allows it
            if connected_clients and socketio_circuit_breaker.can_emit():
                web_data = {
                    'source': source,
                    'message': message,
                    'timestamp': datetime.datetime.now().strftime('%H:%M:%S')
                }
                
                def emit_web():
                    try:
                        socketio.emit('nmea_data_web', web_data)
                        socketio_circuit_breaker.record_success()
                    except Exception as web_emit_error:
                        socketio_circuit_breaker.record_failure()
                        if DEBUG:
                            debug_logger.debug(f"Web emit error: {web_emit_error}")
                        pass  # Silent fail to prevent server freeze
                
                # Run emission in background thread with daemon=True
                threading.Thread(target=emit_web, daemon=True).start()
        except Exception as ws_error:
            # Only log errors in debug mode to prevent log spam
            if DEBUG:
                error_logger.error(f"WebSocket emission error: {ws_error}")

    except Exception as e:
        error_logger.error(f"Error during NMEA emission: {e}")


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

# === ADVANCED LOG CONFIGURATION ===
# 🆕 COMPLETE SUPPRESSION of HTTP/SSL/gevent logs on ALL systems
import logging
import warnings
import datetime
import ipaddress
from logging.handlers import RotatingFileHandler

# Remove ALL HTTP logs (werkzeug/Flask)
logging.getLogger('werkzeug').setLevel(logging.CRITICAL + 1)
logging.getLogger('werkzeug.serving').setLevel(logging.CRITICAL + 1)
logging.getLogger('flask').setLevel(logging.ERROR)

# Remove ALL SSL and gevent logs
logging.getLogger('gevent').setLevel(logging.CRITICAL + 1)  # More than CRITICAL
logging.getLogger('gevent.ssl').setLevel(logging.CRITICAL + 1)
logging.getLogger('gevent.baseserver').setLevel(logging.CRITICAL + 1)
logging.getLogger('gevent.server').setLevel(logging.CRITICAL + 1)
logging.getLogger('gevent.pywsgi').setLevel(logging.CRITICAL + 1)
logging.getLogger('ssl').setLevel(logging.CRITICAL + 1)

# Remove Python SSL warnings
warnings.filterwarnings('ignore', category=Warning)
warnings.filterwarnings('ignore', message='.*SSL.*')
warnings.filterwarnings('ignore', message='.*certificate.*')

# 🆕 COMPLETE SUPPRESSION OF HTTP/WERKZEUG LOGS
# Completely disable Werkzeug and all HTTP logs
logging.getLogger('werkzeug').disabled = True
logging.getLogger('werkzeug.serving').disabled = True

# Redirection complète de stdout pour les logs HTTP gevent
import sys
class HTTPLogFilter:
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout if original_stdout is not None else sys.__stdout__
        
    def write(self, text):
        # Protection against stdout None
        if self.original_stdout is None:
            return
            
        # Filter HTTP logs (contain typical patterns)
        http_patterns = [
            'GET /', 'POST /', 'PUT /', 'DELETE /',
            'HTTP/1.1', 'socket.io', '127.0.0.1', 'localhost'
        ]
        
        # If text contains an HTTP pattern, ignore it
        if any(pattern in text for pattern in http_patterns):
            return
        
        # Otherwise, write to original stdout
        try:
            self.original_stdout.write(text)
        except (AttributeError, OSError):
            pass  # Ignore if stdout is not available
        
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

# Apply HTTP filter only on Windows where it's problematic
# And only if stdout is available
if IS_WINDOWS and sys.stdout is not None:
    sys.stdout = HTTPLogFilter(sys.stdout)
    # The message will be displayed later after main_logger definition

# Remove urllib3 warnings if available
try:
    import urllib3
    urllib3.disable_warnings()
    # Disable only warnings that exist in this version of urllib3
    if hasattr(urllib3.exceptions, 'InsecureRequestWarning'):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    if hasattr(urllib3.exceptions, 'SNIMissingWarning'):
        urllib3.disable_warnings(urllib3.exceptions.SNIMissingWarning)
    if hasattr(urllib3.exceptions, 'InsecurePlatformWarning'):
        urllib3.disable_warnings(urllib3.exceptions.InsecurePlatformWarning)
except ImportError:
    pass

# 🆕 STRUCTURED LOG SYSTEM BY FILES
os.makedirs("logs", exist_ok=True)

# Common formatter for all logs - WITHOUT special characters
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_formatter = logging.Formatter('[%(levelname)s] %(message)s')

# 🆕 LOGGER FOR NMEA FRAMES (replaces print EMIT-DEBUG)
nmea_logger = logging.getLogger("nmea_data")
nmea_logger.setLevel(logging.INFO)
nmea_handler = RotatingFileHandler("logs/nmea_data.log", maxBytes=2*1024*1024, backupCount=5, encoding='utf-8')
nmea_handler.setFormatter(file_formatter)
nmea_logger.addHandler(nmea_handler)

# 🆕 LOGGER FOR GENERAL DEBUG (replaces print DEBUG)
debug_logger = logging.getLogger("debug")
debug_logger.setLevel(logging.DEBUG)
debug_handler = RotatingFileHandler("logs/debug.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
debug_handler.setFormatter(file_formatter)
debug_logger.addHandler(debug_handler)

# 🆕 LOGGER FOR TCP/UDP CONNECTIONS (technical details)
network_logger = logging.getLogger("network")
network_logger.setLevel(logging.INFO)
network_handler = RotatingFileHandler("logs/network.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
network_handler.setFormatter(file_formatter)
network_logger.addHandler(network_handler)

# 🆕 LOGGER FOR SYSTEM ERRORS
error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
error_handler = RotatingFileHandler("logs/errors.log", maxBytes=1024*1024, backupCount=5, encoding='utf-8')
error_handler.setFormatter(file_formatter)
error_logger.addHandler(error_handler)

# 🆕 Main logger for important messages (console + file)
main_logger = logging.getLogger("main")
main_logger.setLevel(logging.INFO)

# File handler for main with UTF-8
main_file_handler = RotatingFileHandler("logs/main.log", maxBytes=1024*1024, backupCount=3, encoding='utf-8')
main_file_handler.setFormatter(file_formatter)
main_logger.addHandler(main_file_handler)

# Console handler for main (important messages only)
main_console_handler = logging.StreamHandler()
main_console_handler.setFormatter(console_formatter)
main_logger.addHandler(main_console_handler)

# 🆕 Display filter initialization messages
if IS_WINDOWS:
    main_logger.info("HTTP filter activated for Windows")

# 🆕 stderr redirection for SSL (preserved)
class SSLErrorFilter:
    """Filter to remove specific SSL errors"""
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr if original_stderr is not None else sys.__stderr__
        
    def write(self, text):
        # Protection against stderr None
        if self.original_stderr is None:
            return
            
        # 🆕 Extended list of SSL patterns to filter
        ssl_patterns = [
            'ssl:', 'sslv3_alert', 'certificate_unknown', 
            'gevent', 'greenlet', 'wrap_socket_and_handle',
            'handshake', '_ssl.c:', 'ssl.sslerror',
            'certificate_verify_failed', 'ssl handshake failed',
            'wsgiserver', 'baseserver', 'pywsgi'
        ]
        
        # Filter known SSL errors
        if any(keyword in text.lower() for keyword in ssl_patterns):
            return  # Completely ignore
        
        # Write everything else to original stderr
        try:
            self.original_stderr.write(text)
        except (AttributeError, OSError):
            pass  # Ignore if stderr is not available
        
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

# Apply SSL filter only on Windows where it's problematic
# And only if stderr is available
if IS_WINDOWS and sys.stderr is not None:
    sys.stderr = SSLErrorFilter(sys.stderr)

main_logger.info("Log system initialized")

# === FLASK SERVER ===
app = Flask(__name__)
# Configure SocketIO with better stability settings and timeouts to prevent hanging
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='gevent',
    ping_timeout=10,           # Detect dead clients faster
    ping_interval=5,           # Send ping every 5 seconds
    max_http_buffer_size=1e6,  # Limit buffer size to prevent memory issues
    engineio_logger=False,     # Disable EngineIO logs to prevent spam
    logger=False,              # Disable SocketIO logs to prevent spam
    allow_upgrades=True,       # Allow protocol upgrades
    transports=['websocket', 'polling'],  # Support both websocket and polling
    always_connect=False       # Don't automatically connect - let client decide
)
CORS(app)  # Allow all origins (wildcard origin *)

# === BLUETOOTH GPS MANAGER (initialized early to avoid reference errors) ===
# Global declaration - will be initialized after BluetoothGPSManager class
bluetooth_manager = None

# === SHUTDOWN MANAGEMENT ===
shutdown_event = threading.Event()
http_server = None

def signal_handler(signum, frame):
    """Handle shutdown signals (Ctrl+C, SIGTERM, etc.)"""
    main_logger.debug(f"\n[INFO] Signal {signum} received - shutting down gracefully...")
    shutdown_event.set()
    
    # Stop HTTP server
    global http_server
    if http_server:
        main_logger.info("Stopping HTTP server...")
        http_server.stop()
    
    # Stop all threads
    serial_stop.set()
    udp_stop.set()
    tcp_stop.set()
    bluetooth_monitor_stop.set()
    
    main_logger.info("Shutdown complete")
    sys.exit(0)

def cleanup_on_exit():
    """Cleanup function called on normal exit"""
    if not shutdown_event.is_set():
        shutdown_event.set()
        serial_stop.set()
        udp_stop.set()
        tcp_stop.set()
        bluetooth_monitor_stop.set()
        
        # Stop the new daemon threads to prevent hanging
        try:
            test_data_stop.set()
        except NameError:
            pass  # test_data_stop not defined yet
            
        try:
            cleanup_stop.set()
        except NameError:
            pass  # cleanup_stop not defined yet
            
        main_logger.info("Cleanup completed")

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
    Automatic Bluetooth GPS detection and connection.
    Uses the Bluetooth manager for automatic discovery and connection.
    Compatible with Windows, macOS, Linux.
    Returns the port name (e.g. /dev/rfcomm0 or COM4), or None.
    """
    global bluetooth_manager
    # On Linux, use automatic Bluetooth manager
    if IS_LINUX:
        debug_logger.debug("Using automatic Bluetooth manager...")
        auto_port = bluetooth_manager.maintain_connection()
        if auto_port:
            return auto_port
    
    # Fallback: traditional method by port enumeration
    debug_logger.debug("Scanning for serial ports...")
    ports = list(serial.tools.list_ports.comports())
    
    if not ports:
        debug_logger.debug("No serial ports detected")
        return None
    
    debug_logger.debug(f"{len(ports)} serial port(s) found: {[p.device for p in ports]}")
    
    # OS-adapted patterns
    if IS_WINDOWS:
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
                debug_logger.debug(f"Suitable serial port: {port_name} ({desc})")
                return port_name
    
    # If nothing found, return the first available port on Windows
    if IS_WINDOWS and ports:
        first_port = ports[0].device
        debug_logger.debug(f"No specific match, using first port: {first_port}")
        return first_port
    
    debug_logger.debug("No suitable serial port found")
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

# Stop events for daemon threads to prevent hanging
test_data_stop = threading.Event()
cleanup_stop = threading.Event()

# === NMEA DATA CLEANING FUNCTION ===
# This function cleans NMEA data by removing common repeater prefixes and unwanted characters.
# It is designed to handle various NMEA formats and ensure clean data for processing.
# It removes common repeater prefixes, cleans up double dollar signs, and strips control characters.
# It is used to ensure that only valid NMEA sentences are processed and emitted.
def clean_nmea_data(data):
    """Clean NMEA data from repeater prefixes"""
    import re
    
    # Remove common repeater prefixes
    data = re.sub(r'^\$[A-Z0-9]{2,6}\$', '$', data)
    
    # Clean double $
    data = re.sub(r'\$+', '$', data)
    
    # Remove control characters
    data = re.sub(r'[\r\n\x00-\x1F]', '', data)
    
    return data.strip()


# Function to listen to UDP broadcasts in server mode
# This function listens for UDP broadcasts on a specified port and emits the received NMEA data.
def udp_listener(stop_event):
# Force binding IP
    bind_ip = "0.0.0.0"  # Force for Windows
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((bind_ip, UDP_PORT))  # Use bind_ip instead of UDP_IP
        main_logger.info(f"[UDP] Listening on {bind_ip}:{UDP_PORT}")
        sock.settimeout(1.0)
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                data, addr = sock.recvfrom(1024)
                message = clean_nmea_data(data.decode('utf-8', errors='ignore'))
                if not REJECTED_PATTERN.match(message):
                    #nmea_logger.info(f"[UDP] {message}")
                    if message and message.strip():
                        emit_nmea_data("UDP", message.strip())
            except socket.timeout:
                continue
            except Exception as e:
                if not shutdown_event.is_set():
                    main_logger.info(f"[UDP] Error: {e}")
                break
                
    except Exception as e:
        main_logger.info(f"[UDP] Bind error on {bind_ip}:{UDP_PORT} - {e}")
        return
    finally:
        try:
            sock.close()
        except:
            pass
            
    main_logger.info("[UDP] Stopped.")

# Function to listen to UDP broadcasts in client mode
# This function listens for UDP broadcasts on a specified port and emits the received NMEA data.
# It is designed to handle incoming messages, filter out unwanted patterns, and emit valid NMEA data.
# It uses a stop event to allow graceful shutdown of the listener thread.

def udp_client_listener(target_ip, target_port, stop_event):
    """UDP listening in client/broadcast mode"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Configuration to receive broadcasts
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    # Bind on all interfaces to receive broadcasts
    sock.bind(('0.0.0.0', target_port))
    
    main_logger.info(f"[UDP-CLIENT] Listening for broadcasts on port {target_port}")
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
                main_logger.info(f"[UDP-CLIENT] Error: {e}")
            break
            
    sock.close()
    main_logger.info("[UDP-CLIENT] Stopped.")

def tcp_listener(stop_event):
    """TCP listening in server mode with structured logs"""
    global TCP_PORT
    
    bind_ip = "0.0.0.0"
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        sock.bind((bind_ip, TCP_PORT))
        sock.listen(1)
        main_logger.info(f"TCP server listening on port {TCP_PORT}")
        sock.settimeout(1.0)
        
        while not stop_event.is_set() and not shutdown_event.is_set():
            try:
                conn, addr = sock.accept()
                main_logger.info(f"TCP client connected: {addr[0]}")
                
                with conn:
                    conn.settimeout(1.0)
                    buffer = ""
                    
                    while not stop_event.is_set() and not shutdown_event.is_set():
                        try:
                            data = conn.recv(1024)
                            if not data:
                                debug_logger.debug(f"TCP client disconnected: {addr[0]}")
                                break
                            
                            # Detailed network LOG to file
                            raw_data = data.decode('utf-8', errors='ignore')
                            network_logger.debug(f"TCP received {len(data)} bytes from {addr}")
                            
                            buffer += raw_data
                            
                            # Process all complete lines in buffer
                            line_count = 0
                            while '\n' in buffer:
                                line, buffer = buffer.split('\n', 1)
                                line_count += 1
                                
                                message = clean_nmea_data(line)
                                
                                if message:
                                    pattern_match = REJECTED_PATTERN.match(message)
                                    
                                    if not pattern_match:
                                        # LOG only accepted frames
                                        debug_logger.debug(f"TCP message accepted: {message[:50]}...")
                                        emit_nmea_data("TCP", message.strip())
                                    else:
                                        debug_logger.debug(f"TCP message rejected by pattern: {message[:30]}...")
                            
                            # Protection against buffer too large
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
            
    main_logger.info("TCP server stopped")

def tcp_client(stop_event):
    """TCP connection in client mode with exponential backoff"""
    global TCP_TARGET_IP, TCP_TARGET_PORT
    
    debug_logger.debug(f"TCP client connecting to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
    
    consecutive_failures = 0
    max_backoff = 30  # Maximum 30 seconds backoff
    
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            
            # Enable keep-alive to detect dead connections
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if hasattr(socket, 'TCP_KEEPIDLE'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)  # Start after 60 seconds
            if hasattr(socket, 'TCP_KEEPINTVL'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)  # Interval 10 seconds
            if hasattr(socket, 'TCP_KEEPCNT'):
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)     # 3 failed attempts
            
            # Connection attempt
            sock.connect((TCP_TARGET_IP, TCP_TARGET_PORT))
            main_logger.info(f"TCP connected to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
            
            # Reset consecutive failures on successful connection
            consecutive_failures = 0
            
            # Connection monitoring variables
            last_data_time = time.time()
            connection_start = time.time()
            data_count = 0
            
            # Data reception loop
            buffer = ""
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    data = sock.recv(1024).decode('utf-8', errors='ignore')
                    if not data:
                        connection_duration = time.time() - connection_start
                        if data_count > 0:
                            debug_logger.info(f"TCP connection closed after {connection_duration:.1f}s, {data_count} messages received")
                        break
                    
                    last_data_time = time.time()
                    buffer += data
                    lines = buffer.split('\n')
                    buffer = lines[-1]  # Keep the last incomplete line
                    
                    for line in lines[:-1]:
                        message = line.strip()
                        if message and (message.startswith('$') or message.startswith('!')):
                            data_count += 1
                            emit_nmea_data("TCP", message)
                            
                except socket.timeout:
                    # Check for data silence (no data for over 30 seconds)
                    if time.time() - last_data_time > 30:
                        main_logger.warning(f"TCP data silence detected: {time.time() - last_data_time:.1f}s since last data")
                    continue
                except Exception as e:
                    error_logger.error(f"TCP receive error: {e}")
                    break
                    
        except socket.timeout:
            consecutive_failures += 1
            if consecutive_failures <= 3:  # Only log first few failures
                network_logger.warning(f"TCP connection timeout (attempt #{consecutive_failures})")
        except ConnectionRefusedError:
            consecutive_failures += 1
            if consecutive_failures <= 3:
                network_logger.warning(f"TCP connection refused (attempt #{consecutive_failures})")
        except Exception as e:
            consecutive_failures += 1
            error_logger.error(f"TCP client error: {e}")
        
        finally:
            try:
                sock.close()
            except:
                pass
        
        # Exponential backoff: start at 5 seconds, double each failure, max 30 seconds
        backoff_time = min(5 * (2 ** min(consecutive_failures - 1, 3)), max_backoff)
        if consecutive_failures <= 3:  # Only log retry messages for first few attempts
            debug_logger.debug(f"TCP client will retry in {backoff_time}s (attempt #{consecutive_failures})")
        
        for _ in range(int(backoff_time * 10)):  # backoff_time in 0.1s loops
            if stop_event.is_set():
                break
            time.sleep(0.1)

def tcp_client_listener(target_ip, target_port, stop_event):
    """TCP connection in client mode to a GPS"""
    main_logger.info(f"[TCP-CLIENT] Attempting connection to {target_ip}:{target_port}")
    
    retry_interval = 2  # Reconnection every 2 seconds (reduced to avoid prolonged disconnections)
    
    while not stop_event.is_set() and not shutdown_event.is_set():
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)  # Connection timeout
            
            # GPS connection
            sock.connect((target_ip, target_port))
            main_logger.info(f"[TCP-CLIENT] Connected to {target_ip}:{target_port}")
            
            sock.settimeout(1.0)  # Read timeout
            buffer = ""
            
            while not stop_event.is_set() and not shutdown_event.is_set():
                try:
                    data = sock.recv(1024)
                    if not data:
                        main_logger.info("[TCP-CLIENT] Connection closed by server")
                        break
                        
                    buffer += data.decode('utf-8', errors='ignore')
                    
                    # Process complete lines
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
                    main_logger.info(f"[TCP-CLIENT] Read error: {e}")
                    break
                    
        except socket.timeout:
            main_logger.info(f"[TCP-CLIENT] Connection timeout to {target_ip}:{target_port}")
        except ConnectionRefusedError:
            if DEBUG:
                main_logger.info(f"[TCP-CLIENT] Connection refused by {target_ip}:{target_port}")
        except Exception as e:
            main_logger.info(f"[TCP-CLIENT] Connection error: {e}")
        finally:
            if sock:
                sock.close()
        
        # Wait before retry
        main_logger.info(f"[TCP-CLIENT] Reconnection in {retry_interval} seconds...")
        for _ in range(retry_interval * 10):  # 2 seconds in 0.1s loops
            if stop_event.is_set():
                break
            time.sleep(0.1)
    
    main_logger.info("[TCP-CLIENT] Stopped.")


# Function to listen to the serial port and send NMEA data
# Uses a buffer to handle pending data and avoid frame loss
def serial_listener(port, baudrate, stop_event):
    main_logger.info(f"[SERIAL] Listener starting on {port} @ {baudrate} bps")
    
    # Check that the port exists
    if not port or port == "None":
        main_logger.info("[SERIAL] No serial port configured")
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
        
        main_logger.info(f"[SERIAL] Attempting to open port {port}...")
        with serial.Serial(**serial_kwargs) as ser:
            main_logger.info(f"[SERIAL] Port opened successfully: {port} @ {baudrate} bps")
            
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
                        main_logger.info("[SERIAL] Too many decoding errors, pausing...")
                        time.sleep(1)
                        consecutive_errors = 0
                    continue
                except Exception as e:
                    consecutive_errors += 1
                    if DEBUG:
                        main_logger.info(f"[SERIAL] Read error: {e}")
                    if consecutive_errors > 20:
                        main_logger.info("[SERIAL] Too many errors, stopping listener")
                        break
                    time.sleep(0.1)
                    continue
                    
    except serial.SerialException as e:
        main_logger.info(f"[ERROR][SERIAL] Cannot open port {port}: {e}")
        if IS_WINDOWS:
            main_logger.info("[INFO] Possible solutions:")
            main_logger.info("  1. Check that the COM port exists in Device Manager")
            main_logger.info("  2. Close any other program using this port")
            main_logger.info("  3. Reconnect your Bluetooth device")
            main_logger.info("  4. Try another serial port")
        else:
            main_logger.info("[INFO] Check serial port access permissions")
            main_logger.info("  sudo chmod 666 /dev/ttyUSB0  # or appropriate port")
    except Exception as e:
        main_logger.info(f"[ERROR][SERIAL] Unexpected error: {e}")
    
    main_logger.info("[SERIAL] Stopped.")

def bluetooth_monitor(stop_event):
    """
    Bluetooth monitoring thread that maintains GPS connection automatically
    """
    global bluetooth_manager, serial_thread
    main_logger.info("[BLUETOOTH-MONITOR] Starting Bluetooth monitoring...")
    
    # Ensure bluetooth_manager is initialized
    if bluetooth_manager is None:
        main_logger.info("[BLUETOOTH-MONITOR] Error: bluetooth_manager not initialized")
        return
    
    check_counter = 0
    while not stop_event.is_set() and not shutdown_event.is_set():
        try:
            if ENABLE_SERIAL and IS_LINUX:
                check_counter += 1
                
                # Periodic log to show monitoring is active
                if check_counter % 10 == 1:  # Every 10 cycles (10 minutes)
                    main_logger.info(f"[BLUETOOTH-MONITOR] Cycle {check_counter} - connection check...")
                
                # Check and maintain Bluetooth connection
                port = bluetooth_manager.maintain_connection()
                if port:
                    # Update global serial port if necessary
                    global SERIAL_PORT
                    current_port = SERIAL_PORT if SERIAL_PORT != "AUTO" else None
                    
                    # In AUTO mode, always check if serial thread is running
                    if SERIAL_PORT == "AUTO" or current_port != port:
                        main_logger.info(f"Bluetooth GPS connected: {port}")
                        
                        # Stop existing serial thread if there is one
                        if serial_thread and serial_thread.is_alive():
                            debug_logger.debug("Stopping existing serial thread...")
                            serial_stop.set()
                            serial_thread.join(timeout=2)
                        
                        # Wait a bit to ensure port is released
                        debug_logger.debug("Waiting for port release...")
                        time.sleep(5)
                        
                        # Start new serial thread
                        debug_logger.debug(f"Starting serial thread on {port}...")
                        serial_stop.clear()
                        serial_thread = threading.Thread(target=serial_listener, args=(port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                        serial_thread.start()
                        
                        # Update global variable for web interface (only if not in AUTO mode)
                        if SERIAL_PORT != "AUTO":
                            SERIAL_PORT = port
                    elif not (serial_thread and serial_thread.is_alive()):
                        # Port hasn't changed but serial thread is not active
                        debug_logger.debug(f"Restarting serial thread on {port}...")
                        serial_stop.clear()
                        serial_thread = threading.Thread(target=serial_listener, args=(port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                        serial_thread.start()
                elif SERIAL_PORT == "AUTO":
                    # In AUTO mode, stop serial thread if no connection
                    if serial_thread and serial_thread.is_alive():
                        debug_logger.debug("No GPS connection - stopping serial thread")
                        serial_stop.set()
                        serial_thread.join(timeout=2)
            
            # Wait 60 seconds before next check
            for _ in range(600):  # 60 seconds in 0.1s increments
                if stop_event.is_set():
                    break
                time.sleep(0.1)
                
        except Exception as e:
            main_logger.info(f"[BLUETOOTH-MONITOR] Error: {e}")
            time.sleep(10)  # Longer pause in case of error
    
    # Clean up rfcomm connection on exit
    if IS_LINUX:
        bluetooth_manager.cleanup_rfcomm()
    
    main_logger.info("[BLUETOOTH-MONITOR] Bluetooth monitoring stopped.")

# === THREAD MANAGEMENT FUNCTION ===
# Remplacer la fonction manage_threads() par cette version avec debug :

def manage_threads():
    global serial_thread, udp_thread, tcp_thread, bluetooth_monitor_thread
    
    debug_logger.info(f"Thread management - UDP:{ENABLE_UDP}, TCP:{ENABLE_TCP}, Serial:{ENABLE_SERIAL}")
    
    # UDP
    if ENABLE_UDP:
        if udp_thread is None or not udp_thread.is_alive():
            udp_stop.clear()
            
            # Choose function based on UDP mode
            if UDP_MODE == "server":
                debug_logger.debug(f"Starting UDP server thread on port {UDP_PORT}")
                udp_thread = threading.Thread(target=udp_listener, args=(udp_stop,), daemon=True)
            else:  # client mode
                debug_logger.debug(f"Starting UDP client thread to {UDP_TARGET_IP}:{UDP_TARGET_PORT}")
                udp_thread = threading.Thread(target=udp_client_listener, args=(UDP_TARGET_IP, UDP_TARGET_PORT, udp_stop), daemon=True)
            
            udp_thread.start()
            time.sleep(0.5)
            if udp_thread.is_alive():
                main_logger.info("UDP connection active")
            else:
                error_logger.error("UDP thread failed to start")
        else:
            debug_logger.debug("UDP thread already active")
    else:
        if udp_thread and udp_thread.is_alive():
            debug_logger.debug("Stopping UDP thread")
            udp_stop.set()
            udp_thread = None
            
    # TCP
    if ENABLE_TCP:
        if tcp_thread is None or not tcp_thread.is_alive():
            tcp_stop.clear()
            
            # Choose function based on TCP mode
            if TCP_MODE == "server":
                debug_logger.debug(f"Starting TCP server on port {TCP_PORT}")
                tcp_thread = threading.Thread(target=tcp_listener, args=(tcp_stop,), daemon=True)
            elif TCP_MODE == "client":  # explicit client mode
                debug_logger.debug(f"Starting TCP client to {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
                tcp_thread = threading.Thread(target=tcp_client, args=(tcp_stop,), daemon=True)
            else:
                error_logger.error(f"Invalid TCP_MODE: {TCP_MODE}, using client mode as fallback")
                tcp_thread = threading.Thread(target=tcp_client, args=(tcp_stop,), daemon=True)
            
            tcp_thread.start()
            time.sleep(0.5)
            if tcp_thread.is_alive():
                main_logger.info("TCP connection active")
            else:
                error_logger.error("TCP thread failed to start")
        else:
            debug_logger.debug("TCP thread already active")
    else:
        if tcp_thread and tcp_thread.is_alive():
            debug_logger.debug("Stopping TCP thread")
            tcp_stop.set()
            tcp_thread = None

    # SERIAL - only if not AUTO or if AUTO is resolved
    if ENABLE_SERIAL:
        actual_port = SERIAL_PORT
        
        if SERIAL_PORT == "AUTO":
            debug_logger.debug("AUTO mode - waiting for Bluetooth discovery...")
        else:
            if serial_thread is None or not serial_thread.is_alive():
                debug_logger.debug(f"Starting serial thread on {actual_port}")
                serial_stop.clear()
                serial_thread = threading.Thread(target=serial_listener, args=(actual_port, SERIAL_BAUDRATE, serial_stop), daemon=True)
                serial_thread.start()
                time.sleep(0.5)
                if serial_thread.is_alive():
                    main_logger.info("Serial connection active")
                else:
                    error_logger.error("Serial thread failed to start")
            else:
                debug_logger.debug("Serial thread already active")
    else:
        if serial_thread and serial_thread.is_alive():
            debug_logger.debug("Stopping serial thread")
            serial_stop.set()
            serial_thread = None
    
    # Thread status summary (only log active connections)
    active_connections = []
    if udp_thread and udp_thread.is_alive():
        active_connections.append("UDP")
    if tcp_thread and tcp_thread.is_alive():
        active_connections.append("TCP")
    if serial_thread and serial_thread.is_alive():
        active_connections.append("Serial")
    
    if active_connections:
        main_logger.info(f"Active connections: {', '.join(active_connections)}")
    else:
        main_logger.warning("No active connections")

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
        
        main_logger.info("[SSL] Generating self-signed SSL certificates...")
        
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
        
        main_logger.info("[SSL] SSL certificates created successfully")
        return True
        
    except ImportError:
        main_logger.info("[SSL] Cryptography module not available - no certificate generation")
        return False
    except Exception as e:
        main_logger.info(f"[SSL] Error during certificate creation: {e}")
        return False

def run_flask_app():
    global http_server
    
    # Service mode compatibility: log startup to file if no console
    if SERVICE_MODE:
        with open("logs/flask_startup.log", "a", encoding='utf-8') as log_file:
            log_file.write(f"[{datetime.datetime.now()}] Starting Flask server on port {HTTPS_PORT}\n")
    else:
        main_logger.info(f"Starting Flask server on port {HTTPS_PORT}")
    
    # Paths for certificates - compatible with PyInstaller
    cert_path = get_resource_path('cert.pem')
    key_path = get_resource_path('key.pem')
    
    debug_logger.debug(f"Looking for certificates:")
    debug_logger.debug(f"  cert.pem: {cert_path}")
    debug_logger.debug(f"  key.pem: {key_path}")
    
    # Create certificates if they don't exist on Windows
    if IS_WINDOWS and not (os.path.exists(cert_path) and os.path.exists(key_path)):
        main_logger.info("SSL certificates missing on Windows - attempting creation...")
        create_self_signed_cert()
    
    # Check certificate existence
    if os.path.exists(cert_path) and os.path.exists(key_path):
        main_logger.info("SSL certificates found - starting HTTPS")
        try:
            # 🆕 Create a silent logger for WSGIServer
            import sys
            
            # Temporarily redirect stdout to suppress HTTP logs
            class NullWriter:
                def write(self, text): pass
                def flush(self): pass
            
            # 🆕 WSGIServer configuration WITHOUT logs
            http_server = WSGIServer(
                ('0.0.0.0', HTTPS_PORT), 
                app, 
                keyfile=key_path, 
                certfile=cert_path,
                log=NullWriter(),  # Remove access logs
                error_log=NullWriter()  # Remove error logs
            )
            
            # 🚫 Ne PAS utiliser http_server.set_spawn() qui cause le TypeError

            main_logger.info(f"HTTPS server active on https://localhost:{HTTPS_PORT}")
            main_logger.info(f"Web interface: https://localhost:{HTTPS_PORT}/config.html")
            main_logger.info("Press Ctrl+C to stop the server")
            
            if IS_WINDOWS:
                main_logger.info(f"Alternative HTTP available on http://localhost:{HTTPS_PORT}")
            
            # 🆕 HTTPS server with simplified SSL handling - prevent hanging
            try:
                def run_https_server():
                    try:
                        http_server.serve_forever()
                    except Exception as https_error:
                        if not shutdown_event.is_set():
                            error_logger.error(f"HTTPS server error: {https_error}")
                
                # Start HTTPS server in background thread to prevent hanging
                import threading
                https_thread = threading.Thread(target=run_https_server, daemon=True)
                https_thread.start()
                main_logger.info("[HTTPS] Server thread started")
                
                # Keep main thread responsive
                try:
                    while not shutdown_event.is_set():
                        time.sleep(1)
                except KeyboardInterrupt:
                    main_logger.info("Keyboard interrupt received")
                    shutdown_event.set()
                    
            except KeyboardInterrupt:
                main_logger.info("Keyboard interrupt received")
                raise
            except Exception as e:
                # Filter ONLY repetitive SSL errors - let real errors through
                error_msg = str(e).lower()
                if any(ssl_keyword in error_msg for ssl_keyword in [
                    'sslv3_alert_certificate_unknown',
                    'certificate_unknown', 
                    'ssl handshake',
                    'wrap_socket_and_handle'
                ]):
                    # Silently ignore these cosmetic SSL errors
                    pass
                else:
                    # Report all other errors
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
            main_logger.info("HTTP mode - no SSL errors on Windows")
        main_logger.info("Press Ctrl+C to stop the server")
        
        # 🆕 Configuration to remove ALL HTTP logs
        import logging
        log = logging.getLogger('werkzeug')
        log.disabled = True
        
        # FIXED: Use threading to prevent blocking and hanging
        import threading
        
        def run_socketio_server():
            try:
                socketio.run(
                    app, 
                    host='0.0.0.0', 
                    port=HTTPS_PORT, 
                    debug=False,
                    allow_unsafe_werkzeug=True,
                    log_output=False  # Remove HTTP logs
                )
            except Exception as server_error:
                if not shutdown_event.is_set():
                    error_logger.error(f"SocketIO server error: {server_error}")
        
        # Start server in background thread
        server_thread = threading.Thread(target=run_socketio_server, daemon=True)
        server_thread.start()
        main_logger.info("[HTTP] SocketIO server thread started")
        
        # Keep main thread alive but responsive to shutdown
        try:
            while not shutdown_event.is_set():
                time.sleep(1)  # Check every second for shutdown
        except KeyboardInterrupt:
            main_logger.info("Keyboard interrupt received")
            shutdown_event.set()
            
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
                main_logger.info(f"[SSL-WARNING] {e}")
            else:
                raise e
    return wrapper

# Test function to be added temporarily
def test_ports_separately():
    """Test UDP and TCP port availability"""
    import socket
    
    debug_logger.debug("Testing network ports...")
    
    # Test UDP
    if ENABLE_UDP and UDP_MODE == "server":
        try:
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_sock.bind(('0.0.0.0', UDP_PORT))
            debug_logger.debug(f"UDP port {UDP_PORT} available")
            udp_sock.close()
        except Exception as e:
            main_logger.warning(f"UDP port {UDP_PORT} unavailable: {e}")
    
    # Test TCP
    if ENABLE_TCP and TCP_MODE == "server":
        try:
            tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_sock.bind(('0.0.0.0', TCP_PORT))
            tcp_sock.listen(1)
            debug_logger.debug(f"TCP port {TCP_PORT} available")
            tcp_sock.close()
        except Exception as e:
            main_logger.warning(f"TCP port {TCP_PORT} unavailable: {e}")
        main_logger.info(f"[TEST] ERROR TCP port {TCP_PORT} problem: {e}")

# Call this function in main_thread() before manage_threads()


def main_thread():
    global SERIAL_PORT, ENABLE_SERIAL, serial_thread
    
    # Service mode logging (only essential info)
    if SERVICE_MODE:
        with open("logs/main_startup.log", "a", encoding='utf-8') as log_file:
            log_file.write(f"\n[{datetime.datetime.now()}] NMEA SERVER STARTING (SERVICE MODE)\n")
            enabled_services = []
            if ENABLE_UDP:
                enabled_services.append(f"UDP({UDP_MODE})")
            if ENABLE_TCP:
                enabled_services.append(f"TCP({TCP_MODE})")
            if ENABLE_SERIAL:
                enabled_services.append(f"Serial({SERIAL_PORT})")
            log_file.write(f"[{datetime.datetime.now()}] Services: {', '.join(enabled_services) if enabled_services else 'None'}\n")
    
    # Startup summary
    enabled_services = []
    if ENABLE_UDP:
        service_info = f"UDP {UDP_MODE}"
        if UDP_MODE == "client":
            service_info += f" -> {UDP_TARGET_IP}:{UDP_TARGET_PORT}"
        else:
            service_info += f" port {UDP_PORT}"
        enabled_services.append(service_info)
    
    if ENABLE_TCP:
        service_info = f"TCP {TCP_MODE}"
        if TCP_MODE == "client":
            service_info += f" -> {TCP_TARGET_IP}:{TCP_TARGET_PORT}"
        else:
            service_info += f" port {TCP_PORT}"
        enabled_services.append(service_info)
    
    if ENABLE_SERIAL:
        enabled_services.append(f"Serial {SERIAL_PORT}")
    
    if enabled_services:
        main_logger.info(f"NMEA Services: {', '.join(enabled_services)}")
    else:
        main_logger.warning("No NMEA services enabled")
    
    if not SERVICE_MODE:
        main_logger.info("Press Ctrl+C to stop the server")
    
    # Auto-detection of serial port if necessary
    if ENABLE_SERIAL and (not SERIAL_PORT or SERIAL_PORT == "AUTO"):
        detected_port = detect_bluetooth_serial_port()
        if detected_port:
            SERIAL_PORT = detected_port
            main_logger.info(f"Serial port detected: {SERIAL_PORT}")
            
            # Start serial thread immediately if a port is detected
            if serial_thread is None or not serial_thread.is_alive():
                debug_logger.debug(f"Starting serial thread on port: {SERIAL_PORT}")
                serial_stop.clear()
                serial_thread = threading.Thread(target=serial_listener, args=(SERIAL_PORT, SERIAL_BAUDRATE, serial_stop), daemon=True)
                serial_thread.start()
        else:
            main_logger.warning("No serial port detected - serial disabled")
            ENABLE_SERIAL = False
    
    # Test ports separately if enabled
    test_ports_separately()

    # Start threads for UDP, TCP and Serial if enabled
    manage_threads()
    
    # Start daemon threads for test data and cleanup - AFTER main initialization
    main_logger.info("[INFO] Starting background daemon threads...")
    
    # Start test data generation thread
    test_thread = threading.Thread(target=test_data_thread, daemon=True)
    test_thread.start()
    main_logger.info("[INFO] Test data generation thread started")
    
    # Start cleanup thread  
    cleanup_thread_obj = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup_thread_obj.start()
    main_logger.info("[INFO] WebSocket cleanup thread started")
    
    # Small pause to let threads start
    time.sleep(0.5)

    try:
        # Launch Flask server
        main_logger.info(f"[INFO] Launching Flask server on port {HTTPS_PORT}")
        
        if SERVICE_MODE:
            # Service mode: run Flask in background and keep main thread alive
            with open("logs/main_startup.log", "a", encoding='utf-8') as log_file:
                log_file.write(f"[{datetime.datetime.now()}] Starting Flask server in service mode...\n")
            
            # Start Flask server in background thread
            flask_thread = threading.Thread(target=run_flask_app, daemon=True)
            flask_thread.start()
            
            # Service mode main loop - keep the process alive
            main_logger.info(f"[SERVICE] NMEA Server running in background (PID: {os.getpid()})")
            while not shutdown_event.is_set():
                time.sleep(5)  # Check every 5 seconds
                
                # Optional: Periodic health check logging
                if time.time() % 300 < 5:  # Every 5 minutes
                    with open("logs/service_health.log", "a", encoding='utf-8') as log_file:
                        log_file.write(f"[{datetime.datetime.now()}] Service alive - PID: {os.getpid()}\n")
        else:
            # Console mode: run Flask normally (blocking)
            run_flask_app()
            
    except KeyboardInterrupt:
        main_logger.info("\n[INFO] Shutdown initiated by user")
    except Exception as e:
        main_logger.info(f"[ERROR] Server error: {e}")
        if SERVICE_MODE:
            with open("logs/main_startup.log", "a", encoding='utf-8') as log_file:
                log_file.write(f"[{datetime.datetime.now()}] SERVER ERROR: {e}\n")
    finally:
        main_logger.info("[INFO] Server stopped.")
        if SERVICE_MODE:
            with open("logs/main_startup.log", "a", encoding='utf-8') as log_file:
                log_file.write(f"[{datetime.datetime.now()}] Server stopped.\n")


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
    Automatic manager for Bluetooth GPS with auto-discovery and connection
    """
    def __init__(self):
        self.target_mac = None  # Adresse MAC du GPS trouvé
        self.target_channel = None  # Canal SPP trouvé
        self.rfcomm_device = 0  # Numéro du device rfcomm (0 = /dev/rfcomm0)
        self.is_connected = False
        self.last_scan_time = 0
        self.scan_interval = 60  # Scan toutes les minutes
        self.connection_timeout = 10  # Connection timeout
        
    def run_command(self, cmd, timeout=10):
        """Exécute une commande shell avec timeout"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, 
                                  text=True, timeout=timeout)
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            main_logger.info(f"[BLUETOOTH] Commande timeout: {cmd}")
            return False, "", "Timeout"
        except Exception as e:
            main_logger.info(f"[BLUETOOTH] Command error: {e}")
            return False, "", str(e)
    
    def scan_bluetooth_devices(self):
        """Scan des appareils Bluetooth à proximité"""
        main_logger.info("[BLUETOOTH] Scan des appareils Bluetooth...")
        
        # Check that Bluetooth is available
        success, stdout, stderr = self.run_command("which hciconfig", 5)
        if not success:
            main_logger.info("[BLUETOOTH] hciconfig non trouvé - Bluetooth non supporté")
            return []
        
        # Check and enable Bluetooth
        success, stdout, stderr = self.run_command("hciconfig", 5)
        if not success:
            main_logger.info("[BLUETOOTH] Bluetooth non disponible")
            return []
        
        # Essayer d'activer l'interface Bluetooth
        success, stdout, stderr = self.run_command("sudo hciconfig hci0 up", 5)
        if not success:
            main_logger.info(f"[BLUETOOTH] Impossible d'activer Bluetooth: {stderr}")
            # Essayer sans sudo
            success, stdout, stderr = self.run_command("hciconfig hci0 up", 5)
            if not success:
                main_logger.info("[BLUETOOTH] Bluetooth non accessible - vérifiez les permissions")
                return []
        
        # Scan des appareils avec timeout plus long
        main_logger.info("[BLUETOOTH] Scan en cours... (peut prendre 10-15 secondes)")
        success, stdout, stderr = self.run_command("hcitool scan", 20)
        if not success:
            main_logger.info(f"[BLUETOOTH] Échec du scan: {stderr}")
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
                    main_logger.info(f"[BLUETOOTH] Trouvé: {mac} - {name}")
        
        main_logger.info(f"[BLUETOOTH] {len(devices)} appareil(s) détecté(s)")
        return devices
    
    def find_spp_channel(self, mac_address):
        """Trouve le canal SPP pour un appareil donné"""
        main_logger.info(f"[BLUETOOTH] Searching SPP channel for {mac_address}...")
        
        success, stdout, stderr = self.run_command(f"sdptool browse {mac_address}", 10)
        if not success:
            main_logger.info(f"[BLUETOOTH] Échec browse: {stderr}")
            return None
        
        # Chercher le canal SPP dans la sortie
        lines = stdout.split('\n')
        in_spp_service = False
        
        for i, line in enumerate(lines):
            if 'Serial Port' in line or 'SPP' in line:
                in_spp_service = True
                main_logger.info(f"[BLUETOOTH] Service Serial Port trouvé")
            elif in_spp_service and 'Channel:' in line:
                try:
                    channel = int(line.split('Channel:')[1].strip())
                    main_logger.info(f"[BLUETOOTH] Canal SPP trouvé: {channel}")
                    return channel
                except (ValueError, IndexError):
                    continue
            elif in_spp_service and line.strip() == "":
                in_spp_service = False
        
        main_logger.info("[BLUETOOTH] Aucun canal SPP trouvé")
        return None
    
    def setup_rfcomm(self, mac_address, channel):
        """Configure rfcomm connection"""
        main_logger.info(f"[BLUETOOTH] Configuration rfcomm{self.rfcomm_device} -> {mac_address}:{channel}")
        
        # Libérer d'abord le device rfcomm s'il existe
        self.cleanup_rfcomm()
        
        # Create new connection
        cmd = f"sudo rfcomm bind {self.rfcomm_device} {mac_address} {channel}"
        success, stdout, stderr = self.run_command(cmd, 10)
        
        if success:
            # Wait for device to be created and stabilized
            rfcomm_path = f"/dev/rfcomm{self.rfcomm_device}"
            for i in range(10):  # Wait up to 5 seconds
                if os.path.exists(rfcomm_path):
                    # Wait a bit more for stabilization
                    time.sleep(2)
                    main_logger.info(f"[BLUETOOTH] rfcomm configured: {rfcomm_path}")
                    return rfcomm_path
                time.sleep(0.5)
            
            main_logger.info(f"[BLUETOOTH] Device {rfcomm_path} not created after timeout")
            return None
        else:
            main_logger.info(f"[BLUETOOTH] rfcomm configuration failed: {stderr}")
            return None
    
    def cleanup_rfcomm(self):
        """Clean rfcomm connection"""
        cmd = f"sudo rfcomm release {self.rfcomm_device}"
        success, stdout, stderr = self.run_command(cmd, 5)
        if success:
            main_logger.info(f"[BLUETOOTH] rfcomm{self.rfcomm_device} libéré")
        
    def test_gps_connection(self, port_path):
        """Test si le port GPS fonctionne en lisant quelques trames"""
        main_logger.info(f"[BLUETOOTH] Testing GPS connection on {port_path}")
        
        # Wait a bit for device to be ready
        time.sleep(2)
        
        ser = None
        try:
            # Test rapide avec gestion explicite de la fermeture
            ser = serial.Serial(port_path, 4800, timeout=5)
            main_logger.info("[BLUETOOTH] Port ouvert, lecture des données...")
            
            # Test plus court - juste 10 secondes max
            for i in range(10):  # Max 10 attempts = 50 seconds
                try:
                    line = ser.readline().decode('ascii', errors='ignore').strip()
                    if line:
                        main_logger.info(f"[BLUETOOTH] Données reçues: {line[:80]}...")
                        # Check if it's a valid NMEA GPS frame
                        if (line.startswith('$GP') or line.startswith('$GN') or 
                            line.startswith('!AI') or line.startswith('$GL')):
                            main_logger.info(f"[BLUETOOTH] ✓ Trame NMEA GPS valide détectée")
                            # Fermer proprement le port et attendre
                            ser.close()
                            time.sleep(3)  # Attendre 3 secondes pour que le port soit libéré
                            return True
                        elif line.startswith('$'):
                            main_logger.info(f"[BLUETOOTH] Trame NMEA détectée (autre): {line[:50]}")
                            # Continuer à chercher des trames GPS spécifiques
                except Exception as e:
                    main_logger.info(f"[BLUETOOTH] Erreur lecture: {e}")
                    continue
            
            main_logger.info("[BLUETOOTH] Aucune trame NMEA GPS valide reçue")
            return False
            
        except Exception as e:
            main_logger.info(f"[BLUETOOTH] Erreur test connexion: {e}")
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
            main_logger.info("[BLUETOOTH] Auto-découverte disponible uniquement sur Linux")
            return None
            
        main_logger.info("[BLUETOOTH] === DÉCOUVERTE AUTOMATIQUE GPS ===")
        
        # Scan des appareils
        devices = self.scan_bluetooth_devices()
        if not devices:
            main_logger.info("[BLUETOOTH] Aucun appareil trouvé")
            return None
        
        # Tester chaque appareil pour GPS/SPP
        for mac, name in devices:
            main_logger.info(f"[BLUETOOTH] Test appareil: {name} ({mac})")
            
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
                main_logger.info(f"[BLUETOOTH] OK GPS trouve: {name} ({mac}) sur canal {channel}")
                self.target_mac = mac
                self.target_channel = channel
                self.is_connected = True
                return rfcomm_path
            else:
                main_logger.info(f"[BLUETOOTH] ERROR Pas de GPS: {name}")
                self.cleanup_rfcomm()
        
        main_logger.info("[BLUETOOTH] Aucun GPS Bluetooth trouvé")
        return None
    
    def detect_existing_rfcomm(self):
        """Détecte si un rfcomm est déjà configuré et fonctionnel"""
        main_logger.info("[BLUETOOTH] Vérification des connexions rfcomm existantes...")
        
        # Vérifier si /dev/rfcomm0 existe
        rfcomm_path = f"/dev/rfcomm{self.rfcomm_device}"
        if os.path.exists(rfcomm_path):
            main_logger.info(f"[BLUETOOTH] Device {rfcomm_path} trouve")
            
            # Tester si c'est un GPS fonctionnel
            if self.test_gps_connection(rfcomm_path):
                main_logger.info(f"[BLUETOOTH] OK GPS fonctionnel detecte sur {rfcomm_path}")
                self.is_connected = True
                return rfcomm_path
            else:
                main_logger.info(f"[BLUETOOTH] ERROR {rfcomm_path} ne repond pas comme un GPS")
        
        return None
    
    def check_connection_status(self):
        """Vérifie l'état de la connexion actuelle"""
        if not self.is_connected:
            return False
            
        rfcomm_path = f"/dev/rfcomm{self.rfcomm_device}"
        
        # Vérifier que le device existe
        if not os.path.exists(rfcomm_path):
            main_logger.info("[BLUETOOTH] Device rfcomm disparu")
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
            main_logger.info(f"[BLUETOOTH] Erreur vérification device: {e}")
            
        main_logger.info("[BLUETOOTH] Connexion GPS perdue")
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
                main_logger.info("[BLUETOOTH] Reconnexion nécessaire")
                self.cleanup_rfcomm()
                self.is_connected = False
        # Wait a bit before reconnecting
        time.sleep(5)
        
        # First check if there's an existing rfcomm connection
        existing_connection = self.detect_existing_rfcomm()
        if existing_connection:
            return existing_connection
        
        # Check if it's time to scan (only if not connected)
        if current_time - self.last_scan_time < self.scan_interval:
            return None
            
        self.last_scan_time = current_time
        main_logger.info("[BLUETOOTH] Automatic reconnection attempt...")
        
        # (Re)connection attempt
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
                                main_logger.info("Configuration file changed, reloading...")
                                self.callback()
                    time.sleep(1)  # Check every second
                except Exception as e:
                    error_logger.error(f"Config watcher error: {e}")
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
        main_logger.info("[CONFIG] Reloading configuration...")
        
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
        TCP_MODE = os.getenv("TCP_MODE", "client")  # Défaut client pour éviter conflits
        UDP_TARGET_IP = os.getenv("UDP_TARGET_IP", "")
        UDP_TARGET_PORT = int(os.getenv("UDP_TARGET_PORT", 50110))
        TCP_TARGET_IP = os.getenv("TCP_TARGET_IP", "")
        TCP_TARGET_PORT = int(os.getenv("TCP_TARGET_PORT", 50110))
        
        SERIAL_PORT = os.getenv("SERIAL_PORT", DEFAULT_SERIAL_PORT).strip()
        SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 4800))
        
        main_logger.info(f"[CONFIG] New configuration loaded:")
        main_logger.info(f"  - Serial: {ENABLE_SERIAL} (Port: {SERIAL_PORT})")
        main_logger.info(f"  - UDP: {ENABLE_UDP} (Port: {UDP_PORT})")
        main_logger.info(f"  - TCP: {ENABLE_TCP} (Port: {TCP_PORT})")
        
        # Restart connections
        manage_threads()
        
        main_logger.info("Configuration reloaded")
        
    except Exception as e:
        error_logger.error(f"Configuration reload error: {e}")


def get_current_status():
    """Returns current status of all connections"""
    global udp_thread, tcp_thread, serial_thread, bluetooth_manager
    
    # Safe thread verification
    try:
        udp_active = (udp_thread is not None and 
                     hasattr(udp_thread, 'is_alive') and 
                     udp_thread.is_alive() and 
                     ENABLE_UDP)
    except Exception as e:
        debug_logger.debug(f"UDP status check error: {e}")
        udp_active = False
    
    try:
        tcp_active = (tcp_thread is not None and 
                     hasattr(tcp_thread, 'is_alive') and 
                     tcp_thread.is_alive() and 
                     ENABLE_TCP)
    except Exception as e:
        debug_logger.debug(f"TCP status check error: {e}")
        tcp_active = False
    
    try:
        # Check serial/bluetooth status
        serial_connected = False
        if ENABLE_SERIAL:
            if serial_thread is not None and hasattr(serial_thread, 'is_alive') and serial_thread.is_alive():
                serial_connected = True
            elif IS_LINUX and bluetooth_manager is not None:
                try:
                    serial_connected = bluetooth_manager.check_connection_status()
                except Exception as bt_error:
                    debug_logger.debug(f"Bluetooth check error: {bt_error}")
                    serial_connected = False
    except Exception as e:
        debug_logger.debug(f"Serial status check error: {e}")
        serial_connected = False
    
    # Count active connections
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
        main_logger.info(f"[STATUS] Final status - UDP: {udp_active}, TCP: {tcp_active}, Serial: {serial_connected}")
    
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

        # Gestion des modes UDP et TCP (préserver les valeurs actuelles si non spécifiées)
        UDP_MODE = request.form.get('udp_mode', UDP_MODE)  # Utiliser la valeur actuelle comme défaut
        TCP_MODE = request.form.get('tcp_mode', TCP_MODE)  # Utiliser la valeur actuelle comme défaut
        
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
        
        main_logger.info(f"[API] Configuration updated:")
        if UDP_MODE == 'server':
            main_logger.info(f"  - UDP Serveur: {ENABLE_UDP} ({UDP_IP}:{UDP_PORT})")
        else:
            main_logger.info(f"  - UDP Client: {ENABLE_UDP} -> {UDP_TARGET_IP}:{UDP_TARGET_PORT}")
        
        if TCP_MODE == 'server':
            main_logger.info(f"  - TCP Serveur: {ENABLE_TCP} ({TCP_IP}:{TCP_PORT})")
        else:
            main_logger.info(f"  - TCP Client: {ENABLE_TCP} -> {TCP_TARGET_IP}:{TCP_TARGET_PORT}")
        
        main_logger.info(f"  - Serial: {ENABLE_SERIAL} ({SERIAL_PORT})")
        
        # Restart threads with new configuration
        manage_threads()
        
        return jsonify({
            'success': True, 
            'message': 'Configuration updated and applied successfully'
        })
        
    except Exception as e:
        main_logger.info(f"[API] Error updating config: {e}")
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
            main_logger.info(f"[API-STATUS] Retour: {status}")
            
        return jsonify(status)
    except Exception as e:
        main_logger.info(f"[API-STATUS] Erreur: {e}")
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

# WebSocket connection tracking to prevent emissions to dead connections
connected_clients = set()

# Circuit breaker for SocketIO emissions to prevent server hanging
class SocketIOCircuitBreaker:
    def __init__(self, failure_threshold=50, timeout=60):  # More lenient settings
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = 0
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
        self.last_success_time = time.time()
    
    def can_emit(self):
        # Reset circuit breaker if we haven't had failures for a while
        if self.state == 'OPEN' and time.time() - self.last_success_time > 300:  # Reset after 5 minutes of no activity
            self.reset()
        
        if self.state == 'CLOSED':
            return True
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'HALF_OPEN'
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        self.failure_count = 0
        self.state = 'CLOSED'
        self.last_success_time = time.time()
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            main_logger.warning(f"[CIRCUIT-BREAKER] SocketIO emissions disabled due to {self.failure_count} failures")
    
    def reset(self):
        """Reset the circuit breaker"""
        self.failure_count = 0
        self.state = 'CLOSED'
        self.last_success_time = time.time()
        main_logger.info("[CIRCUIT-BREAKER] Circuit breaker reset")

# Global circuit breaker instance
socketio_circuit_breaker = SocketIOCircuitBreaker()

# Periodic cleanup of dead connections
def cleanup_dead_connections():
    """Clean up tracking of dead WebSocket connections"""
    global connected_clients  # Fix variable scope issue
    try:
        if connected_clients:
            # Try to ping all clients and remove dead ones
            dead_clients = set()
            for client_id in connected_clients.copy():
                try:
                    # Quick check - if this fails, client is likely dead - remove timeout parameter
                    socketio.emit('ping', room=client_id)
                except:
                    dead_clients.add(client_id)
            
            if dead_clients:
                connected_clients -= dead_clients
                main_logger.info(f"[CLEANUP] Removed {len(dead_clients)} dead WebSocket connections")
    except Exception as e:
        if DEBUG:
            debug_logger.debug(f"[CLEANUP] Error cleaning connections: {e}")

# Cleanup thread - NON-RECURSIVE (uses globally declared cleanup_stop event)
def cleanup_thread():
    """Background thread for cleaning dead connections - prevents hanging"""
    while not cleanup_stop.is_set() and not shutdown_event.is_set():
        try:
            cleanup_dead_connections()
        except Exception as e:
            if DEBUG:
                debug_logger.debug(f"Cleanup error: {e}")
        
        # Use event.wait() instead of sleep for better shutdown response
        cleanup_stop.wait(60.0)  # Wait 60 seconds or until stop event

# Cleanup thread will be started in main_thread() function

# Test NMEA data generator for WebSocket testing
def generate_test_nmea_data():
    """Generate test NMEA data when no real data source is available"""
    global connected_clients  # Fix variable scope issue
    if not connected_clients:
        return  # No clients connected, don't generate data
    
    # Only generate test data if no real data sources are active
    if not (ENABLE_TCP and tcp_thread and tcp_thread.is_alive()) and not (ENABLE_UDP and udp_thread and udp_thread.is_alive()) and not (ENABLE_SERIAL and serial_thread and serial_thread.is_alive()):
        # Generate a test GPS position (moving around France)
        import random, math
        lat_base = 48.8566  # Paris latitude
        lon_base = 2.3522   # Paris longitude
        
        # Add some variation
        lat_offset = random.uniform(-0.1, 0.1)
        lon_offset = random.uniform(-0.1, 0.1)
        
        lat = lat_base + lat_offset
        lon = lon_base + lon_offset
        
        # Convert to NMEA format
        lat_deg = int(lat)
        lat_min = (lat - lat_deg) * 60
        lat_str = f"{lat_deg:02d}{lat_min:06.3f}"
        lat_dir = 'N' if lat >= 0 else 'S'
        
        lon_deg = int(abs(lon))
        lon_min = (abs(lon) - lon_deg) * 60
        lon_str = f"{lon_deg:03d}{lon_min:06.3f}"
        lon_dir = 'E' if lon >= 0 else 'W'
        
        # Generate test GPGGA sentence
        test_sentence = f"$GPGGA,120000.00,{lat_str},{lat_dir},{lon_str},{lon_dir},1,08,1.0,50.0,M,45.0,M,,*65"
        
        # Emit test data
        emit_nmea_data("TEST", test_sentence)
        
        if DEBUG:
            main_logger.info(f"[TEST-DATA] Generated: {test_sentence}")

# Test data generation thread - NON-RECURSIVE
test_data_stop = threading.Event()

def test_data_thread():
    """Background thread for generating test data - prevents hanging"""
    while not test_data_stop.is_set() and not shutdown_event.is_set():
        try:
            generate_test_nmea_data()
        except Exception as e:
            if DEBUG:
                debug_logger.debug(f"Test data generation error: {e}")
        
        # Use event.wait() instead of sleep for better shutdown response
        test_data_stop.wait(5.0)  # Wait 5 seconds or until stop event

# Test data and cleanup threads will be started in main_thread() function

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    """Gérer les nouvelles connexions WebSocket avec tracking"""
    global connected_clients  # Fix variable scope issue
    try:
        connected_clients.add(request.sid)
        main_logger.info(f"[WEBSOCKET] Client connecté: {request.sid} (total: {len(connected_clients)})")
        
        # Reset circuit breaker when new clients connect
        if socketio_circuit_breaker.state == 'OPEN':
            socketio_circuit_breaker.reset()
            main_logger.info("[WEBSOCKET] Circuit breaker reset due to new client connection")
        
        # Envoyer les dernières données NMEA au client qui se connecte - avec timeout
        try:
            for formatted_data in last_nmea_data[-10:]:  # Les 10 dernières
                # Extraire la trame NMEA pure du message formaté
                if '] ' in formatted_data:
                    # Format: [timestamp][source] message
                    nmea_message = formatted_data.split('] ', 2)[-1] if '] ' in formatted_data else formatted_data
                else:
                    nmea_message = formatted_data
                
                # Envoyer la trame NMEA pure pour le plugin Windy - remove timeout parameter
                socketio.emit('nmea_data', nmea_message, room=request.sid)
        except Exception as history_error:
            if DEBUG:
                debug_logger.debug(f"Error sending history to {request.sid}: {history_error}")
    except Exception as e:
        error_logger.error(f"[WEBSOCKET] Error handling connect: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Gérer les déconnexions WebSocket avec cleanup"""
    global connected_clients  # Fix variable scope issue
    try:
        connected_clients.discard(request.sid)  # Remove from tracking set
        main_logger.info(f"[WEBSOCKET] Client déconnecté: {request.sid} (remaining: {len(connected_clients)})")
    except Exception as e:
        if DEBUG:
            debug_logger.debug(f"[WEBSOCKET] Error handling disconnect: {e}")

@socketio.on('request_status')
def handle_request_status():
    """Gérer les demandes de statut via WebSocket - remove timeout parameter"""
    try:
        status = get_current_status()
        emit('status_update', status)
        
        if DEBUG:
            main_logger.info(f"[WEBSOCKET] Status envoyé: {status}")
            
    except Exception as e:
        if DEBUG:
            main_logger.info(f"[WEBSOCKET] Erreur envoi status: {e}")
        try:
            emit('status_update', {
                'udp_active': False,
                'tcp_active': False,
                'serial_connected': False,
                'connections_active': 0,
                'error': str(e)
            })
        except:
            pass  # Silent fail if emit fails

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
        main_logger.info("[MAIN] Starting NMEA Server...")
        main_thread()  # Utiliser la fonction main_thread() existante
    except KeyboardInterrupt:
        main_logger.info("[MAIN] Received interrupt signal")
    finally:
        main_logger.info("[MAIN] Stopping config watcher...")
        config_watcher.stop()
        bluetooth_manager.cleanup_rfcomm()
