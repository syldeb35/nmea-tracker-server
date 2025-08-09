# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

block_cipher = None

# Fonction pour vérifier et ajouter des fichiers optionnels
def add_optional_file(file_path, dest_dir):
    """Ajoute un fichier seulement s'il existe"""
    if os.path.exists(file_path):
        return (file_path, dest_dir)
    else:
        print(f"⚠️  Fichier optionnel manquant: {file_path}")
        return None

# Liste des fichiers de données avec vérification
datas = [
    ('templates/config.html', 'templates'),
    ('templates/index.html', 'templates'),
    ('templates/favicon.svg', 'templates'),
]

# Ajout des fichiers optionnels
optional_files = [
    ('cert.pem', '.'),
    ('key.pem', '.'),
    ('.env', '.'),
]

for file_path, dest_dir in optional_files:
    optional_file = add_optional_file(file_path, dest_dir)
    if optional_file:
        datas.append(optional_file)

a = Analysis(
    ['nmea_server_test.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core Flask et extensions
        'gevent',
        'gevent.socket',
        'gevent.ssl',
        'gevent.pywsgi',
        'gevent.monkey',
        'gevent._util',
        'gevent.greenlet',
        'flask',
        'flask_socketio',
        'flask_cors',
        
        # SocketIO et EngineIO complets
        'socketio',
        'socketio.server',
        'socketio.namespace',
        'socketio.packet',
        'socketio.pubsub_manager',
        'engineio',
        'engineio.server',
        'engineio.socket',
        'engineio.packet',
        'engineio.async_drivers.gevent',
        'engineio.async_gevent',
        
        # Serial et ports
        'serial',
        'serial.tools.list_ports',
        'serial.serialutil',
        
        # Bluetooth et subprocess pour Linux
        'subprocess',
        'subprocess.run',
        
        # Modules système
        'pkg_resources.py2_warn',
        'dotenv',
        'logging.handlers',
        'platform',
        'ssl',
        'socket',
        'threading',
        'time',
        'os',
        'sys',
        're',
        'json',
        'datetime',
        'math',
        'base64',
        'hashlib',
        'urllib',
        'urllib.parse',
        'urllib3',
        'urllib3.exceptions',
        
        # Modules cryptography pour SSL/TLS
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.asymmetric',
        'cryptography.hazmat.primitives.asymmetric.rsa',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.serialization',
        'cryptography.x509',
        'cryptography.x509.oid',
        'cffi',
        
        # Modules supplémentaires pour Flask-SocketIO
        'dns',
        'dns.resolver',
        'dns.exception',
        'eventlet',
        'eventlet.wsgi',
        'eventlet.green',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.security',
        'jinja2',
        'jinja2.ext',
        'markupsafe',
        
        # Importations implicites détectées
        'importlib',
        'importlib.util',
        'importlib.metadata',
        'collections',
        'collections.abc',
        'queue',
        'functools',
        'inspect',
        'warnings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'PIL',
        'cv2',
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
    name='nmea_tracker_server2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # RESTORED: Silent background execution for system tray
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Icône personnalisée de l'application
)
