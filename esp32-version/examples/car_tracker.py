# Car/Vehicle Tracker Configuration Example  
# Optimized for automotive GPS tracking

WIFI_CONFIG = {
    "mode": "STA",  # Connect to existing WiFi when parked
    "sta_ssid": "HomeWiFi",
    "sta_password": "your_password",
    # Fallback to AP mode when no WiFi available
    "ap_ssid": "CarTracker_GPS", 
    "ap_password": "car123456"
}

NETWORK_CONFIG = {
    "http_port": 80,
    "websocket_port": 81
}

# Automotive GPS typically uses 9600 baud
SERIAL_CONFIG = {
    "uart_num": 2,
    "tx_pin": 17,
    "rx_pin": 16, 
    "baudrate": 9600,  # Common automotive GPS rate
    "timeout": 1000
}

# Car-focused NMEA sentences
NMEA_CONFIG = {
    "sentences": [
        "GGA",  # GPS Fix Data
        "RMC",  # Speed and position
        "VTG",  # Speed over ground
        "GLL"   # Geographic position
    ],
    "min_update_interval": 0.2  # 5Hz for responsive tracking
}

HARDWARE_CONFIG = {
    "status_led_pin": 2,
    "external_led_pin": None,
    "buzzer_pin": None
}

SYSTEM_CONFIG = {
    "debug": False,
    "gc_interval": 5,        # Frequent GC for responsive updates
    "max_clients": 2,        # Driver + passenger devices
    "buffer_size": 512       # Smaller buffer for car GPS
}
