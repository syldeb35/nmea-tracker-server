#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NMEA Server System Tray Application
NMEA server management application from the system tray
"""

import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw
import pystray
from pystray import MenuItem as item
import webbrowser
import psutil
import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tray_app.log'),
        logging.StreamHandler()
    ]
)

class NMEAServerTray:
    def __init__(self):
        self.server_process = None
        self.server_running = False
        self.icon = None
        self.server_script = "nmea_server.py"
        self.server_executable = "nmea_tracker_server.exe"
        
        # Check if the executable exists, otherwise use the Python script
        if os.path.exists(self.server_executable):
            self.server_command = [self.server_executable]
        elif os.path.exists(self.server_script):
            self.server_command = [sys.executable, self.server_script]
        else:
            logging.error("Neither the executable nor the Python script were found!")
            messagebox.showerror("Error", "Unable to find the NMEA server!")
            sys.exit(1)
        
        # Create the logs folder if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        self.setup_icon()
        # Automatically start the server after tray icon setup
        self.start_server()
        
    def create_icon_image(self, is_running=False):
        """Creates a colored icon according to the server status"""
        try:
            # Try to load the custom icon as a base
            if os.path.exists("icon.png"):
                base_image = Image.open("icon.png").convert('RGBA')
                # Resize if necessary
                base_image = base_image.resize((64, 64), Image.Resampling.LANCZOS)
                
                # Apply a colored tint according to the status
                overlay = Image.new('RGBA', (64, 64), (0, 255, 0, 100) if is_running else (255, 0, 0, 100))
                image = Image.alpha_composite(base_image, overlay)
            else:
                # Create a simple colored icon
                color = (0, 200, 0, 255) if is_running else (200, 0, 0, 255)  # Green or Red
                image = Image.new('RGBA', (64, 64), color)
                
                # Add a darker circle in the center for better visibility
                draw = ImageDraw.Draw(image)
                center_color = (0, 150, 0, 255) if is_running else (150, 0, 0, 255)
                draw.ellipse([16, 16, 48, 48], fill=center_color)
                
            return image
            
        except Exception as e:
            logging.warning(f"Unable to create icon: {e}")
            # Fallback colored icon
            color = (0, 200, 0, 255) if is_running else (200, 0, 0, 255)
            return Image.new('RGBA', (64, 64), color)

    def setup_icon(self):
        """Configures the system tray icon"""
        # Create the initial icon (server stopped = red)
        image = self.create_icon_image(is_running=False)
        
        # Create the context menu
        menu = pystray.Menu(
            item('Start server', self.start_server, enabled=lambda item: not self.server_running),
            item('Stop server', self.stop_server, enabled=lambda item: self.server_running),
            pystray.Menu.SEPARATOR,
            item('Open web interface', self.open_web_interface, enabled=lambda item: self.server_running),
            item('Open configuration page', self.open_config_interface, enabled=lambda item: self.server_running),
            item('View logs', self.view_logs),
            pystray.Menu.SEPARATOR,
            item('About', self.show_about),
            item('Quit', self.quit_application)
        )
        
        # Create the system icon
        self.icon = pystray.Icon(
            "NMEA Server",
            image,
            "NMEA Tracker Server",
            menu
        )
        
    def update_icon_status(self, is_running):
        """Updates the icon color according to the server status"""
        try:
            if self.icon:
                new_image = self.create_icon_image(is_running)
                self.icon.icon = new_image
                # Also update the tooltip
                status_text = "Running" if is_running else "Stopped"
                self.icon.title = f"NMEA Tracker Server - {status_text}"
                logging.debug(f"Icon updated: {'Green' if is_running else 'Red'}")
        except Exception as e:
            logging.error(f"Error updating icon: {e}")
        
    def start_server(self, icon=None, item=None):
        """Starts the NMEA server"""
        if self.server_running:
            logging.info("The server is already running")
            return
            
        try:
            logging.info(f"Starting server: {' '.join(self.server_command)}")
            
            # Start the server in no-console mode (CREATE_NO_WINDOW on Windows)
            startupinfo = None
            creation_flags = 0
            
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                creation_flags = subprocess.CREATE_NO_WINDOW
            
            self.server_process = subprocess.Popen(
                self.server_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                creationflags=creation_flags,
                cwd=os.getcwd()
            )
            
            self.server_running = True
            logging.info(f"Server started with PID: {self.server_process.pid}")
            
            # Update the icon to green
            self.update_icon_status(True)
            
            # Start a thread to monitor the server
            threading.Thread(target=self.monitor_server, daemon=True).start()
            
            # Notification
            if self.icon:
                self.icon.notify("NMEA server started", "The server is now running")
                
        except Exception as e:
            logging.error(f"Error starting server: {e}")
            messagebox.showerror("Error", f"Unable to start the server:\n{e}")
            
    def stop_server(self, icon=None, item=None):
        """Stops the NMEA server"""
        if not self.server_running:
            logging.info("The server is not running")
            return
            
        try:
            logging.info("Stopping server...")
            
            if self.server_process:
                # Try to gracefully stop the process
                if sys.platform == "win32":
                    # On Windows, use terminate
                    self.server_process.terminate()
                else:
                    # On Unix, use SIGTERM
                    self.server_process.terminate()
                
                # Wait a bit for a clean shutdown
                try:
                    self.server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    # Force stop if necessary
                    logging.warning("Forced server stop")
                    self.server_process.kill()
                    self.server_process.wait()
                
                self.server_process = None
                
            # Also try to kill any remaining processes
            self.kill_remaining_processes()
            
            self.server_running = False
            logging.info("Server stopped")
            
            # Update the icon to red
            self.update_icon_status(False)
            
            # Notification
            if self.icon:
                self.icon.notify("NMEA server stopped", "The server has been stopped")
                
        except Exception as e:
            logging.error(f"Error stopping server: {e}")
            messagebox.showerror("Error", f"Error stopping the server:\n{e}")
            
    def kill_remaining_processes(self):
        """Kills any NMEA server processes that might still be running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    # Look for processes that match our server
                    if proc.info['cmdline']:
                        cmdline = ' '.join(proc.info['cmdline'])
                        if ('nmea_server.py' in cmdline or 
                            'nmea_tracker_server.exe' in cmdline):
                            logging.info(f"Stopping remaining process: PID {proc.info['pid']}")
                            proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception as e:
            logging.error(f"Error cleaning up processes: {e}")
            
    def monitor_server(self):
        """Monitors the server to detect if it stops unexpectedly"""
        while self.server_running and self.server_process:
            try:
                # Check if the process is still alive
                if self.server_process.poll() is not None:
                    logging.warning("The server stopped unexpectedly")
                    self.server_running = False
                    # Update the icon to red
                    self.update_icon_status(False)
                    if self.icon:
                        self.icon.notify("Server stopped", "The server stopped unexpectedly")
                    break
                    
                time.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logging.error(f"Error monitoring server: {e}")
                break
                
    def open_web_interface(self, icon=None, item=None):
        """Opens the server's web interface"""
        if not self.server_running:
            messagebox.showwarning("Server stopped", "The server must be running to open the web interface")
            return
            
        try:
            webbrowser.open('https://localhost:5000')
            logging.info("Web interface opened")
        except Exception as e:
            logging.error(f"Error opening web interface: {e}")
            messagebox.showerror("Error", f"Unable to open the web interface:\n{e}")
            
    def open_config_interface(self, icon=None, item=None):
        """Opens the server's web interface"""
        if not self.server_running:
            messagebox.showwarning("Server stopped", "The server must be running to open the web interface")
            return
            
        try:
            webbrowser.open('https://localhost:5000/config.html')
            logging.info("Web interface opened")
        except Exception as e:
            logging.error(f"Error opening web interface: {e}")
            messagebox.showerror("Error", f"Unable to open the web interface:\n{e}")
            
    def view_logs(self, icon=None, item=None):
        """Opens the logs folder"""
        try:
            if sys.platform == "win32":
                os.startfile(os.path.abspath('logs'))
            elif sys.platform == "darwin":
                subprocess.Popen(['open', os.path.abspath('logs')])
            else:
                subprocess.Popen(['xdg-open', os.path.abspath('logs')])
        except Exception as e:
            logging.error(f"Error opening logs folder: {e}")
            
    def show_about(self, icon=None, item=None):
        """Shows information about the application"""
        messagebox.showinfo(
            "About",
            "NMEA Tracker Server - System Tray\n\n"
            "Manager for the NMEA server from the system tray.\n"
            "Allows you to start/stop the server and access the web interface.\n\n"
            "Version: 1.0"
        )
        
    def quit_application(self, icon=None, item=None):
        """Quits the application"""
        if self.server_running:
            if messagebox.askyesno("Confirmation", "The server is running. Do you want to stop it and quit?"):
                self.stop_server()
            else:
                return
                
        logging.info("Tray application closing")
        if self.icon:
            self.icon.stop()
        sys.exit(0)
        
    def run(self):
        """Runs the system tray application"""
        logging.info("Starting NMEA Server Tray application")
        try:
            self.icon.run()
        except KeyboardInterrupt:
            self.quit_application()

def main():
    """Main entry point"""
    try:
        app = NMEAServerTray()
        app.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        messagebox.showerror("Fatal error", f"A fatal error occurred:\n{e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
