# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Function to check and add optional files
def add_optional_file(file_path, dest_dir):
    """Add a file only if it exists"""
    if os.path.exists(file_path):
        return (file_path, dest_dir)
    else:
        print(f"Optional file missing: {file_path}")
        return None

# Data files list with verification
datas = [
    ('icon.png', '.'),
    ('icon.ico', '.'),
    ('icon.svg', '.'),
]

# Optional files addition
optional_files = [
    ('nmea_tracker_server.exe', '.'),
    ('nmea_server.py', '.'),
]

for file_path, dest_dir in optional_files:
    optional_file = add_optional_file(file_path, dest_dir)
    if optional_file:
        datas.append(optional_file)

a = Analysis(
    ['nmea_server_tray.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core GUI and system tray
        'tkinter',
        'tkinter.messagebox',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pystray',
        'pystray._base',
        'pystray._win32',
        'pystray._util',
        
        # Process management
        'psutil',
        'psutil._psutil_windows',
        'subprocess',
        'threading',
        'time',
        'webbrowser',
        
        # System modules
        'os',
        'sys',
        'logging',
        'logging.handlers',
        'platform',
        'signal',
        'atexit',
        
        # Standard library
        'json',
        'datetime',
        'collections',
        'functools',
        'inspect',
        'warnings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'cv2',
        'flask',
        'flask_socketio',
        'gevent',
        'serial',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='nmea_server_tray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console mode for system tray
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Custom application icon
)
