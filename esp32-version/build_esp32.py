# NMEA Tracker ESP32 - Build and Flash Script
# Automates the process of uploading files to ESP32

import os
import sys
import subprocess
import time

def run_command(cmd, check=True):
    """Run a shell command and return result"""
    print(f"🔄 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.returncode != 0 and check:
        print(f"❌ Error: {result.stderr}")
        return False
    
    if result.stdout:
        print(result.stdout)
    
    return True

def check_dependencies():
    """Check if required tools are installed"""
    print("📋 Checking dependencies...")
    
    tools = ['esptool.py', 'ampy']
    missing = []
    
    for tool in tools:
        result = subprocess.run(f"which {tool}", shell=True, capture_output=True)
        if result.returncode != 0:
            missing.append(tool)
    
    if missing:
        print(f"❌ Missing tools: {', '.join(missing)}")
        print("📦 Install with:")
        print("   pip install esptool adafruit-ampy")
        return False
    
    print("✅ All dependencies found")
    return True

def detect_port():
    """Detect ESP32 serial port"""
    print("🔍 Detecting ESP32 port...")
    
    import serial.tools.list_ports
    
    for port in serial.tools.list_ports.comports():
        if any(keyword in port.description.lower() for keyword in 
               ['cp210', 'ch340', 'esp32', 'silicon labs']):
            print(f"✅ Found ESP32 at: {port.device}")
            return port.device
    
    # Default ports to try
    default_ports = ['/dev/ttyUSB0', '/dev/ttyACM0', 'COM3', 'COM4', 'COM5']
    
    for port in default_ports:
        if os.path.exists(port) or port.startswith('COM'):
            print(f"🔍 Trying default port: {port}")
            return port
    
    print("❌ No ESP32 port detected")
    return None

def flash_firmware(port, firmware_path=None):
    """Flash MicroPython firmware to ESP32"""
    if not firmware_path:
        print("⚠️  No firmware specified, skipping flash")
        return True
    
    if not os.path.exists(firmware_path):
        print(f"❌ Firmware file not found: {firmware_path}")
        return False
    
    print("🔥 Flashing MicroPython firmware...")
    
    # Erase flash
    if not run_command(f"esptool.py --chip esp32 --port {port} erase_flash"):
        return False
    
    time.sleep(2)
    
    # Flash firmware
    if not run_command(f"esptool.py --chip esp32 --port {port} write_flash -z 0x1000 {firmware_path}"):
        return False
    
    print("✅ Firmware flashed successfully")
    time.sleep(3)  # Wait for ESP32 to boot
    return True

def upload_files(port):
    """Upload Python files to ESP32"""
    print("📁 Uploading files to ESP32...")
    
    files_to_upload = [
        'main.py',
        'config.py', 
        'boot.py'
    ]
    
    for filename in files_to_upload:
        if os.path.exists(filename):
            print(f"⬆️  Uploading {filename}...")
            if not run_command(f"ampy --port {port} put {filename}"):
                print(f"❌ Failed to upload {filename}")
                return False
            time.sleep(1)  # Small delay between uploads
        else:
            print(f"⚠️  File not found: {filename}")
    
    print("✅ All files uploaded successfully")
    return True

def reset_esp32(port):
    """Reset ESP32 to start the application"""
    print("🔄 Resetting ESP32...")
    run_command(f"ampy --port {port} reset", check=False)
    time.sleep(2)

def main():
    print("=" * 60)
    print("🛰️  NMEA Tracker ESP32 - Build & Flash Tool")
    print("=" * 60)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='ESP32 NMEA Tracker build tool')
    parser.add_argument('--port', help='Serial port (auto-detect if not specified)')
    parser.add_argument('--firmware', help='MicroPython firmware file to flash')
    parser.add_argument('--no-flash', action='store_true', help='Skip firmware flashing')
    parser.add_argument('--no-upload', action='store_true', help='Skip file upload')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Detect or use specified port
    port = args.port or detect_port()
    if not port:
        print("❌ No ESP32 port found. Specify with --port option")
        sys.exit(1)
    
    print(f"🔌 Using port: {port}")
    
    # Flash firmware if requested
    if not args.no_flash and args.firmware:
        if not flash_firmware(port, args.firmware):
            sys.exit(1)
    
    # Upload files
    if not args.no_upload:
        if not upload_files(port):
            sys.exit(1)
    
    # Reset ESP32
    reset_esp32(port)
    
    print("\n🎉 Build and flash completed successfully!")
    print("\n📡 Your ESP32 should now be running the NMEA Tracker")
    print("\n🔗 Next steps:")
    print("   1. Connect your GPS/AIS device to UART pins")
    print("   2. Connect to WiFi network: NMEA_Tracker_ESP32") 
    print("   3. Open browser: http://192.168.4.1")
    print("   4. Monitor serial output for debugging")

if __name__ == "__main__":
    main()
