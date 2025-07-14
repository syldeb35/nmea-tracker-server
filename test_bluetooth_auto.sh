#!/bin/bash

# Test script pour la fonctionnalité Bluetooth GPS automatique

echo "=== Test de la fonctionnalité Bluetooth GPS automatique ==="
echo

# Vérifier les prérequis
echo "1. Vérification des prérequis..."

# Vérifier que bluez-utils est installé
if ! command -v hcitool &> /dev/null; then
    echo "❌ hcitool non trouvé. Installation de bluez-utils nécessaire:"
    echo "   sudo apt-get install bluez bluez-utils"
    exit 1
fi

if ! command -v sdptool &> /dev/null; then
    echo "❌ sdptool non trouvé. Installation de bluez-utils nécessaire:"
    echo "   sudo apt-get install bluez bluez-utils" 
    exit 1
fi

if ! command -v rfcomm &> /dev/null; then
    echo "❌ rfcomm non trouvé. Installation de bluez-utils nécessaire:"
    echo "   sudo apt-get install bluez bluez-utils"
    exit 1
fi

echo "✅ Outils Bluetooth disponibles"

# Vérifier que Bluetooth est activé
echo
echo "2. Vérification du statut Bluetooth..."
if hciconfig hci0 2>/dev/null | grep -q "UP RUNNING"; then
    echo "✅ Bluetooth activé"
else
    echo "⚠️  Tentative d'activation Bluetooth..."
    if sudo hciconfig hci0 up; then
        echo "✅ Bluetooth activé avec succès"
    else
        echo "❌ Impossible d'activer Bluetooth. Vérifiez:"
        echo "   - Que le module Bluetooth est présent"
        echo "   - Que le service bluetooth est démarré: sudo systemctl start bluetooth"
        exit 1
    fi
fi

# Test de scan rapide
echo
echo "3. Test de scan Bluetooth (10 secondes)..."
echo "Recherche d'appareils GPS/téléphones à proximité..."

timeout 10 hcitool scan > /tmp/bt_scan.txt 2>/dev/null || true

if [ -s /tmp/bt_scan.txt ]; then
    echo "✅ Appareils Bluetooth trouvés:"
    cat /tmp/bt_scan.txt | grep -v "Scanning" | head -5
else
    echo "⚠️  Aucun appareil trouvé. Assurez-vous que:"
    echo "   - Votre GPS/téléphone est allumé"
    echo "   - Le Bluetooth est activé sur l'appareil"
    echo "   - L'appareil est en mode découvrable"
fi

# Vérifier les permissions rfcomm
echo
echo "4. Vérification des permissions rfcomm..."
if [ -w /dev/rfcomm0 ] 2>/dev/null || sudo rfcomm --help &>/dev/null; then
    echo "✅ Permissions rfcomm OK"
else
    echo "⚠️  Vérifiez que l'utilisateur peut utiliser rfcomm (groupe dialout)"
    echo "   sudo usermod -a -G dialout $USER"
    echo "   Puis redémarrer la session"
fi

# Test manuel optionnel
echo
echo "5. Test manuel (optionnel):"
echo "Si vous connaissez l'adresse MAC de votre GPS, testez manuellement:"
echo "   sdptool browse XX:XX:XX:XX:XX:XX"
echo "   sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX CHANNEL"
echo

echo "=== Configuration recommandée ==="
echo "Dans la page de configuration du serveur NMEA:"
echo "- Port série: AUTO (pour activation de la découverte automatique)"
echo "- Le serveur scannera automatiquement toutes les minutes"
echo "- La connexion sera établie automatiquement lors de la détection"
echo

echo "=== Test terminé ==="
echo "Démarrez le serveur NMEA pour tester la découverte automatique."
