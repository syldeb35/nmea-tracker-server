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
    ('icon.png', '.'),
    ('icon.ico', '.'),
    ('icon.svg', '.'),
]

# Ajout des fichiers optionnels
optional_files = [
    ('nmea_tracker_server2.exe', '.'),
    ('nmea_server_test.py', '.'),
]

for file_path, dest_dir in optional_files:
    optional_file = add_optional_file(file_path, dest_dir)
    if optional_file:
        datas.append(optional_file)

a = Analysis(
    ['nmea_server_manager.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Core GUI (tkinter est inclus avec Python standard)
        'tkinter',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        'tkinter.filedialog',
        'tkinter.ttk',
        
        # Process management (modules standard)
        'subprocess',
        'threading',
        'time',
        'webbrowser',
        
        # System modules (standard)
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
        'pathlib',
        're',
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
        'PIL',
        'pystray',
        'psutil',
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
    name='nmea_server_manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Mode sans console pour l'interface graphique
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Icône personnalisée de l'application
)
