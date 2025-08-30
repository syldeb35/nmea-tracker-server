
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-08-30

### ✨ Added in 1.2.0

- **MarineTraffic UDP Forwarder**: Forward AIS sentences to MarineTraffic (configurable IP, port, ID)
- **Editable MarineTraffic Configuration**: MarineTraffic parameters (IP, port, ID) are now editable and persistent via the web UI
- **.env Integration**: All configuration, including MarineTraffic, is now saved to and loaded from the .env file
- **UI/UX Improvements**: Configuration page refactored to two columns, improved layout and usability
- **Build Script Translation**: build_with_tray.bat fully translated to English
- **Backend/Frontend Integration**: Flask backend and web UI now fully synchronized for all configuration fields

### 🎨 Interface 1.2.0

- **Improved Configuration UI**: Two-column layout, MarineTraffic fields included
- **Real-time status and value population**: All config fields are now initialized from .env and changes are persistent

### 🐛 Fixed in 1.2.0

- **Configuration Persistence**: MarineTraffic and other config values now correctly saved and loaded via the web UI
- **UI Initialization**: All fields now show current values from .env on page load

---

## [1.1.0] - 2025-08-03

### ✨ Added in 1.1.0

- **Full AIS support** with decoding of fragmented sentences
- **Multi-fragment AIS message handling** for ship names, destinations, and ETA
- **Client/server modes** for TCP and UDP connections
- **Dynamic configuration** via web interface with persistence in .env
- **Auto-loading** configuration at startup from .env file
- **Smart cache** for AIS fragments with automatic cleanup
- **Extended REST API** (/api/config, /api/status, /api/nmea_history)
- **Structured logging** by file (main.log, debug.log, network.log, errors.log, nmea_data.log)

### 🎨 Interface 1.1.0

- **Improved configuration interface** with client/server modes
- **Real-time display** of AIS data with ship names
- **Visualization of TCP client connections** to external GPS devices
- **Protocol color coding** (UDP=yellow, TCP=cyan, Serial=green)
- **Connection status** in real time via WebSocket
- **Correct initialization** of forms with actual values

### 🔧 Technical

- **AIS Type 5 decoding** for static data (names, types, destinations)
- **Fragmented AIS parser** for multi-frame messages
- **Separate TCP/UDP threads** depending on client/server mode
- **Configuration variables** read from .env at startup
- **AIS ship cache** with merging of position/static data
- **Robust error handling** for SSL and network
- **Suppression of verbose HTTP logs** for a cleaner interface

### 🚀 Performance

- **Optimized NMEA parsing** with smart cleanup
- **AIS fragment cache** with automatic expiration (30s)
- **Dual WebSocket emission** (Windy plugin + web interface)
- **Improved memory management** for real-time data buffer

### 🐛 Fixed in 1.1.0

- **UDP/TCP did not start** automatically at launch
- **AIS ship names** not retrieved (fragmented sentences)
- **Default configuration** used instead of .env values
- **Interface not initialized** with actual client/server modes
- **Noisy HTTP logs** hidden on Windows
- **TCP/UDP threads** server mode only (client added)

### 📦 Configuration

- **Default UDP port**: 50110 (instead of 5005)
- **TCP client mode** to external GPS devices
- **Extended .env variables**: UDP_MODE, TCP_MODE, *_TARGET_IP, *_TARGET_PORT.
- **Automatic persistence** of parameters via web interface

## [1.0.0] - 2025-07-10

### ✨ Added in 1.0.0

- **Real-time NMEA/AIS server** with multi-source support (Serial, UDP, TCP)
- **Modern web interface** with interactive Leaflet.js map
- **NMEA decoder** for GGA, RMC, GLL, VTG, HDT formats
- **Auto-detection** of Bluetooth serial ports
- **Intuitive and responsive web configuration**
- **HTTPS server** with integrated SSL certificates
- **WebSocket** for real-time updates
- **Rotating logging** of NMEA sentences
- **Graceful shutdown** with Ctrl+C
- **Standalone executable** via PyInstaller with custom icon
- **Cross-platform support** (Windows, Linux, macOS)

### 🎨 Interface in 1.0.0

- **Real-time map** with GPS tracking and history
- **Custom SVG favicon** for the web app
- **Responsive design** for mobile/desktop
- **Dark/maritime theme** for the viewer
- **Professional app icon** (maritime compass)

### 🔧 Technical in 1.0.0

- **Flask + SocketIO** for backend
- **gevent** for network performance
- **PySerial** with advanced error handling
- **Signal handling** for Unix/Windows
- **Configuration via environment variables**
- **Automated build scripts**

### 📦 Distribution

- **Build scripts** for Windows/Unix
- **Automated executable tests**
- **Complete documentation** (README, BUILD_README)
- **Multi-resolution icon** for Windows

### 🔒 Security

- **SSL certificates** for HTTPS
- **Automatic HTTP fallback**
- **Robust error handling**
- **NMEA data validation**

## [Unreleased]

### 🔮 Planned

- Authentication interface
- Historical data charts
- Multi-language support
- Companion mobile app
- REST API for third-party integrations
- Docker package
- Cloud synchronization

---

**Version format:** [Major.Minor.Patch]

- **Major**: Incompatible API changes
- **Minor**: Backwards-compatible new features
- **Patch**: Backwards-compatible bug fixes
