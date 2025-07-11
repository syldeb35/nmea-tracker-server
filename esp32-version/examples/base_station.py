# Base Station Configuration Example
# Optimized for stationary NMEA/AIS data collection and relay

WIFI_CONFIG = {
    "mode": "STA",  # Connect to existing network for internet access
    "sta_ssid": "BaseStationNetwork",
    "sta_password": "station2024",
    # Fallback AP mode if network fails
    "ap_ssid": "NMEA_BaseStation", 
    "ap_password": "basestation123"
}

NETWORK_CONFIG = {
    "http_port": 80,
    "websocket_port": 81,
    "tcp_relay_port": 10110,  # Standard NMEA relay port
    "udp_broadcast_port": 4001  # UDP broadcast for clients
}

# Base station typically handles multiple NMEA sources
SERIAL_CONFIG = {
    "uart_num": 2,
    "tx_pin": 17,
    "rx_pin": 16,
    "baudrate": 38400,  # Higher baudrate for base stations
    "timeout": 500      # Shorter timeout for responsiveness
}

# Comprehensive NMEA sentence collection for base station
NMEA_CONFIG = {
    "sentences": [
        # GPS sentences
        "GGA", "RMC", "GLL", "VTG", "ZDA", "GSA", "GSV",
        # Navigation sentences  
        "HDT", "HDG", "ROT", "VHW", "VLW",
        # Wind and weather
        "MWV", "MWD", "MTA", "MMB",
        # AIS sentences
        "VDM", "VDO", "AIV", "ABK", "BBM",
        # Depth and speed
        "DPT", "DBT", "MTW", "VBW"
    ],
    "min_update_interval": 0.05,  # 20Hz update rate for base station
    "sentence_filtering": True,   # Enable advanced filtering
    "duplicate_filtering": True   # Remove duplicate sentences
}

# Base station hardware configuration
HARDWARE_CONFIG = {
    "status_led_pin": 2,
    "external_led_pin": 5,       # External status LED
    "relay_control_pin": 4,      # Control relay for antenna switching
    "buzzer_pin": None,          # No buzzer for silent operation
    "power_monitor_pin": 34      # Monitor power supply voltage
}

# Base station system configuration
SYSTEM_CONFIG = {
    "debug": True,               # Enable debug for monitoring
    "gc_interval": 30,           # Less frequent GC for stability
    "max_clients": 10,           # Support multiple clients
    "buffer_size": 4096,         # Large buffer for high data rates
    "log_to_sd": True,           # Enable SD card logging if available
    "ntp_sync": True,            # Sync time with NTP server
    "data_relay": True,          # Enable data relay to other systems
    "web_authentication": False  # No auth for internal network
}

# Data relay configuration
RELAY_CONFIG = {
    "tcp_relay_enabled": True,
    "udp_broadcast_enabled": True,
    "mqtt_relay_enabled": False,  # Optional MQTT relay
    "mqtt_broker": "mqtt.basestation.local",
    "mqtt_topic": "nmea/data",
    "relay_rate_limit": 100      # Max sentences per second
}

# Base station specific features
BASE_STATION_CONFIG = {
    "auto_restart": True,        # Auto restart on errors
    "watchdog_timeout": 300,     # 5 minute watchdog timer
    "position_logging": True,    # Log all positions
    "statistics_interval": 60,   # Stats update every minute
    "backup_power_monitor": True, # Monitor backup power
    "antenna_switching": False,   # Multiple antenna support
    "remote_management": True     # Allow remote configuration
}
