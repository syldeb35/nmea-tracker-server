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
    ['nmea_server.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'gevent',
        'gevent.socket',
        'gevent.ssl',
        'gevent.pywsgi',
        'gevent.monkey',
        'flask',
        'flask_socketio',
        'flask_cors',
        'serial',
        'serial.tools.list_ports',
        'engineio.async_drivers.gevent',
        'socketio',
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
    name='nmea_tracker_server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Icône personnalisée de l'application
)
