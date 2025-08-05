# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for NMEA Tracker Server - System Tray Version
Crée un exécutable Windows qui fonctionne en arrière-plan avec icône système
"""

import os
import sys

# Configuration de base
block_cipher = None
app_name = 'nmea_tracker_tray'

# Répertoire de travail (où se trouve ce fichier .spec)
work_dir = os.path.dirname(os.path.abspath(SPEC))

# Script principal
main_script = os.path.join(work_dir, 'nmea_server_tray.py')

# Données à inclure (templates, certificats, etc.)
datas = [
    (os.path.join(work_dir, 'templates'), 'templates'),
    (os.path.join(work_dir, 'cert.pem'), '.'),
    (os.path.join(work_dir, 'key.pem'), '.'),
    (os.path.join(work_dir, 'icon.ico'), '.'),
    (os.path.join(work_dir, 'nmea_server_fallback.py'), '.'),  # Inclure le serveur fallback
]

# Modules cachés nécessaires
hiddenimports = [
    'flask',
    'flask_socketio', 
    'socketio',
    'eventlet',
    'eventlet.wsgi',
    'dns',
    'dns.resolver',
    'gevent',
    'gevent.socket',
    'gevent._socket3',
    'serial',
    'serial.tools.list_ports',
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'cryptography',
    'cryptography.hazmat.primitives.serialization',
    'cryptography.hazmat.primitives.asymmetric.rsa',
    'cryptography.x509',
    'nmea_server_fallback',  # Inclure le module fallback
]

# Binaires à exclure (pour réduire la taille)
excludes = [
    'tkinter',
    'matplotlib',
    'numpy',
    'pandas',
    'scipy',
    'pytest',
    'IPython',
    'jupyter',
]

a = Analysis(
    [main_script],
    pathex=[work_dir],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console visible - application en arrière-plan
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(work_dir, 'icon.ico') if os.path.exists(os.path.join(work_dir, 'icon.ico')) else None,
    version_file=None,
)
