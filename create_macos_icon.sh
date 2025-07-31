#!/bin/bash

echo "🍎 Creating macOS .icns icon..."

# Check if we have the SVG icon
if [ ! -f "icon.svg" ]; then
    echo "❌ icon.svg not found. Creating a basic one..."
    # Create a basic SVG if missing
    cat > icon.svg << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1976d2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1256a3;stop-opacity:1" />
    </linearGradient>
  </defs>
  <circle cx="256" cy="256" r="240" fill="url(#grad1)" stroke="#fff" stroke-width="8"/>
  <path d="M256 96 L320 224 L256 192 L192 224 Z" fill="#fff"/>
  <path d="M128 288 L384 288" stroke="#fff" stroke-width="16" stroke-linecap="round"/>
  <path d="M160 352 L352 352" stroke="#fff" stroke-width="12" stroke-linecap="round"/>
  <circle cx="256" cy="416" r="24" fill="#fff"/>
</svg>
EOF
fi

# Check if we have tools to convert SVG
if command -v rsvg-convert >/dev/null 2>&1; then
    CONVERTER="rsvg-convert"
elif command -v inkscape >/dev/null 2>&1; then
    CONVERTER="inkscape"
elif command -v convert >/dev/null 2>&1; then
    CONVERTER="imagemagick"
else
    echo "❌ No SVG converter found. Please install one of: rsvg-convert, inkscape, or imagemagick"
    echo "   brew install librsvg"
    echo "   brew install inkscape"
    echo "   brew install imagemagick"
    exit 1
fi

# Create iconset directory
ICONSET_DIR="icon.iconset"
rm -rf "$ICONSET_DIR"
mkdir "$ICONSET_DIR"

echo "📐 Converting SVG to multiple PNG sizes..."

# Function to convert SVG to PNG
convert_svg() {
    local size=$1
    local output=$2
    
    case $CONVERTER in
        "rsvg-convert")
            rsvg-convert -w $size -h $size icon.svg -o "$output"
            ;;
        "inkscape")
            inkscape icon.svg -w $size -h $size -o "$output" 2>/dev/null
            ;;
        "imagemagick")
            convert -background none icon.svg -resize ${size}x${size} "$output"
            ;;
    esac
}

# Generate all required sizes for macOS
echo "  • 16x16..."
convert_svg 16 "$ICONSET_DIR/icon_16x16.png"
convert_svg 32 "$ICONSET_DIR/icon_16x16@2x.png"

echo "  • 32x32..."
convert_svg 32 "$ICONSET_DIR/icon_32x32.png"
convert_svg 64 "$ICONSET_DIR/icon_32x32@2x.png"

echo "  • 128x128..."
convert_svg 128 "$ICONSET_DIR/icon_128x128.png"
convert_svg 256 "$ICONSET_DIR/icon_128x128@2x.png"

echo "  • 256x256..."
convert_svg 256 "$ICONSET_DIR/icon_256x256.png"
convert_svg 512 "$ICONSET_DIR/icon_256x256@2x.png"

echo "  • 512x512..."
convert_svg 512 "$ICONSET_DIR/icon_512x512.png"
convert_svg 1024 "$ICONSET_DIR/icon_512x512@2x.png"

# Verify all files were created
echo "📋 Verifying generated files..."
ls -la "$ICONSET_DIR/"

# Create .icns file
if command -v iconutil >/dev/null 2>&1; then
    echo "🔨 Creating .icns file..."
    iconutil -c icns "$ICONSET_DIR" -o icon.icns
    
    if [ -f "icon.icns" ]; then
        echo "✅ Successfully created icon.icns"
        echo "📊 File size: $(du -h icon.icns | cut -f1)"
        
        # Clean up iconset directory
        rm -rf "$ICONSET_DIR"
        
        echo "🎉 macOS icon creation completed!"
        echo "📁 Generated: icon.icns"
    else
        echo "❌ Failed to create icon.icns"
        exit 1
    fi
else
    echo "❌ iconutil not found. This script must be run on macOS to create .icns files."
    echo "📁 PNG files created in: $ICONSET_DIR/"
    echo "💡 You can manually create the .icns file with: iconutil -c icns $ICONSET_DIR"
    exit 1
fi
