# Boat/Marine Configuration Example
# Optimized for marine GPS and AIS reception

WIFI_CONFIG = {
    "mode": "AP",  # Access Point mode for boat hotspot
    "ap_ssid": "BoatTracker_AIS",
    "ap_password": "marine2024"
}

NETWORK_CONFIG = {
    "http_port": 80,
    "websocket_port": 81
}

# Marine GPS typically uses 4800 baud
SERIAL_CONFIG = {
    "uart_num": 2,
    "tx_pin": 17,
    "rx_pin": 16,
    "baudrate": 4800,  # Standard marine NMEA
    "timeout": 2000    # Longer timeout for marine conditions
}

# Marine-specific NMEA sentences
NMEA_CONFIG = {
    "sentences": [
        "GGA",  # GPS Fix Data
        "RMC",  # Recommended Minimum  
        "VTG",  # Track made good
        "HDT",  # True Heading
        "HDG",  # Magnetic Heading
        "ROT",  # Rate of Turn
        "AIS",  # AIS messages
        "VDM",  # AIS VHF Data-link Message
        "VDO"   # AIS VHF Data-link Own-vessel report
    ],
    "min_update_interval": 0.5  # 2Hz update rate
}

HARDWARE_CONFIG = {
    "status_led_pin": 2,
    "external_led_pin": 5,   # External marine LED indicator
    "buzzer_pin": 4          # Alert buzzer for emergencies
}

SYSTEM_CONFIG = {
    "debug": False,
    "gc_interval": 15,       # Less frequent GC for stability
    "max_clients": 3,        # Limit for marine bandwidth
    "buffer_size": 2048      # Larger buffer for AIS messages
}
