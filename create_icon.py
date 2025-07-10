#!/usr/bin/env python3
"""
Script pour convertir l'icône SVG en fichier ICO multi-résolution pour Windows
"""

import os
from PIL import Image
import cairosvg
from io import BytesIO

def svg_to_ico(svg_path, ico_path):
    """Convertit un fichier SVG en fichier ICO multi-résolution"""
    
    # Tailles d'icônes Windows standard
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []
    
    print(f"🎨 Conversion de {svg_path} vers {ico_path}")
    
    for size in sizes:
        print(f"  📐 Génération taille {size}x{size}...")
        
        # Convertir SVG en PNG en mémoire
        png_data = cairosvg.svg2png(
            url=svg_path,
            output_width=size,
            output_height=size
        )
        
        # Charger l'image PNG
        img = Image.open(BytesIO(png_data))
        
        # Convertir en RGBA si nécessaire
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        images.append(img)
    
    # Sauvegarder en tant que fichier ICO
    print(f"  💾 Sauvegarde du fichier ICO...")
    images[0].save(
        ico_path,
        format='ICO',
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )
    
    print(f"✅ Icône créée avec succès : {ico_path}")
    print(f"📊 Tailles incluses : {', '.join(f'{s}x{s}' for s in sizes)}")
    
    # Afficher la taille du fichier
    file_size = os.path.getsize(ico_path)
    print(f"📁 Taille du fichier : {file_size:,} bytes ({file_size/1024:.1f} KB)")

if __name__ == "__main__":
    # Chemins des fichiers
    svg_file = "icon.svg"
    ico_file = "icon.ico"
    
    # Vérifier que le fichier SVG existe
    if not os.path.exists(svg_file):
        print(f"❌ Erreur : {svg_file} non trouvé")
        exit(1)
    
    try:
        svg_to_ico(svg_file, ico_file)
        print("\n🎯 L'icône est prête à être utilisée dans nmea_server.spec !")
        print("   Modifiez la ligne : icon='icon.ico'")
        
    except Exception as e:
        print(f"❌ Erreur lors de la conversion : {e}")
        print("💡 Essayez d'installer les dépendances : pip install Pillow cairosvg")
        exit(1)
