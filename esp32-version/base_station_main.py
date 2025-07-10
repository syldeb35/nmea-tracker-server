# Enhanced Base Station Main Application
# This version includes advanced features for base station operation

#!/usr/bin/env micropython
# -*- coding: utf-8 -*-

import network
import socket
import time
import gc
import json
import re
from machine import UART, Pin, reset, Timer
import _thread
import ubinascii
import hashlib
import ntptime

# Try to import config, fallback to defaults
try:
    from base_station import *
except ImportError:
    from config import *

# === ENHANCED BASE STATION CLASS ===
class BaseStationManager:
    def __init__(self):
        self.stats = {
            'total_sentences': 0,
            'sentences_per_minute': 0,
            'connected_clients': 0,
            'uptime_start': time.time(),
            'last_data_time': 0,
            'error_count': 0
        }
        
        self.data_buffer = []
        self.last_position = {'lat': 0, 'lon': 0, 'time': 0}
        
        # Initialize hardware
        self.setup_hardware()
        
        # Start watchdog timer if configured
        if hasattr(BASE_STATION_CONFIG, 'watchdog_timeout'):
            self.watchdog_timer = Timer(0)
            self.watchdog_timer.init(
                period=BASE_STATION_CONFIG['watchdog_timeout'] * 1000,
                mode=Timer.PERIODIC,
                callback=self.watchdog_callback
            )
    
    def setup_hardware(self):
        """Initialize base station hardware"""
        # Status LEDs
        self.status_led = Pin(HARDWARE_CONFIG['status_led_pin'], Pin.OUT)
        
        if HARDWARE_CONFIG['external_led_pin']:
            self.external_led = Pin(HARDWARE_CONFIG['external_led_pin'], Pin.OUT)
        
        # Relay control for antenna switching
        if HARDWARE_CONFIG.get('relay_control_pin'):
            self.relay_pin = Pin(HARDWARE_CONFIG['relay_control_pin'], Pin.OUT)
        
        # Power monitoring
        if HARDWARE_CONFIG.get('power_monitor_pin'):
            from machine import ADC
            self.power_adc = ADC(Pin(HARDWARE_CONFIG['power_monitor_pin']))
            self.power_adc.atten(ADC.ATTN_11DB)
    
    def watchdog_callback(self, timer):
        """Watchdog timer callback"""
        current_time = time.time()
        if current_time - self.stats['last_data_time'] > 300:  # 5 minutes without data
            print("[WATCHDOG] No data received - restarting...")
            reset()
    
    def update_stats(self):
        """Update system statistics"""
        self.stats['total_sentences'] += 1
        self.stats['last_data_time'] = time.time()
        
        # Calculate sentences per minute
        uptime_minutes = (time.time() - self.stats['uptime_start']) / 60
        if uptime_minutes > 0:
            self.stats['sentences_per_minute'] = int(self.stats['total_sentences'] / uptime_minutes)
    
    def get_system_status(self):
        """Get comprehensive system status"""
        uptime = time.time() - self.stats['uptime_start']
        
        status = {
            'uptime_seconds': int(uptime),
            'uptime_formatted': self.format_uptime(uptime),
            'memory_free': gc.mem_free() if hasattr(gc, 'mem_free') else 0,
            'total_sentences': self.stats['total_sentences'],
            'sentences_per_minute': self.stats['sentences_per_minute'],
            'error_count': self.stats['error_count'],
            'last_position': self.last_position
        }
        
        # Add power monitoring if available
        if hasattr(self, 'power_adc'):
            voltage = (self.power_adc.read() / 4095) * 3.3 * 2  # Voltage divider
            status['supply_voltage'] = round(voltage, 2)
        
        return status
    
    def format_uptime(self, seconds):
        """Format uptime in human readable format"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{days}d {hours}h {minutes}m"
    
    def log_position(self, lat, lon):
        """Log position data for tracking"""
        self.last_position = {
            'lat': lat,
            'lon': lon, 
            'time': time.time()
        }
        
        # Add to data buffer for export
        if len(self.data_buffer) > 1000:  # Keep last 1000 positions
            self.data_buffer.pop(0)
        
        self.data_buffer.append(self.last_position.copy())

# Initialize base station manager
base_station = BaseStationManager()

# === ENHANCED NMEA PARSER ===
class EnhancedNMEAParser:
    def __init__(self):
        # Comprehensive NMEA patterns
        self.patterns = {
            'GGA': re.compile(r'^\$..GGA,([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),\*([A-F0-9]{2})'),
            'RMC': re.compile(r'^\$..RMC,([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),\*([A-F0-9]{2})'),
            'VTG': re.compile(r'^\$..VTG,([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),\*([A-F0-9]{2})'),
            'HDT': re.compile(r'^\$..HDT,([^,]*),([^,]*),\*([A-F0-9]{2})'),
            'VDM': re.compile(r'^\![A-Z]{2}VDM,([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),\*([A-F0-9]{2})')
        }
        
        self.sentence_counts = {}
        self.last_sentences = {}
    
    def validate_checksum(self, sentence):
        """Validate NMEA sentence checksum"""
        if '*' not in sentence:
            return False
        
        try:
            data, checksum = sentence.split('*')
            calculated = 0
            for char in data[1:]:  # Skip the $ or !
                calculated ^= ord(char)
            return f"{calculated:02X}" == checksum.upper()
        except:
            return False
    
    def parse_coordinate(self, coord_str, direction):
        """Convert NMEA coordinate to decimal degrees"""
        if not coord_str or not direction:
            return 0.0
        
        try:
            if len(coord_str) >= 7 and '.' in coord_str:
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
    
    def parse_sentence(self, sentence):
        """Parse any supported NMEA sentence"""
        sentence = sentence.strip()
        
        # Validate checksum
        if not self.validate_checksum(sentence):
            return None
        
        # Detect sentence type
        sentence_type = None
        for stype in ['GGA', 'RMC', 'VTG', 'HDT', 'VDM']:
            if stype in sentence:
                sentence_type = stype
                break
        
        if not sentence_type or sentence_type not in self.patterns:
            return None
        
        # Count sentences
        self.sentence_counts[sentence_type] = self.sentence_counts.get(sentence_type, 0) + 1
        
        # Parse specific sentence types
        if sentence_type == 'GGA':
            return self.parse_gga(sentence)
        elif sentence_type == 'RMC':
            return self.parse_rmc(sentence)
        elif sentence_type == 'VTG':
            return self.parse_vtg(sentence)
        elif sentence_type == 'HDT':
            return self.parse_hdt(sentence)
        elif sentence_type == 'VDM':
            return self.parse_ais(sentence)
        
        return None
    
    def parse_gga(self, sentence):
        """Parse GGA sentence"""
        match = self.patterns['GGA'].match(sentence)
        if match:
            groups = match.groups()
            try:
                lat = self.parse_coordinate(groups[1], groups[2])
                lon = self.parse_coordinate(groups[3], groups[4])
                
                # Log position if valid
                if lat != 0 and lon != 0:
                    base_station.log_position(lat, lon)
                
                return {
                    'type': 'GGA',
                    'timestamp': groups[0],
                    'latitude': lat,
                    'longitude': lon,
                    'fix_quality': int(groups[5]) if groups[5] else 0,
                    'satellites': int(groups[6]) if groups[6] else 0,
                    'hdop': float(groups[7]) if groups[7] else 0.0,
                    'altitude': float(groups[8]) if groups[8] else 0.0,
                    'altitude_units': groups[9]
                }
            except:
                pass
        return None
    
    def parse_rmc(self, sentence):
        """Parse RMC sentence"""
        match = self.patterns['RMC'].match(sentence)
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
                    'date': groups[8],
                    'magnetic_variation': float(groups[9]) if groups[9] else 0.0
                }
            except:
                pass
        return None
    
    def parse_vtg(self, sentence):
        """Parse VTG sentence (Track made good)"""
        match = self.patterns['VTG'].match(sentence)
        if match:
            groups = match.groups()
            try:
                return {
                    'type': 'VTG',
                    'true_course': float(groups[0]) if groups[0] else 0.0,
                    'magnetic_course': float(groups[2]) if groups[2] else 0.0,
                    'speed_knots': float(groups[4]) if groups[4] else 0.0,
                    'speed_kmh': float(groups[6]) if groups[6] else 0.0
                }
            except:
                pass
        return None
    
    def parse_hdt(self, sentence):
        """Parse HDT sentence (True heading)"""
        match = self.patterns['HDT'].match(sentence)
        if match:
            groups = match.groups()
            try:
                return {
                    'type': 'HDT',
                    'heading': float(groups[0]) if groups[0] else 0.0
                }
            except:
                pass
        return None
    
    def parse_ais(self, sentence):
        """Parse AIS VDM sentence"""
        match = self.patterns['VDM'].match(sentence)
        if match:
            groups = match.groups()
            return {
                'type': 'AIS',
                'fragment_count': int(groups[0]) if groups[0] else 1,
                'fragment_number': int(groups[1]) if groups[1] else 1,
                'message_id': groups[2],
                'channel': groups[3],
                'data': groups[4],
                'fillbits': int(groups[5]) if groups[5] else 0
            }
        return None

# === TCP RELAY SERVER ===
def tcp_relay_server():
    """TCP server for relaying NMEA data to other systems"""
    if not RELAY_CONFIG.get('tcp_relay_enabled', False):
        return
    
    try:
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', NETWORK_CONFIG['tcp_relay_port']))
        server_socket.listen(5)
        
        print(f"[TCP Relay] Server listening on port {NETWORK_CONFIG['tcp_relay_port']}")
        
        relay_clients = []
        
        while True:
            client_socket, addr = server_socket.accept()
            relay_clients.append(client_socket)
            print(f"[TCP Relay] Client connected: {addr}")
            
            # Clean up disconnected clients
            active_clients = []
            for client in relay_clients:
                try:
                    client.send(b'')  # Test connection
                    active_clients.append(client)
                except:
                    client.close()
            relay_clients = active_clients
    
    except Exception as e:
        print(f"[TCP Relay] Error: {e}")

# Start base station
if __name__ == "__main__":
    print("🛰️ Starting Enhanced NMEA Base Station...")
    
    # Sync time if configured
    if SYSTEM_CONFIG.get('ntp_sync', False):
        try:
            ntptime.settime()
            print("[NTP] Time synchronized")
        except:
            print("[NTP] Time sync failed")
    
    # Start TCP relay if enabled
    if RELAY_CONFIG.get('tcp_relay_enabled', False):
        _thread.start_new_thread(tcp_relay_server, ())
    
    print("✅ Enhanced Base Station ready!")
