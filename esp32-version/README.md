# NMEA Tracker ESP32 - Installation and Setup Guide

## 📋 Requirements

### Hardware
- **ESP32 Development Board** (ESP32-DevKitC, NodeMCU-32S, or similar)
- **GPS/AIS Device** with NMEA output
- **Jumper Wires** for connections
- **Power Supply** (USB or external 5V)
- **Optional**: External WiFi antenna for better range

### Software
- **MicroPython firmware** for ESP32
- **File transfer tool** (ampy, Thonny, or similar)
- **Serial terminal** for debugging

## 🚀 Installation Steps

### 1. Flash MicroPython Firmware

1. Download the latest ESP32 MicroPython firmware from:
   https://micropython.org/download/esp32/

2. Install esptool:
   ```bash
   pip install esptool
   ```

3. Flash the firmware:
   ```bash
   # Erase flash
   esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
   
   # Flash MicroPython (adjust firmware filename)
   esptool.py --chip esp32 --port /dev/ttyUSB0 write_flash -z 0x1000 esp32-20210902-v1.17.bin
   ```

   **Windows users**: Replace `/dev/ttyUSB0` with `COM3` (or your port)

### 2. Upload Files to ESP32

Install ampy for file transfer:
```bash
pip install adafruit-ampy
```

Upload the files:
```bash
# Upload main application
ampy --port /dev/ttyUSB0 put main.py

# Upload configuration  
ampy --port /dev/ttyUSB0 put config.py

# Optional: Upload boot.py for auto-start
ampy --port /dev/ttyUSB0 put boot.py
```

### 3. Hardware Connections

Connect your GPS/AIS device to the ESP32:

```
GPS/AIS Device    ESP32
--------------    -----
TX (Data Out)  -> GPIO16 (RX2)
RX (Data In)   -> GPIO17 (TX2) [Optional]
GND            -> GND
VCC            -> 3.3V or 5V (depending on device)
```

**Common GPS Modules:**
- **NEO-6M/8M**: 3.3V operation
- **NEO-9M**: 3.3V operation  
- **AIS Receivers**: Usually 5V

## ⚙️ Configuration

Edit `config.py` to customize your setup:

### WiFi Access Point Mode (Default)
```python
WIFI_CONFIG = {
    "mode": "AP",
    "ap_ssid": "NMEA_Tracker_ESP32",
    "ap_password": "nmea123456"
}
```

### WiFi Station Mode (Connect to existing network)
```python
WIFI_CONFIG = {
    "mode": "STA", 
    "sta_ssid": "YourWiFiNetwork",
    "sta_password": "YourWiFiPassword"
}
```

### Serial/UART Settings
```python
SERIAL_CONFIG = {
    "uart_num": 2,
    "tx_pin": 17,     # Adjust if needed
    "rx_pin": 16,     # Adjust if needed  
    "baudrate": 4800  # Standard NMEA
}
```

## 🔧 Usage

### 1. Power On
- Connect ESP32 to USB power
- Built-in LED will blink during startup
- LED stays on when WiFi is connected

### 2. Connect to Web Interface

**Access Point Mode:**
1. Connect your device to WiFi: `NMEA_Tracker_ESP32`
2. Password: `nmea123456`
3. Open browser: `http://192.168.4.1`

**Station Mode:**
1. Check serial output for assigned IP
2. Open browser: `http://[ESP32_IP_ADDRESS]`

### 3. Monitor NMEA Data
- Real-time position data
- GPS status information  
- Raw NMEA sentence stream
- WebSocket connection status

## 🔍 Troubleshooting

### No WiFi Connection
- Check SSID/password in config.py
- Verify ESP32 is within range
- Try AP mode for initial testing

### No NMEA Data
- Verify GPS device connections
- Check baudrate settings (usually 4800 or 9600)
- Ensure GPS has satellite fix
- Test with different UART pins if needed

### Memory Issues
- Reduce max_clients in config.py
- Increase gc_interval for more frequent cleanup
- Use shorter variable names in custom code

### Serial Console Debug
Connect to ESP32 via serial terminal:
```bash
# Linux/Mac
screen /dev/ttyUSB0 115200

# Windows (PuTTY)
# Connect to COM port at 115200 baud
```

## 📍 GPIO Pin Reference

**Default Configuration:**
- GPIO16: UART RX (connect to GPS TX)
- GPIO17: UART TX (connect to GPS RX)
- GPIO2: Status LED (built-in)

**Alternative Pins:**
You can use other GPIO pins by modifying config.py:
- Available: 4, 5, 12, 13, 14, 15, 18, 19, 21, 22, 23, 25, 26, 27
- Avoid: 0, 1, 2, 3, 6-11 (used by system/flash)

## 🔧 Customization

### Adding New NMEA Sentences
Edit the parser in main.py to support additional sentence types:

```python
def parse_vtg(self, sentence):
    # Add VTG (Track made good) parsing
    # Implementation here...
```

### Custom Web Interface  
Modify the `get_html_page()` function to customize the UI:
- Add new data fields
- Change styling/colors
- Add charts or maps

### Hardware Expansions
- Add external LEDs for status indication
- Include buzzer for alarms
- Add SD card logging
- Include display (OLED/LCD)

## 📝 File Structure

```
esp32-version/
├── main.py          # Main application code
├── config.py        # Configuration settings
├── boot.py          # Optional auto-start script
├── README.md        # This file
└── examples/        # Example configurations
    ├── boat_setup.py
    └── car_tracker.py
```

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the serial console output
3. Test with minimal configuration
4. Verify hardware connections

## 📄 License

MIT License - Feel free to modify and distribute!
