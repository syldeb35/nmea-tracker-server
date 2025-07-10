#!/usr/bin/env micropython
# -*- coding: utf-8 -*-
"""
NMEA Tracker Server - ESP32 MicroPython Version
===============================================

Portable NMEA/AIS data receiver and web interface for ESP32
- Receives NMEA data via Serial/Bluetooth
- Serves web interface via WiFi AP or STA mode
- Real-time data streaming via WebSockets
- NMEA sentence parsing and filtering

Hardware Requirements:
- ESP32 DevKit or similar
- GPS/AIS device with NMEA output
- Optional: External antenna for better WiFi range

Author: Converted from Python desktop version
License: MIT
"""

import network
import socket
import time
import gc
import json
import re
from machine import UART, Pin, reset
import _thread
import ubinascii
import hashlib

# === CONFIGURATION ===
class Config:
    # WiFi Configuration
    WIFI_SSID = "NMEA_Tracker_ESP32"
    WIFI_PASSWORD = "nmea123456"
    WIFI_MODE = "AP"  # "AP" for Access Point, "STA" for Station
    
    # When using STA mode, configure these:
    STA_SSID = "YourWiFiNetwork"
    STA_PASSWORD = "YourWiFiPassword"
    
    # Network
    HTTP_PORT = 80
    WEBSOCKET_PORT = 81
    
    # Serial/UART Configuration
    UART_NUM = 2  # UART2 on ESP32
    UART_TX = 17  # GPIO17
    UART_RX = 16  # GPIO16
    UART_BAUDRATE = 4800
    
    # NMEA Filtering
    NMEA_SENTENCES = ['GGA', 'RMC', 'GLL', 'VTG', 'HDT']
    
    # Status LED
    LED_PIN = 2  # Built-in LED on most ESP32 boards

# === GLOBAL VARIABLES ===
led = Pin(Config.LED_PIN, Pin.OUT)
uart = None
wifi = None
clients = []
nmea_data = {
    'latitude': 0.0,
    'longitude': 0.0,
    'speed': 0.0,
    'heading': 0.0,
    'timestamp': '',
    'fix_quality': 0,
    'satellites': 0,
    'last_sentence': ''
}

# === NMEA PARSER ===
class NMEAParser:
    def __init__(self):
        self.gga_pattern = re.compile(r'^\$..GGA,([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),\*([A-F0-9]{2})')
        self.rmc_pattern = re.compile(r'^\$..RMC,([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),\*([A-F0-9]{2})')
    
    def parse_coordinate(self, coord_str, direction):
        """Convert NMEA coordinate to decimal degrees"""
        if not coord_str or not direction:
            return 0.0
        
        try:
            # Format: DDMM.MMMM or DDDMM.MMMM
            if len(coord_str) >= 7:
                if '.' in coord_str:
                    dot_pos = coord_str.index('.')
                    degrees = float(coord_str[:dot_pos-2])
                    minutes = float(coord_str[dot_pos-2:])
                    decimal = degrees + (minutes / 60.0)
                    
                    if direction in ['S', 'W']:
                        decimal = -decimal
                    return decimal
        except:
            pass
        return 0.0
    
    def parse_gga(self, sentence):
        """Parse GGA sentence (GPS Fix Data)"""
        match = self.gga_pattern.match(sentence)
        if match:
            groups = match.groups()
            try:
                lat = self.parse_coordinate(groups[1], groups[2])
                lon = self.parse_coordinate(groups[3], groups[4])
                
                return {
                    'type': 'GGA',
                    'timestamp': groups[0],
                    'latitude': lat,
                    'longitude': lon,
                    'fix_quality': int(groups[5]) if groups[5] else 0,
                    'satellites': int(groups[6]) if groups[6] else 0,
                    'hdop': float(groups[7]) if groups[7] else 0.0,
                    'altitude': float(groups[8]) if groups[8] else 0.0
                }
            except:
                pass
        return None
    
    def parse_rmc(self, sentence):
        """Parse RMC sentence (Recommended Minimum)"""
        match = self.rmc_pattern.match(sentence)
        if match:
            groups = match.groups()
            try:
                lat = self.parse_coordinate(groups[2], groups[3])
                lon = self.parse_coordinate(groups[4], groups[5])
                
                return {
                    'type': 'RMC',
                    'timestamp': groups[0],
                    'status': groups[1],
                    'latitude': lat,
                    'longitude': lon,
                    'speed': float(groups[6]) if groups[6] else 0.0,
                    'course': float(groups[7]) if groups[7] else 0.0,
                    'date': groups[8]
                }
            except:
                pass
        return None
    
    def parse_sentence(self, sentence):
        """Parse any supported NMEA sentence"""
        sentence = sentence.strip()
        if not sentence.startswith('$'):
            return None
        
        # Check sentence type
        if 'GGA' in sentence:
            return self.parse_gga(sentence)
        elif 'RMC' in sentence:
            return self.parse_rmc(sentence)
        
        return None

# === WiFi MANAGEMENT ===
def setup_wifi():
    global wifi
    
    if Config.WIFI_MODE == "AP":
        # Access Point Mode
        wifi = network.WLAN(network.AP_IF)
        wifi.active(True)
        wifi.config(essid=Config.WIFI_SSID, password=Config.WIFI_PASSWORD)
        print(f"[WiFi] AP Mode: {Config.WIFI_SSID}")
        print(f"[WiFi] IP: {wifi.ifconfig()[0]}")
        return wifi.ifconfig()[0]
    
    else:
        # Station Mode
        wifi = network.WLAN(network.STA_IF)
        wifi.active(True)
        wifi.connect(Config.STA_SSID, Config.STA_PASSWORD)
        
        # Wait for connection
        timeout = 10
        while not wifi.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1
            led.value(not led.value())  # Blink while connecting
        
        if wifi.isconnected():
            ip = wifi.ifconfig()[0]
            print(f"[WiFi] Connected to {Config.STA_SSID}")
            print(f"[WiFi] IP: {ip}")
            led.value(1)  # Solid on when connected
            return ip
        else:
            print("[WiFi] Connection failed!")
            return None

# === SERIAL/UART HANDLER ===
def setup_uart():
    global uart
    try:
        uart = UART(Config.UART_NUM, 
                   baudrate=Config.UART_BAUDRATE,
                   tx=Config.UART_TX, 
                   rx=Config.UART_RX,
                   timeout=1000)
        print(f"[UART] Initialized on pins TX:{Config.UART_TX}, RX:{Config.UART_RX}")
        return True
    except Exception as e:
        print(f"[UART] Error: {e}")
        return False

def uart_reader_thread():
    """Thread to read NMEA data from UART"""
    global nmea_data
    parser = NMEAParser()
    buffer = ""
    
    print("[UART] Reader thread started")
    
    while True:
        try:
            if uart and uart.any():
                data = uart.read()
                if data:
                    buffer += data.decode('utf-8', 'ignore')
                    
                    # Process complete lines
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line.startswith('$'):
                            # Parse NMEA sentence
                            parsed = parser.parse_sentence(line)
                            if parsed:
                                update_nmea_data(parsed)
                                send_to_websocket_clients({
                                    'type': 'nmea',
                                    'data': parsed,
                                    'raw': line
                                })
                            
                            nmea_data['last_sentence'] = line
                            led.value(not led.value())  # Blink on data
            
            time.sleep(0.1)
        except Exception as e:
            print(f"[UART] Reader error: {e}")
            time.sleep(1)

def update_nmea_data(parsed):
    """Update global NMEA data with parsed sentence"""
    global nmea_data
    
    if parsed['type'] == 'GGA':
        nmea_data['latitude'] = parsed['latitude']
        nmea_data['longitude'] = parsed['longitude']
        nmea_data['fix_quality'] = parsed['fix_quality']
        nmea_data['satellites'] = parsed['satellites']
        nmea_data['timestamp'] = parsed['timestamp']
    
    elif parsed['type'] == 'RMC':
        nmea_data['latitude'] = parsed['latitude']
        nmea_data['longitude'] = parsed['longitude']
        nmea_data['speed'] = parsed['speed']
        nmea_data['heading'] = parsed['course']
        nmea_data['timestamp'] = parsed['timestamp']

def send_to_websocket_clients(message):
    """Send message to all connected WebSocket clients"""
    global clients
    if clients:
        try:
            json_msg = json.dumps(message)
            # Add frame for WebSocket protocol
            frame = create_websocket_frame(json_msg)
            disconnected = []
            
            for client in clients:
                try:
                    client.send(frame)
                except:
                    disconnected.append(client)
            
            # Remove disconnected clients
            for client in disconnected:
                clients.remove(client)
                print(f"[WebSocket] Client disconnected")
        except Exception as e:
            print(f"[WebSocket] Send error: {e}")

def create_websocket_frame(data):
    """Create a WebSocket frame for sending data"""
    data_bytes = data.encode('utf-8')
    data_length = len(data_bytes)
    
    if data_length < 126:
        frame = bytes([0x81, data_length]) + data_bytes
    elif data_length < 65536:
        frame = bytes([0x81, 126]) + data_length.to_bytes(2, 'big') + data_bytes
    else:
        frame = bytes([0x81, 127]) + data_length.to_bytes(8, 'big') + data_bytes
    
    return frame

# === WEB SERVER ===
def get_html_page():
    """Generate the enhanced HTML page for base station"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>NMEA Base Station ESP32</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --accent-blue: #3b82f6;
            --accent-green: #10b981;
            --accent-orange: #f59e0b;
            --accent-red: #ef4444;
            --border-color: #475569;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: var(--bg-card);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }

        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-green));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header .subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 768px) {
            .container {
                grid-template-columns: 1fr;
            }
        }

        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }

        .panel h3 {
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.3rem;
        }

        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }

        .status-indicator.online {
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
        }

        .status-indicator.offline {
            background: var(--accent-red);
        }

        .data-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        .data-item {
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .data-label {
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 5px;
        }

        .data-value {
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--accent-green);
        }

        .data-value.warning {
            color: var(--accent-orange);
        }

        .data-value.error {
            color: var(--accent-red);
        }

        #map {
            height: 300px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }

        .full-width {
            grid-column: 1 / -1;
        }

        #console {
            background: #0a0a0a;
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            height: 250px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            white-space: pre-wrap;
        }

        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s;
        }

        .btn-primary {
            background: var(--accent-blue);
            color: white;
        }

        .btn-success {
            background: var(--accent-green);
            color: white;
        }

        .btn-warning {
            background: var(--accent-orange);
            color: white;
        }

        .btn:hover {
            transform: translateY(-2px);
            filter: brightness(1.1);
        }

        .stats-row {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }

        .stat-card {
            flex: 1;
            background: var(--bg-secondary);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid var(--border-color);
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: var(--accent-blue);
        }

        .stat-label {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛰️ NMEA Base Station ESP32</h1>
        <p class="subtitle">Real-time NMEA/AIS Data Collection & Monitoring</p>
        <div style="margin-top: 15px;">
            <span class="status-indicator" id="connection-indicator"></span>
            <span id="connection-text">Connecting...</span>
        </div>
    </div>

    <div class="container">
        <!-- Position & Navigation Panel -->
        <div class="panel">
            <h3>📍 Position & Navigation</h3>
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-label">Latitude</div>
                    <div class="data-value" id="latitude">--°</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Longitude</div>
                    <div class="data-value" id="longitude">--°</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Speed (SOG)</div>
                    <div class="data-value" id="speed">-- kts</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Course (COG)</div>
                    <div class="data-value" id="heading">--°</div>
                </div>
            </div>
        </div>

        <!-- GPS Status Panel -->
        <div class="panel">
            <h3>🛰️ GPS Status</h3>
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-label">Fix Quality</div>
                    <div class="data-value" id="fix-quality">--</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Satellites</div>
                    <div class="data-value" id="satellites">--</div>
                </div>
                <div class="data-item">
                    <div class="data-label">HDOP</div>
                    <div class="data-value" id="hdop">--</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Last Update</div>
                    <div class="data-value" id="last-update">--</div>
                </div>
            </div>
        </div>

        <!-- Interactive Map -->
        <div class="panel full-width">
            <h3>🗺️ Position Map</h3>
            <div id="map"></div>
        </div>

        <!-- System Statistics -->
        <div class="panel">
            <h3>📊 System Statistics</h3>
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-number" id="total-sentences">0</div>
                    <div class="stat-label">Total Sentences</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="sentences-per-minute">0</div>
                    <div class="stat-label">Sentences/min</div>
                </div>
            </div>
            <div class="stats-row">
                <div class="stat-card">
                    <div class="stat-number" id="connected-clients">0</div>
                    <div class="stat-label">Connected Clients</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="uptime">0</div>
                    <div class="stat-label">Uptime (min)</div>
                </div>
            </div>
        </div>

        <!-- Console Output -->
        <div class="panel">
            <h3>💻 NMEA Console</h3>
            <div class="controls">
                <button class="btn btn-primary" onclick="clearConsole()">Clear</button>
                <button class="btn btn-success" onclick="togglePause()">
                    <span id="pause-text">Pause</span>
                </button>
                <button class="btn btn-warning" onclick="exportData()">Export</button>
            </div>
            <div id="console">Waiting for NMEA data...</div>
        </div>
    </div>

    <script>
        // Global variables
        let map, marker, trackPoints = [];
        let ws, isPaused = false;
        let totalSentences = 0, startTime = Date.now();
        let sentenceBuffer = [];

        // Initialize map
        function initMap() {
            map = L.map('map').setView([48.8566, 2.3522], 10); // Default to Paris
            
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }).addTo(map);
            
            marker = L.marker([0, 0]).addTo(map);
        }

        // WebSocket connection
        function connectWebSocket() {
            ws = new WebSocket('ws://' + window.location.hostname + ':81');
            
            ws.onopen = function() {
                updateConnectionStatus(true);
            };
            
            ws.onclose = function() {
                updateConnectionStatus(false);
                // Attempt reconnection
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                
                if (message.type === 'nmea') {
                    updateDisplay(message.data);
                    updateConsole(message.raw);
                    updateStatistics();
                }
            };
        }

        function updateConnectionStatus(connected) {
            const indicator = document.getElementById('connection-indicator');
            const text = document.getElementById('connection-text');
            
            if (connected) {
                indicator.className = 'status-indicator online pulse';
                text.textContent = 'Connected';
                text.style.color = 'var(--accent-green)';
            } else {
                indicator.className = 'status-indicator offline';
                text.textContent = 'Disconnected';
                text.style.color = 'var(--accent-red)';
            }
        }

        function updateDisplay(data) {
            if (data.latitude !== undefined && data.longitude !== undefined) {
                document.getElementById('latitude').textContent = data.latitude.toFixed(6) + '°';
                document.getElementById('longitude').textContent = data.longitude.toFixed(6) + '°';
                
                // Update map
                if (data.latitude !== 0 && data.longitude !== 0) {
                    const latlng = [data.latitude, data.longitude];
                    marker.setLatLng(latlng);
                    map.setView(latlng, 15);
                    
                    // Add to track
                    trackPoints.push(latlng);
                    if (trackPoints.length > 100) trackPoints.shift(); // Limit track points
                }
            }
            
            if (data.speed !== undefined) {
                document.getElementById('speed').textContent = data.speed.toFixed(1) + ' kts';
            }
            
            if (data.course !== undefined) {
                document.getElementById('heading').textContent = data.course.toFixed(1) + '°';
            }
            
            if (data.fix_quality !== undefined) {
                const fixElement = document.getElementById('fix-quality');
                fixElement.textContent = data.fix_quality;
                
                // Color coding for fix quality
                if (data.fix_quality >= 2) {
                    fixElement.className = 'data-value';
                } else if (data.fix_quality === 1) {
                    fixElement.className = 'data-value warning';
                } else {
                    fixElement.className = 'data-value error';
                }
            }
            
            if (data.satellites !== undefined) {
                const satElement = document.getElementById('satellites');
                satElement.textContent = data.satellites;
                
                // Color coding for satellite count
                if (data.satellites >= 6) {
                    satElement.className = 'data-value';
                } else if (data.satellites >= 4) {
                    satElement.className = 'data-value warning';
                } else {
                    satElement.className = 'data-value error';
                }
            }
            
            if (data.hdop !== undefined) {
                document.getElementById('hdop').textContent = data.hdop.toFixed(1);
            }
            
            if (data.timestamp) {
                document.getElementById('last-update').textContent = data.timestamp;
            }
        }

        function updateConsole(sentence) {
            if (isPaused) return;
            
            const console = document.getElementById('console');
            const timestamp = new Date().toLocaleTimeString();
            const line = `[${timestamp}] ${sentence}\\n`;
            
            console.textContent += line;
            
            // Keep only last 50 lines
            const lines = console.textContent.split('\\n');
            if (lines.length > 50) {
                console.textContent = lines.slice(-50).join('\\n');
            }
            
            console.scrollTop = console.scrollHeight;
        }

        function updateStatistics() {
            totalSentences++;
            document.getElementById('total-sentences').textContent = totalSentences;
            
            // Calculate sentences per minute
            const elapsed = (Date.now() - startTime) / 60000; // minutes
            const spm = Math.round(totalSentences / elapsed);
            document.getElementById('sentences-per-minute').textContent = spm;
            
            // Update uptime
            document.getElementById('uptime').textContent = Math.round(elapsed);
        }

        // Control functions
        function clearConsole() {
            document.getElementById('console').textContent = '';
        }

        function togglePause() {
            isPaused = !isPaused;
            const pauseText = document.getElementById('pause-text');
            pauseText.textContent = isPaused ? 'Resume' : 'Pause';
        }

        function exportData() {
            const data = {
                timestamp: new Date().toISOString(),
                totalSentences: totalSentences,
                trackPoints: trackPoints,
                currentPosition: {
                    latitude: parseFloat(document.getElementById('latitude').textContent),
                    longitude: parseFloat(document.getElementById('longitude').textContent)
                }
            };
            
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `nmea_export_${new Date().toISOString().slice(0,10)}.json`;
            a.click();
        }

        // Initialize everything
        window.onload = function() {
            initMap();
            connectWebSocket();
        };
    </script>
</body>
</html>'''

def handle_http_request(client_socket):
    """Handle HTTP requests"""
    try:
        request = client_socket.recv(1024).decode('utf-8')
        
        if 'GET /' in request:
            response = 'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n'
            response += get_html_page()
            client_socket.send(response.encode('utf-8'))
        
        elif 'GET /api/status' in request:
            response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
            status_data = {
                **nmea_data,
                'system': {
                    'clients_connected': len(clients),
                    'uptime_seconds': int(time.time()),
                    'free_memory': gc.mem_free() if hasattr(gc, 'mem_free') else 0,
                    'wifi_rssi': wifi.status('rssi') if wifi and hasattr(wifi, 'status') else 0
                }
            }
            response += json.dumps(status_data)
            client_socket.send(response.encode('utf-8'))
        
        elif 'GET /api/config' in request:
            response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n\r\n'
            config_data = {
                'wifi_mode': Config.WIFI_MODE,
                'wifi_ssid': Config.WIFI_SSID,
                'uart_baudrate': Config.UART_BAUDRATE,
                'uart_pins': {'tx': Config.UART_TX, 'rx': Config.UART_RX},
                'nmea_sentences': Config.NMEA_SENTENCES
            }
            response += json.dumps(config_data)
            client_socket.send(response.encode('utf-8'))
        
        elif 'GET /api/reset' in request:
            response = 'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n'
            response += '{"status": "restarting"}'
            client_socket.send(response.encode('utf-8'))
            client_socket.close()
            time.sleep(1)
            reset()
        
        else:
            response = 'HTTP/1.1 404 Not Found\r\n\r\n404 Not Found'
            client_socket.send(response.encode('utf-8'))
    
    except Exception as e:
        print(f"[HTTP] Error: {e}")
    
    finally:
        client_socket.close()

def websocket_handshake(client_socket, request):
    """Perform WebSocket handshake"""
    try:
        lines = request.split('\r\n')
        key = None
        
        for line in lines:
            if line.startswith('Sec-WebSocket-Key:'):
                key = line.split(':', 1)[1].strip()
                break
        
        if key:
            # WebSocket magic string
            magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
            accept_key = ubinascii.b2a_base64(
                hashlib.sha1((key + magic).encode()).digest()
            ).decode().strip()
            
            response = (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept_key}\r\n\r\n"
            )
            
            client_socket.send(response.encode())
            return True
    except Exception as e:
        print(f"[WS] Handshake error: {e}")
    
    return False

def http_server_thread():
    """HTTP server thread"""
    try:
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', Config.HTTP_PORT))
        server_socket.listen(5)
        
        print(f"[HTTP] Server listening on port {Config.HTTP_PORT}")
        
        while True:
            client_socket, addr = server_socket.accept()
            try:
                handle_http_request(client_socket)
            except Exception as e:
                print(f"[HTTP] Client error: {e}")
                client_socket.close()
    
    except Exception as e:
        print(f"[HTTP] Server error: {e}")

def websocket_server_thread():
    """WebSocket server thread"""
    global clients
    
    try:
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', Config.WEBSOCKET_PORT))
        server_socket.listen(5)
        
        print(f"[WebSocket] Server listening on port {Config.WEBSOCKET_PORT}")
        
        while True:
            client_socket, addr = server_socket.accept()
            
            try:
                request = client_socket.recv(1024).decode('utf-8')
                
                if 'Upgrade: websocket' in request:
                    if websocket_handshake(client_socket, request):
                        clients.append(client_socket)
                        print(f"[WebSocket] Client connected: {addr}")
                    else:
                        client_socket.close()
                else:
                    client_socket.close()
            
            except Exception as e:
                print(f"[WebSocket] Client error: {e}")
                client_socket.close()
    
    except Exception as e:
        print(f"[WebSocket] Server error: {e}")

# === MAIN FUNCTION ===
def main():
    print("=" * 50)
    print("🛰️  NMEA Tracker ESP32 - Starting...")
    print("=" * 50)
    
    # Setup WiFi
    ip = setup_wifi()
    if not ip:
        print("[ERROR] WiFi setup failed!")
        return
    
    # Setup UART
    if setup_uart():
        print("[UART] Ready to receive NMEA data")
    else:
        print("[WARNING] UART setup failed - no serial data")
    
    # Start threads
    try:
        _thread.start_new_thread(uart_reader_thread, ())
        _thread.start_new_thread(http_server_thread, ())
        _thread.start_new_thread(websocket_server_thread, ())
        
        print(f"\n🌐 Web interface: http://{ip}")
        print("📡 NMEA data streaming active")
        print("🔌 Connect your GPS/AIS device to UART pins")
        print(f"   TX: GPIO{Config.UART_TX}, RX: GPIO{Config.UART_RX}")
        print("\n✅ System ready!")
        
        # Main loop - keep system alive and manage memory
        while True:
            time.sleep(10)
            gc.collect()  # Garbage collection
            led.value(not led.value())  # Heartbeat
    
    except Exception as e:
        print(f"[ERROR] System error: {e}")
        reset()

# === ENTRY POINT ===
if __name__ == "__main__":
    main()
