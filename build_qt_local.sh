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
