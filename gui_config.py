import sys
import os
import json
import subprocess
import platform
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QWidget, QLabel, QLineEdit, QSpinBox, QCheckBox, 
                             QPushButton, QGroupBox, QComboBox, QTextEdit, 
                             QTabWidget, QMessageBox, QStatusBar, QGridLayout,
                             QSplitter, QFrame)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor

class NMEAServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_process = None
        self.config_file = ".env"
        self.init_ui()
        self.load_config()
        self.setup_status_timer()
        
    def init_ui(self):
        self.setWindowTitle("NMEA Server Configuration")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget avec splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Panel de configuration (gauche)
        config_panel = self.create_config_panel()
        splitter.addWidget(config_panel)
        
        # Panel de logs (droite)
        log_panel = self.create_log_panel()
        splitter.addWidget(log_panel)
        
        # Ratio 60/40
        splitter.setSizes([480, 320])
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Server stopped")
        
    def create_config_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # === CONNECTION TYPES ===
        conn_group = QGroupBox("Connection Types")
        conn_layout = QVBoxLayout(conn_group)
        
        self.enable_serial = QCheckBox("Serial Connection")
        self.enable_udp = QCheckBox("UDP Connection") 
        self.enable_tcp = QCheckBox("TCP Connection")
        self.enable_debug = QCheckBox("Enable Debug Logging")
        
        conn_layout.addWidget(self.enable_serial)
        conn_layout.addWidget(self.enable_udp)
        conn_layout.addWidget(self.enable_tcp)
        conn_layout.addWidget(self.enable_debug)
        
        layout.addWidget(conn_group)
        
        # === NETWORK SETTINGS ===
        net_group = QGroupBox("Network Settings")
        net_layout = QGridLayout(net_group)
        
        # UDP
        net_layout.addWidget(QLabel("UDP IP:"), 0, 0)
        self.udp_ip = QLineEdit("0.0.0.0")
        net_layout.addWidget(self.udp_ip, 0, 1)
        
        net_layout.addWidget(QLabel("UDP Port:"), 0, 2)
        self.udp_port = QSpinBox()
        self.udp_port.setRange(1024, 65535)
        self.udp_port.setValue(5005)
        net_layout.addWidget(self.udp_port, 0, 3)
        
        # TCP
        net_layout.addWidget(QLabel("TCP IP:"), 1, 0)
        self.tcp_ip = QLineEdit("0.0.0.0")
        net_layout.addWidget(self.tcp_ip, 1, 1)
        
        net_layout.addWidget(QLabel("TCP Port:"), 1, 2)
        self.tcp_port = QSpinBox()
        self.tcp_port.setRange(1024, 65535)
        self.tcp_port.setValue(5006)
        net_layout.addWidget(self.tcp_port, 1, 3)
        
        layout.addWidget(net_group)
        
        # === SERIAL SETTINGS ===
        serial_group = QGroupBox("Serial Settings")
        serial_layout = QGridLayout(serial_group)
        
        serial_layout.addWidget(QLabel("Serial Port:"), 0, 0)
        self.serial_port = QComboBox()
        self.populate_serial_ports()
        serial_layout.addWidget(self.serial_port, 0, 1)
        
        serial_layout.addWidget(QLabel("Baud Rate:"), 1, 0)
        self.serial_baudrate = QComboBox()
        self.serial_baudrate.addItems(["4800", "9600", "19200", "38400", "57600", "115200"])
        self.serial_baudrate.setCurrentText("4800")
        serial_layout.addWidget(self.serial_baudrate, 1, 1)
        
        layout.addWidget(serial_group)
        
        # === BLUETOOTH AUTO INFO ===
        bt_info = QFrame()
        bt_info.setFrameStyle(QFrame.Shape.Box)
        bt_info.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 5px;")
        bt_layout = QVBoxLayout(bt_info)
        
        bt_title = QLabel("🔵 AUTO Mode (Linux)")
        bt_title.setFont(QFont("", 0, QFont.Weight.Bold))
        bt_layout.addWidget(bt_title)
        
        bt_desc = QLabel("• Automatically discovers GPS devices via Bluetooth scan\n"
                        "• Creates rfcomm connection automatically\n"
                        "• Reconnects automatically if connection is lost\n"
                        "• No manual sdptool/rfcomm commands needed")
        bt_desc.setWordWrap(True)
        bt_layout.addWidget(bt_desc)
        
        layout.addWidget(bt_info)
        
        # === CONTROL BUTTONS ===
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white; padding: 8px;")
        
        self.apply_button = QPushButton("Apply Config")
        self.apply_button.clicked.connect(self.apply_config)
        self.apply_button.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.apply_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget
        
    def create_log_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("Server Logs:"))
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Log controls
        log_controls = QHBoxLayout()
        
        clear_logs = QPushButton("Clear Logs")
        clear_logs.clicked.connect(self.log_text.clear)
        
        open_web = QPushButton("Open Web Interface")
        open_web.clicked.connect(self.open_web_interface)
        
        log_controls.addWidget(clear_logs)
        log_controls.addWidget(open_web)
        log_controls.addStretch()
        
        layout.addLayout(log_controls)
        
        return widget
        
    def populate_serial_ports(self):
        """Detect available serial ports"""
        self.serial_port.clear()
        
        # Add AUTO option for Linux
        if platform.system() == "Linux":
            self.serial_port.addItem("AUTO - Bluetooth GPS Auto-Discovery")
        
        # Detect serial ports
        try:
            import serial.tools.list_ports
            ports = serial.tools.list_ports.comports()
            for port in ports:
                self.serial_port.addItem(f"{port.device} - {port.description}")
        except ImportError:
            # Fallback for common ports
            if platform.system() == "Windows":
                for i in range(1, 21):
                    self.serial_port.addItem(f"COM{i}")
            else:
                common_ports = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", 
                               "/dev/ttyACM1", "/dev/rfcomm0", "/dev/rfcomm1"]
                for port in common_ports:
                    if os.path.exists(port):
                        self.serial_port.addItem(port)
    
    def load_config(self):
        """Load configuration from .env file"""
        if not os.path.exists(self.config_file):
            return
            
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if key == "ENABLE_SERIAL":
                            self.enable_serial.setChecked(value.lower() == "true")
                        elif key == "ENABLE_UDP":
                            self.enable_udp.setChecked(value.lower() == "true")
                        elif key == "ENABLE_TCP":
                            self.enable_tcp.setChecked(value.lower() == "true")
                        elif key == "DEBUG":
                            self.enable_debug.setChecked(value.lower() == "true")
                        elif key == "UDP_IP":
                            self.udp_ip.setText(value)
                        elif key == "UDP_PORT":
                            try:
                                self.udp_port.setValue(int(value))
                            except ValueError:
                                self.udp_port.setValue(0)  # Set default value or handle error
                                print(f"Error parsing configuration for key 'UDP_PORT': Invalid value '{value}'")  # Enhanced logging
                        elif key == "TCP_IP":
                            self.tcp_ip.setText(value)
                        elif key == "TCP_PORT":
                            try:
                                self.tcp_port.setValue(int(value))
                            except ValueError:
                                self.tcp_port.setValue(0)  # Set default value or handle error
                                print(f"Invalid TCP_PORT value: {value}. Key: TCP_PORT")  # Clearer debugging
                        elif key == "SERIAL_PORT":
                            # Find and select the port
                            for i in range(self.serial_port.count()):
                                if value in self.serial_port.itemText(i) or value == "AUTO":
                                    self.serial_port.setCurrentIndex(i)
                                    break
                        elif key == "SERIAL_BAUDRATE":
                            self.serial_baudrate.setCurrentText(value)
        except Exception as e:
            QMessageBox.warning(self, "Config Error", f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to .env file"""
        try:
            config_lines = [
                f'ENABLE_SERIAL={"true" if self.enable_serial.isChecked() else "false"}',
                f'ENABLE_UDP={"true" if self.enable_udp.isChecked() else "false"}',
                f'ENABLE_TCP={"true" if self.enable_tcp.isChecked() else "false"}',
                f'DEBUG={"true" if self.enable_debug.isChecked() else "false"}',
                f'UDP_IP={self.udp_ip.text()}',
                f'UDP_PORT={self.udp_port.value()}',
                f'TCP_IP={self.tcp_ip.text()}',
                f'TCP_PORT={self.tcp_port.value()}',
                f'SERIAL_PORT={"AUTO" if "AUTO" in self.serial_port.currentText() else self.serial_port.currentText().split(" - ")[0]}',
                f'SERIAL_BAUDRATE={self.serial_baudrate.currentText()}'
            ]
            
            with open(self.config_file, 'w') as f:
                f.write('\n'.join(config_lines))
                
            self.status_bar.showMessage("Configuration saved", 2000)
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Error saving config: {e}")
    
    def apply_config(self):
        """Apply configuration and restart server if running"""
        self.save_config()
        if self.server_process and self.server_process.state() == QProcess.ProcessState.Running:
            reply = QMessageBox.question(self, "Restart Server", 
                                       "Server is running. Restart with new configuration?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_server()
                QTimer.singleShot(1000, self.start_server)  # Wait 1s before restart
    
    def start_server(self):
        """Start the NMEA server"""
        if self.server_process and self.server_process.state() == QProcess.ProcessState.Running:
            return
            
        self.save_config()
        
        # Setup process
        self.server_process = QProcess()
        self.server_process.readyReadStandardOutput.connect(self.read_output)
        self.server_process.readyReadStandardError.connect(self.read_error)
        self.server_process.finished.connect(self.server_finished)
        
        # Start server
        python_cmd = sys.executable
        self.server_process.start(python_cmd, ["nmea_server.py"])
        
        if self.server_process.waitForStarted():
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.status_bar.showMessage("Server starting...")
            self.log_text.append("[GUI] Starting NMEA server...")
        else:
            QMessageBox.critical(self, "Start Error", "Failed to start server")
    
    def stop_server(self):
        """Stop the NMEA server"""
        if self.server_process:
            self.server_process.terminate()
            if not self.server_process.waitForFinished(3000):
                self.server_process.kill()
    
    def server_finished(self):
        """Handle server process finished"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_bar.showMessage("Server stopped")
        self.log_text.append("[GUI] Server stopped")
    
    def read_output(self):
        """Read and display server output"""
        data = self.server_process.readAllStandardOutput()
        text = bytes(data).decode('utf-8')
        self.log_text.append(text.strip())
        self.log_text.ensureCursorVisible()
    
    def read_error(self):
        """Read and display server errors"""
        data = self.server_process.readAllStandardError()
        text = bytes(data).decode('utf-8')
        self.log_text.append(f"[ERROR] {text.strip()}")
        self.log_text.ensureCursorVisible()
    
    def setup_status_timer(self):
        """Setup timer to check server status"""
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_server_status)
        self.status_timer.start(2000)  # Check every 2 seconds
    
    def check_server_status(self):
        """Check if server is running and update status"""
        if self.server_process and self.server_process.state() == QProcess.ProcessState.Running:
            server_protocol = os.getenv("SERVER_PROTOCOL", "https")
            server_host = os.getenv("SERVER_HOST", "localhost")
            server_port = os.getenv("SERVER_PORT", "5000")
            self.status_bar.showMessage(f"Server running - {server_protocol}://{server_host}:{server_port}")
        elif self.start_button.isEnabled():
            self.status_bar.showMessage("Server stopped")
    
    def open_web_interface(self):
        """Open web interface in default browser"""
        import webbrowser
        server_protocol = os.getenv("SERVER_PROTOCOL", "https")
        server_host = os.getenv("SERVER_HOST", "localhost")
        server_port = os.getenv("SERVER_PORT", "5000")
        webbrowser.open(f"{server_protocol}://{server_host}:{server_port}/config.html")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.server_process and self.server_process.state() == QProcess.ProcessState.Running:
            reply = QMessageBox.question(self, "Close Application",
                                       "Server is running. Stop server and close?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.stop_server()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Dark theme (optionnel)
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    # app.setPalette(palette)  # Uncomment for dark theme
    
    window = NMEAServerGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()