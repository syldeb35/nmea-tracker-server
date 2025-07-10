# NMEA Tracker ESP32 - Configuration File
# Copy this file to your ESP32 as config.py

# WiFi Configuration
WIFI_CONFIG = {
    # Mode: "AP" for Access Point (ESP32 creates hotspot)
    #       "STA" for Station (ESP32 connects to existing WiFi)
    "mode": "AP",
    
    # Access Point settings (when mode = "AP")
    "ap_ssid": "NMEA_Tracker_ESP32",
    "ap_password": "nmea123456",
    
    # Station settings (when mode = "STA") 
    "sta_ssid": "YourWiFiNetwork",
    "sta_password": "YourWiFiPassword"
}

# Network Ports
NETWORK_CONFIG = {
    "http_port": 80,
    "websocket_port": 81
}

# UART/Serial Configuration
SERIAL_CONFIG = {
    "uart_num": 2,       # UART2 on ESP32
    "tx_pin": 17,        # GPIO17 for TX
    "rx_pin": 16,        # GPIO16 for RX  
    "baudrate": 4800,    # Standard NMEA baudrate
    "timeout": 1000      # Read timeout in ms
}

# NMEA Sentence Filtering
NMEA_CONFIG = {
    # Sentences to process (others will be ignored)
    "sentences": ["GGA", "RMC", "GLL", "VTG", "HDT", "AIS"],
    
    # Update rate limiting (minimum time between updates in seconds)
    "min_update_interval": 0.1
}

# Hardware Configuration
HARDWARE_CONFIG = {
    "status_led_pin": 2,   # Built-in LED on most ESP32 boards
    "external_led_pin": None,  # Optional external status LED
    "buzzer_pin": None     # Optional buzzer for alerts
}

# System Configuration
SYSTEM_CONFIG = {
    "debug": False,
    "gc_interval": 10,     # Garbage collection interval (seconds)
    "max_clients": 5,      # Maximum WebSocket clients
    "buffer_size": 1024    # UART buffer size
}
