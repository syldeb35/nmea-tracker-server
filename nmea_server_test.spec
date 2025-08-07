# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['nmea_server_test.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('cert.pem', '.'),
        ('key.pem', '.'),
        ('icon.ico', '.'),
        ('icon.png', '.'),
    ],
    hiddenimports=[
        # Gevent - moteur asynchrone principal
        'gevent',
        'gevent.socket',
        'gevent.select',
        'gevent.threading',
        'gevent.time',
        'gevent.queue',
        'gevent.pool',
        'gevent.event',
        'gevent.pywsgi',
        'gevent.monkey',
        'gevent._util',
        'gevent.greenlet',
        'gevent.subprocess',
        
        # Flask et extensions
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
        
        # System tray support
        'pystray',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'tkinter',
        'tkinter.messagebox',
        'tkinter.simpledialog',
        
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
        'ipaddress',
        'warnings',
        
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
        
        # Importations implicites
        'importlib',
        'importlib.util',
        'importlib.metadata',
        'collections',
        'collections.abc',
        'queue',
        'functools',
        'inspect',
        'webbrowser',
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
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
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
    name='nmea_tracker_server_enhanced',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True = console mode par défaut
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
