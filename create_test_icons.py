#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test des icônes colorées pour le system tray
"""

from PIL import Image, ImageDraw
import os

def create_test_icons():
    """Crée des icônes de test pour visualiser les couleurs"""
    
    # Icône rouge (serveur arrêté)
    red_icon = Image.new('RGBA', (64, 64), (200, 0, 0, 255))
    draw = ImageDraw.Draw(red_icon)
    draw.ellipse([16, 16, 48, 48], fill=(150, 0, 0, 255))
    red_icon.save("test_icon_red.png")
    
    # Icône verte (serveur en marche)
    green_icon = Image.new('RGBA', (64, 64), (0, 200, 0, 255))
    draw = ImageDraw.Draw(green_icon)
    draw.ellipse([16, 16, 48, 48], fill=(0, 150, 0, 255))
    green_icon.save("test_icon_green.png")
    
    print("Icônes de test créées:")
    print("- test_icon_red.png (serveur arrêté)")
    print("- test_icon_green.png (serveur en marche)")

if __name__ == "__main__":
    create_test_icons()
