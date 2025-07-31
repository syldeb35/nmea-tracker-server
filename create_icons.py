#!/usr/bin/env python3
from PIL import Image, ImageDraw
import os

def create_simple_icon(size, format_name, filename):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Couleurs
    bg_color = (25, 118, 210, 255)  # Bleu
    fg_color = (255, 255, 255, 255)  # Blanc
    
    # Cercle de fond
    margin = size // 16
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=bg_color, outline=fg_color, width=size//64)
    
    # Boussole simple
    center = size // 2
    needle_size = size // 8
    draw.polygon([
        (center, center - needle_size),
        (center + needle_size//3, center),
        (center, center - needle_size//4),
        (center - needle_size//3, center),
    ], fill=fg_color)
    
    # Horizon
    y = center + needle_size//2
    draw.line([size//4, y, 3*size//4, y], fill=fg_color, width=size//32)
    
    img.save(filename, format_name)
    print(f"✅ Created {filename}")

if __name__ == "__main__":
    try:
        # Créer PNG
        create_simple_icon(512, "PNG", "icon.png")
        
        # Créer ICO pour Windows
        img = Image.open("icon.png")
        img.save("icon.ico", "ICO", sizes=[(16,16), (32,32), (64,64), (128,128), (256,256)])
        print("✅ Created icon.ico")
        
        # Créer ICNS pour macOS (basique)
        try:
            img.save("icon.icns", "ICNS")
            print("✅ Created icon.icns")
        except:
            print("⚠️ ICNS not supported, will create on macOS")
            
    except ImportError:
        print("❌ Pillow not installed. Run: pip install Pillow")
