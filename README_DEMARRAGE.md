# NMEA Tracker Server - Guide de démarrage

## ✅ Configuration terminée !

Votre serveur NMEA est maintenant configuré et prêt à l'emploi.

## 🚀 Démarrage rapide

### Option 1: Script automatique (recommandé)
Double-cliquez sur `start_server.bat` pour démarrer le serveur.

### Option 2: Ligne de commande
```bash
cd "c:\Users\captain\Documents\WindyPlugin\nmea-tracker-server\nmea-tracker-server"
.\.venv\Scripts\python.exe nmea_server.py
```

## 🌐 Interface web

Une fois le serveur démarré, ouvrez votre navigateur sur :
- **HTTPS** : https://localhost:5000/config.html
- **HTTP** (fallback) : http://localhost:5000/config.html

## 📡 Ports de communication

- **Port HTTP/HTTPS** : 5000 (interface de configuration)
- **Port UDP** : 5005 (écoute des données NMEA)
- **Port TCP** : 5006 (écoute des données NMEA)
- **Port série** : AUTO (détection automatique Bluetooth/USB)

## 🔧 Configuration

Le serveur peut recevoir des données NMEA de :
1. **Port série** (GPS Bluetooth ou USB)
2. **UDP** (autres applications/appareils)
3. **TCP** (connexions directes)

Toutes les données reçues sont redistribuées via WebSocket pour le plugin Windy.

## 📊 Logs

Les logs sont automatiquement créés dans le dossier `logs/` :
- `main.log` : Messages principaux
- `nmea_data.log` : Trames NMEA reçues
- `network.log` : Détails des connexions réseau
- `debug.log` : Informations de débogage
- `errors.log` : Erreurs système

## 🛑 Arrêt du serveur

Appuyez sur **Ctrl+C** dans le terminal pour arrêter proprement le serveur.

## 🔍 Dépannage

Si le serveur ne démarre pas :
1. Vérifiez que l'environnement virtuel existe : `.venv\Scripts\python.exe`
2. Vérifiez que les ports ne sont pas occupés par d'autres programmes
3. Consultez les logs dans le dossier `logs/`

## 📞 Support

En cas de problème, consultez les logs d'erreur ou contactez le support technique.
