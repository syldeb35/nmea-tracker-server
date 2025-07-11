# Boot script for NMEA Tracker ESP32
# This file runs automatically when the ESP32 starts up
# Copy this to your ESP32 as boot.py for auto-start functionality

import gc
import time
from machine import Pin

# Enable garbage collection
gc.enable()

# Status LED setup
led = Pin(2, Pin.OUT)

def blink_led(times, delay=0.2):
    """Blink the status LED"""
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()
        time.sleep(delay)

# Startup indication
print("\n" + "="*50)
print("🛰️  NMEA Tracker ESP32 - Boot Sequence")
print("="*50)

# Boot blink pattern
blink_led(3, 0.1)  # 3 quick blinks

# Import and run main application
try:
    print("[BOOT] Loading main application...")
    import main
    print("[BOOT] Application loaded successfully")
except ImportError as e:
    print(f"[BOOT] Error importing main: {e}")
    print("[BOOT] Make sure main.py is uploaded to the ESP32")
    blink_led(10, 0.1)  # Error indication
except Exception as e:
    print(f"[BOOT] Unexpected error: {e}")
    blink_led(5, 0.5)  # Error indication

print("[BOOT] Boot sequence completed")
