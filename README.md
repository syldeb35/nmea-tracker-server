# 🧭 NMEA Tracker Server

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)
[![Build Status](https://github.com/syldeb35/nmea-tracker-server/actions/workflows/build-system-tray.yml/badge.svg)](https://github.com/syldeb35/nmea-tracker-server/actions/workflows/build-system-tray.yml)
[![Release](https://img.shields.io/github/v/release/syldeb35/nmea-tracker-server)](https://github.com/syldeb35/nmea-tracker-server/releases/latest)

**Real-time NMEA/AIS server with a modern web interface for GPS data tracking and maritime navigation.**

![NMEA Tracker Interface](https://img.shields.io/badge/Interface-Web%20HTTPS-brightgreen.svg)

## 🌟 Features

### 📡 NMEA Data Reception

- ✅ **Serial (Bluetooth/USB)** - Direct connection to GPS receivers
- ✅ **UDP** - Network reception of NMEA data
- ✅ **TCP** - TCP connection for data streams
- ✅ **Auto-detection** of Bluetooth serial ports
- ✅ **AIS decoding** - Support for maritime vessel tracking

### 🗺️ Real-time Web Interface

- ✅ **Interactive map** with Leaflet.js
- ✅ **Real-time GPS tracking** with history
- ✅ **NMEA decoding** (GGA, RMC, GLL, VTG, HDT)
- ✅ **AIS message parsing** (AIVDM/AIVDO)
- ✅ **WebSocket** for instant updates
- ✅ **Responsive design** for mobile/desktop

### 🔧 Advanced Configuration

- ✅ **Intuitive web configuration interface**
- ✅ **HTTPS server** with SSL certificates
- ✅ **Optimized logging system** with categorized levels
- ✅ **Service mode** for background operation
- ✅ **Multi-platform** (Windows, Linux, macOS)

### 📦 Distribution

- ✅ **Standalone executable** (PyInstaller)
- ✅ **System tray application** for discrete operation
- ✅ **No installation** required on the target machine
- ✅ **Professional custom icon**
- ✅ **Clean shutdown** with signal handling

## 🚀 Quick Installation

### 📦 Option 1: Direct Download (Recommended for Windows)

**System Tray Version (Discrete Interface)**:
[![Download System Tray](https://img.shields.io/badge/Download-System%20Tray%20Version-brightgreen?style=for-the-badge&logo=windows)](https://github.com/syldeb35/nmea-tracker-server/releases/latest/download/nmea_tracker_tray.exe)

**All Versions**:
[![Download All](https://img.shields.io/badge/Download-All%20Versions-blue?style=for-the-badge&logo=github)](https://github.com/syldeb35/nmea-tracker-server/releases/latest)

**Automated Builds**: All executables are automatically generated via GitHub Actions for each release.

### 🛠️ Option 2: Build from Source Code

**Quick method with interactive menu:**

```bash
# Main script with menu (Linux/macOS)
./run.sh
```

**Manual method by OS:**

```bash
# Linux
./scripts/linux/setup.sh        # Installation
./scripts/linux/build.sh        # Build

# Windows  
scripts\windows\setup.bat       # Installation
scripts\windows\build.bat       # Build

# macOS
./scripts/macos/setup.sh        # Installation
./scripts/macos/build.sh        # Build
```

**Available scripts:**

- 📁 `scripts/linux/` - Scripts for Linux (Ubuntu, Debian, CentOS, etc.)
- 📁 `scripts/windows/` - Scripts for Windows (.bat)
- 📁 `scripts/macos/` - Scripts for macOS
- 🚀 `run.sh` - Main interactive menu (Linux/macOS)

### Option 3: Manual Python Installation

```bash
# Clone the repository
git clone https://github.com/syldeb35/nmea-tracker-server.git
cd nmea-tracker-server

# Install dependencies
pip install -r requirements.txt

# Start the server
python nmea_server.py
```

## 🌐 Usage

1. **Starting**: Launch the executable or `python nmea_server.py`
2. **Configuration**: Open `https://localhost:5000/config.html`
3. **Visualization**: Access `https://localhost:5000/` to see real-time data
4. **Stopping**: Use `Ctrl+C` for a clean shutdown

### 📱 Web Interface

| Page | Description | URL |
|------|-------------|-----|
| **Viewer** | Real-time map + NMEA data | `https://localhost:5000/` |
| **Configuration** | Connection settings | `https://localhost:5000/config.html` |

## 🔧 Configuration

### Supported Connections

#### 📻 Serial Port (Bluetooth/USB)

```text
Port: Auto-detection or manual (e.g., COM3, /dev/rfcomm0, AUTO)
Speed: 4800, 9600, 19200, 38400, 57600, 115200 bps
```

#### 🌐 UDP Network

```text
Mode: Server/Client
Server - IP: 0.0.0.0 (listen on all interfaces)
Server - Port: 50110 (default)
Client - Target IP: Remote server address
Client - Target Port: Remote server port
```

#### 🔗 TCP Network

```text
Mode: Server/Client
Server - IP: 0.0.0.0 (listen on all interfaces)
Server - Port: 50111 (default)
Client - Target IP: Remote server address  
Client - Target Port: Remote server port
```

### Environment Variables (.env)

```bash
DEBUG=False
SERVICE_MODE=False
ENABLE_SERIAL=True
ENABLE_UDP=True
ENABLE_TCP=True
UDP_MODE=server
TCP_MODE=client
UDP_PORT=50110
TCP_PORT=50111
UDP_TARGET_IP=192.168.1.100
UDP_TARGET_PORT=50110
TCP_TARGET_IP=192.168.1.100
TCP_TARGET_PORT=50110
SERIAL_PORT=AUTO
SERIAL_BAUDRATE=4800
HTTP_PORT=5000
```

## 📊 Supported NMEA Formats

| Format | Description | Extracted Data |
|--------|-------------|----------------|
| **GGA** | GPS Position | Latitude, Longitude, Altitude, Time |
| **RMC** | Position + Navigation | Position, Speed, Date, Time |
| **GLL** | Geographic Position | Latitude, Longitude, Time |
| **VTG** | Speed/Course | True heading, Speed |
| **HDT** | True Heading | Navigation direction |
| **AIS** | Vessel Tracking | AIVDM/AIVDO vessel information |

## 📋 Logging System

The server uses a categorized logging system optimized for production:

### Log Files

```text
logs/
├── main.log          # Essential operational information
├── debug.log         # Technical details (DEBUG=true only)
├── errors.log        # Actual problems and errors
├── network.log       # Network operations and connections
└── nmea_data.log     # NMEA message data (rotating)
```

### Log Levels

- **Main Logger**: Important user information (connections, status, warnings)
- **Debug Logger**: Technical details only shown when `DEBUG=true`
- **Error Logger**: Actual errors and problems
- **Network Logger**: Network-specific operations

## 🛠️ Development

### Project Structure

```text
nmea-tracker-server/
├── 📄 nmea_server.py     # Main server application
├── 📄 nmea_server.spec   # PyInstaller configuration
├── 📁 templates/              # Web interface
│   ├── index.html             # Main viewer
│   ├── config.html            # Configuration page
│   └── favicon.svg            # Web icon
├── 📄 cert.pem / key.pem      # SSL certificates
├── 📄 requirements.txt        # Python dependencies
├── 📄 icon.svg / icon.ico     # Application icons
├── 📁 scripts/                # Build scripts by OS
│   ├── linux/                 # Linux-specific scripts
│   ├── windows/               # Windows-specific scripts
│   └── macos/                 # macOS-specific scripts
└── 📁 logs/                   # Categorized log files
```

### Build Process

```bash
# Install PyInstaller
pip install pyinstaller

# Build
pyinstaller nmea_server.spec --clean --noconfirm

# Result
dist/nmea_tracker_server.exe  # Windows
dist/nmea_tracker_server      # Linux/macOS
```

### Technologies Used

- **Backend**: Python 3.8+, Flask, SocketIO, gevent
- **Frontend**: HTML5, JavaScript ES6, Leaflet.js
- **Network**: WebSocket, HTTP/HTTPS, UDP/TCP
- **Serial**: PySerial with Bluetooth auto-detection
- **Service Mode**: Silent background operation support
- **Logging**: Categorized rotating logs for production

## 🔧 Service Mode

The server supports silent background operation:

```bash
# Enable service mode in .env
SERVICE_MODE=True

# Start in background (no console output)
python nmea_server.py

# Check service logs
tail -f logs/main.log
```

### Service Features

- **Silent Operation**: Minimal console output
- **Background Threads**: All connections as daemon threads
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT
- **Log Management**: Rotating logs with size limits
- **Auto-recovery**: Connection monitoring and reconnection

## 🐛 Troubleshooting

### Serial Port Issues

```bash
# Set SERIAL_PORT=AUTO in .env for auto-detection
SERIAL_PORT=AUTO

# Linux: Permissions for manual ports
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0

# Windows: Check Device Manager for COM ports
# Reinstall Bluetooth drivers if necessary

# Check available ports in logs
tail -f logs/debug.log | grep "serial"
```

### Network Port Conflicts

```bash
# Kill existing processes using ports
sudo lsof -i :5000        # Linux/macOS
netstat -ano | find "5000"  # Windows

# Or change ports in .env
HTTP_PORT=5001
UDP_PORT=50112
TCP_PORT=50113
```

### Connection Issues

```bash
# Enable debug mode for detailed logs
DEBUG=True

# Check specific log files
tail -f logs/network.log    # Network connections
tail -f logs/errors.log     # Error details
tail -f logs/debug.log      # Technical details

# Test individual components
ENABLE_SERIAL=True
ENABLE_UDP=False
ENABLE_TCP=False
```

### Service Mode Problems

```bash
# Check if running in service mode
ps aux | grep nmea_server  # Linux/macOS
tasklist | findstr nmea        # Windows

# Service logs location
logs/main_startup.log          # Service startup info
logs/main.log                  # Operational logs
```

## 📈 Roadmap

- [x] ✅ **NMEA/AIS parsing** - Complete NMEA and AIS message decoding
- [x] ✅ **Service mode** - Background operation with optimized logging
- [x] ✅ **Auto-detection** - Automatic serial port discovery
- [x] ✅ **Multi-protocol** - Simultaneous UDP/TCP/Serial connections
- [ ] 🔐 **Authentication interface** - User login and access control
- [ ] 📊 **Historical data graphs** - Data visualization and analytics
- [ ] 🌍 **Multi-language support** - Internationalization
- [ ] 📱 **Mobile companion app** - Smartphone integration
- [ ] ⚙️ **REST API** - Third-party integrations
- [ ] 📦 **Docker package** - Containerized deployment
- [ ] 🔄 **Cloud synchronization** - Remote data backup

## 🤝 Contributing

Contributions are welcome!

1. **Fork** the project
2. **Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Code in **Python 3.8+**
- **Tests** for new features
- **Updated documentation** for changes
- **Descriptive commit messages**
- **Follow logging standards** (main/debug/error categories)

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Sylvain** - *Initial development*

## 🙏 Acknowledgments

- 🗺️ **OpenStreetMap** for maps
- 📦 **Leaflet.js** for interactive mapping
- 🐍 **PyInstaller** for executable compilation
- 🌊 **Maritime community** for NMEA specifications
- ⚡ **Flask/SocketIO** for real-time web interface

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/syldeb35/nmea-tracker-server/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/syldeb35/nmea-tracker-server/discussions)
- 📧 **Contact**: Through GitHub profile

---

## ⭐ Support the Project

If this project helps you, please give it a star!

[![GitHub stars](https://img.shields.io/github/stars/syldeb35/nmea-tracker-server.svg?style=social&label=Star)](https://github.com/syldeb35/nmea-tracker-server)

---

# 📊 Project Status & Technical Details

## ✅ Recent Achievements (August 2025)

### 🔧 **Logging System Optimization**
- **Categorized Logging**: Separated logs into main.log, debug.log, errors.log, network.log
- **Production Ready**: Optimized for service mode with minimal verbosity
- **Log Levels**: Proper categorization of info/debug/error messages
- **Rotating Logs**: Automatic log rotation for NMEA data

### 🔄 **Service Mode Enhancement**
- **Background Operation**: Silent running with daemon threads
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT
- **Service Logs**: Dedicated startup logging for service monitoring
- **Auto-recovery**: Connection monitoring and automatic reconnection

### 🌐 **Network Protocol Improvements**
- **Multi-mode Support**: UDP/TCP server and client modes
- **Connection Management**: Robust connection handling with retry logic
- **Port Configuration**: Flexible port assignment and conflict resolution
- **Auto-detection**: Enhanced serial port discovery (AUTO mode)

### 🧹 **Code Internationalization**
- **Complete English Translation**: All French comments and messages translated
- **Consistent Terminology**: Standardized logging and error messages
- **Documentation Update**: README fully translated and updated

## 🏗️ **Current Architecture**

### Thread Management
```text
Main Process
├── HTTP Server Thread (Flask/SocketIO)
├── Serial Listener Thread (AUTO detection)
├── UDP Thread (Server/Client mode)
├── TCP Thread (Server/Client mode)
└── Bluetooth Monitor Thread (Linux)
```

### Logging Architecture
```text
Logging System
├── main_logger → logs/main.log (operational info)
├── debug_logger → logs/debug.log (technical details)
├── error_logger → logs/errors.log (problems)
├── network_logger → logs/network.log (connections)
└── nmea_logger → logs/nmea_data.log (data, rotating)
```

### Configuration System
```text
.env Configuration
├── SERVICE_MODE=False/True (background operation)
├── DEBUG=False/True (detailed logging)
├── SERIAL_PORT=AUTO (auto-detection)
├── UDP_MODE=server/client
├── TCP_MODE=server/client
└── Connection parameters (IPs, ports)
```

## 🔄 **Development Timeline**

### Phase 1: Core Features ✅
- **NMEA Parsing**: Complete GGA, RMC, GLL, VTG, HDT support
- **AIS Decoding**: AIVDM/AIVDO vessel tracking messages
- **Multi-protocol**: Serial, UDP, TCP simultaneous operation
- **Web Interface**: Real-time mapping with Leaflet.js

### Phase 2: Production Ready ✅
- **Service Mode**: Background operation with minimal logging
- **Logging Optimization**: Categorized logs for different use cases
- **Auto-detection**: Smart serial port discovery
- **Signal Handling**: Graceful shutdown and cleanup

### Phase 3: Platform Support ✅
- **Cross-platform**: Windows, Linux, macOS support
- **Build System**: Automated GitHub Actions CI/CD
- **Documentation**: Complete English translation
- **Error Handling**: Robust connection management

### Phase 4: Advanced Features (Planned)
- **Authentication**: User access control
- **Historical Data**: Long-term storage and visualization
- **REST API**: Third-party integration support
- **Mobile App**: Companion smartphone application

## 🎯 **Key Technical Achievements**

### Performance Optimizations
- **Efficient Threading**: All network connections as daemon threads
- **Rate Limiting**: NMEA message throttling to prevent spam
- **Memory Management**: Rotating logs with size limits
- **Connection Pooling**: Reusable network connections

### Reliability Features
- **Auto-recovery**: Automatic reconnection on connection loss
- **Error Isolation**: Individual thread failure doesn't crash server
- **Graceful Degradation**: Continues operation with partial failures
- **Health Monitoring**: Connection status tracking

### Security Enhancements
- **HTTPS Support**: SSL certificates with automatic fallback
- **Input Validation**: NMEA message format verification
- **Port Security**: Configurable binding to specific interfaces
- **Process Isolation**: Service mode runs independently

---

*Last updated: August 9, 2025*  
*Status: Production ready with optimized logging and service mode*  
*Next milestone: Advanced analytics and mobile integration*
