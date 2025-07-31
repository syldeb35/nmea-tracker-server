#!/bin/bash

echo "🚀 Setting up Qt GUI files..."

# Créer create_icns_cross_platform.py
cat > create_icns_cross_platform.py << 'EOF'
#!/usr/bin/env python3
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("❌ Pillow not installed. Install with: pip install Pillow")
    print("Installing Pillow...")
    os.system("pip install Pillow")
    from PIL import Image, ImageDraw

def create_nmea_icon(size):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    bg_color = (25, 118, 210, 255)
    fg_color = (255, 255, 255, 255)
    s = size / 512.0
    
    margin = int(16 * s)
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=bg_color, outline=fg_color, width=int(4*s))
    
    center_x, center_y = size // 2, size // 2
    needle_size = int(64 * s)
    needle_points = [
        (center_x, center_y - needle_size),
        (center_x + int(24*s), center_y),
        (center_x, center_y - int(8*s)),
        (center_x - int(24*s), center_y),
    ]
    draw.polygon(needle_points, fill=fg_color)
    
    y1 = center_y + int(32 * s)
    y2 = center_y + int(64 * s)
    
    draw.line([int(64*s), y1, size-int(64*s), y1], 
             fill=fg_color, width=int(8*s))
    draw.line([int(96*s), y2, size-int(96*s), y2], 
             fill=fg_color, width=int(6*s))
    
    dot_size = int(12 * s)
    draw.ellipse([center_x-dot_size, center_y+int(96*s)-dot_size,
                 center_x+dot_size, center_y+int(96*s)+dot_size], 
                fill=fg_color)
    
    return img

def create_icns_file():
    print("🍎 Creating macOS .icns icon (cross-platform)...")
    
    sizes = [16, 32, 64, 128, 256, 512, 1024]
    iconset_dir = Path("icon.iconset")
    iconset_dir.mkdir(exist_ok=True)
    
    print("📐 Generating PNG files...")
    for size in sizes:
        print(f"  • {size}x{size}...")
        img = create_nmea_icon(size)
        
        if size <= 512:
            filename = f"icon_{size}x{size}.png"
            img.save(iconset_dir / filename, "PNG")
        
        if size >= 32 and size <= 512:
            retina_size = size // 2
            filename = f"icon_{retina_size}x{retina_size}@2x.png"
            img.save(iconset_dir / filename, "PNG")
    
    try:
        base_img = create_nmea_icon(512)
        base_img.save("icon.icns", "ICNS")
        print("✅ Successfully created icon.icns using Pillow")
    except Exception as e:
        print(f"⚠️  Could not create .icns with Pillow: {e}")
        print("📁 PNG files created in: icon.iconset/")
    
    print("🎉 Icon creation completed!")

if __name__ == "__main__":
    create_icns_file()
EOF

chmod +x create_icns_cross_platform.py

echo "✅ Created create_icns_cross_platform.py"

# Créer gui_config.spec
cat > gui_config.spec << 'EOF'
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
EOF

echo "✅ Created gui_config.spec"

# Créer build_qt_local.sh
cat > build_qt_local.sh << 'EOF'
#!/bin/bash

echo "🏗️ Building Qt GUI Application locally..."

pip install -r requirements.txt
pip install -r requirements_gui.txt
pip install pyinstaller

rm -rf build/ dist/

echo "🔧 Building NMEA Server..."
pyinstaller nmea_server.spec --clean --noconfirm

echo "🖥️ Building Qt GUI..."
pyinstaller gui_config.spec --clean --noconfirm

echo "✅ Build completed!"
ls -la dist/
EOF

chmod +x build_qt_local.sh

echo "✅ Created build_qt_local.sh"

echo ""
echo "🎉 All Qt GUI files created successfully!"
echo "📋 Created files:"
ls -la create_icns_cross_platform.py gui_config.spec build_qt_local.sh

echo ""
echo "🚀 Next steps:"
echo "1. Test icon creation: python create_icns_cross_platform.py"
echo "2. Test build: ./build_qt_local.sh"
