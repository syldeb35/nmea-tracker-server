# -*- mode: python ; coding: utf-8 -*-

import sys
import os

IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform.startswith('darwin')

if IS_WINDOWS:
    icon_file = 'icon.ico'
elif IS_MACOS:
    icon_file = 'icon.icns'
else:
    icon_file = None

a = Analysis(
    ['gui_config.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('cert.pem', '.'),
        ('key.pem', '.'),
        ('.env', '.'),
        ('icon.svg', '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui', 
        'PyQt6.QtWidgets',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'flask',
        'flask_socketio',
        'flask_cors',
        'gevent',
        'gevent.pywsgi',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='NMEA_Server_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=icon_file,
)

if IS_MACOS:
    app = BUNDLE(
        exe,
        name='NMEA Server GUI.app',
        icon=icon_file,
        bundle_identifier='com.nmea.server.gui',
    )
