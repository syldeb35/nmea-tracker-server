# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['nmea_server.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates/config.html', 'templates'),
        ('templates/index.html', 'templates'),
        ('templates/favicon.svg', 'templates'),
        ('cert.pem', '.'),
        ('key.pem', '.'),
        ('.env', '.'),
    ],
    hiddenimports=[
        'gevent',
        'gevent.socket',
        'gevent.ssl',
        'gevent.pywsgi',
        'flask',
        'flask_socketio',
        'flask_cors',
        'serial',
        'serial.tools.list_ports',
        'engineio.async_drivers.gevent',
        'socketio',
        'pkg_resources.py2_warn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
