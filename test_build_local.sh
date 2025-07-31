#!/bin/bash

echo "🧪 Testing build process locally..."

# Install dependencies
pip install PyQt6 pyserial flask flask-socketio flask-cors gevent python-dotenv Pillow pyinstaller

# Create missing files
cat > requirements_gui.txt << 'INNER_EOF'
PyQt6>=6.0.0
pyserial>=3.5
INNER_EOF

cat > start_gui.sh << 'INNER_EOF'
#!/bin/bash
echo "🚀 Starting NMEA Server GUI..."
if [ -f "gui_config.py" ]; then
    echo "Starting Qt GUI..."
    python gui_config.py
else
    echo "❌ gui_config.py not found"
    echo "Starting web interface instead..."
    python nmea_server.py
fi
INNER_EOF
chmod +x start_gui.sh

cat > .env << 'INNER_EOF'
ENABLE_SERIAL=true
ENABLE_UDP=true
ENABLE_TCP=true
DEBUG=false
UDP_IP=0.0.0.0
UDP_PORT=5005
TCP_IP=0.0.0.0
TCP_PORT=5006
SERIAL_PORT=/dev/ttyUSB0
SERIAL_BAUDRATE=4800
INNER_EOF

# Create icons
python -c "
from PIL import Image, ImageDraw
import os

def create_icon(size, filename, format_name):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    bg_color = (25, 118, 210, 255)
    fg_color = (255, 255, 255, 255)
    
    margin = size // 16
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=bg_color, outline=fg_color, width=max(1, size//64))
    
    center = size // 2
    needle_size = size // 8
    draw.polygon([
        (center, center - needle_size),
        (center + needle_size//3, center),
        (center, center - needle_size//4),
        (center - needle_size//3, center),
    ], fill=fg_color)
    
    y = center + needle_size//2
    draw.line([size//4, y, 3*size//4, y], fill=fg_color, width=max(1, size//32))
    
    img.save(filename, format_name)
    return img

create_icon(512, 'icon.png', 'PNG')
img = create_icon(256, 'temp.png', 'PNG')
img.save('icon.ico', 'ICO', sizes=[(16,16), (32,32), (64,64), (128,128), (256,256)])
os.remove('temp.png')
print('✅ Icons created')
"

# Test builds
echo "🔧 Testing server build..."
python -m PyInstaller --onefile --name "nmea_tracker_server" nmea_server.py

echo "🖥️ Testing GUI build..."
python -m PyInstaller --onefile --windowed --name "NMEA_Server_GUI" --icon "icon.png" --hidden-import "PyQt6" gui_config.py

echo "📋 Build results:"
ls -la dist/

echo "✅ Local test completed!"
