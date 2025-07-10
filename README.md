# 🧭 NMEA Tracker Server

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)

**Serveur NMEA/AIS temps réel avec interface web moderne pour le suivi de données GPS et navigation maritime.**

![NMEA Tracker Interface](https://img.shields.io/badge/Interface-Web%20HTTPS-brightgreen.svg)

## 🌟 Fonctionnalités

### 📡 **Réception de données NMEA**
- ✅ **Série (Bluetooth/USB)** - Connexion directe aux récepteurs GPS
- ✅ **UDP** - Réception réseau de données NMEA
- ✅ **TCP** - Connexion TCP pour flux de données
- ✅ **Auto-détection** des ports série Bluetooth

### 🗺️ **Interface web temps réel**
- ✅ **Carte interactive** avec Leaflet.js
- ✅ **Tracking GPS** en temps réel avec historique
- ✅ **Décodage NMEA** (GGA, RMC, GLL, VTG, HDT)
- ✅ **WebSocket** pour mise à jour instantanée
- ✅ **Design responsive** adaptatif mobile/desktop

### 🔧 **Configuration avancée**
- ✅ **Interface de configuration** web intuitive
- ✅ **Serveur HTTPS** avec certificats SSL
- ✅ **Logging rotatif** des trames NMEA
- ✅ **Multi-plateforme** (Windows, Linux, macOS)

### 📦 **Distribution**
- ✅ **Exécutable autonome** (PyInstaller)
- ✅ **Aucune installation** requise sur la machine cible
- ✅ **Icône personnalisée** professionnelle
- ✅ **Arrêt propre** avec Ctrl+C

## 🚀 Installation rapide

### Option 1: Exécutable (Recommandé)
```bash
# Windows
build_windows.bat

# Linux/macOS
./build_unix.sh

# Test
./test_executable.sh  # ou test_executable.bat
```

### Option 2: Installation Python
```bash
# Cloner le repository
git clone https://github.com/VOTRE_USERNAME/nmea-tracker-server.git
cd nmea-tracker-server

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
python nmea_server.py
```

## 🌐 Utilisation

1. **Démarrage** : Lancez l'exécutable ou `python nmea_server.py`
2. **Configuration** : Ouvrez https://localhost:5000/config.html
3. **Visualisation** : Accédez à https://localhost:5000/ pour voir les données en temps réel
4. **Arrêt** : Utilisez `Ctrl+C` pour un arrêt propre

### 📱 Interface web

| Page | Description | URL |
|------|-------------|-----|
| **Visualiseur** | Carte temps réel + données NMEA | `https://localhost:5000/` |
| **Configuration** | Paramètres connexions | `https://localhost:5000/config.html` |

## 🔧 Configuration

### Connexions supportées

#### 📻 Port série (Bluetooth/USB)
```
Port : Auto-détection ou manuel (ex: COM3, /dev/rfcomm0)
Vitesse : 4800, 9600, 19200, 38400, 57600, 115200 bps
```

#### 🌐 Réseau UDP
```
IP : 0.0.0.0 (écoute sur toutes les interfaces)
Port : 5005 (par défaut)
```

#### 🔗 Réseau TCP
```
IP : 0.0.0.0 (écoute sur toutes les interfaces)  
Port : 5006 (par défaut)
```

### Variables d'environnement (.env)
```bash
DEBUG=False
ENABLE_SERIAL=True
ENABLE_UDP=True
ENABLE_TCP=True
SERIAL_PORT=AUTO
SERIAL_BAUDRATE=4800
```

## 📊 Formats NMEA supportés

| Format | Description | Données extraites |
|--------|-------------|-------------------|
| **GGA** | Position GPS | Latitude, Longitude, Altitude, Heure |
| **RMC** | Position + Navigation | Position, Vitesse, Date, Heure |
| **GLL** | Position géographique | Latitude, Longitude, Heure |
| **VTG** | Vitesse/Route | Cap vrai, Vitesse |
| **HDT** | Cap vrai | Direction de navigation |

## 🛠️ Développement

### Structure du projet
```
nmea-tracker-server/
├── 📄 nmea_server.py          # Serveur principal
├── 📄 nmea_server.spec        # Configuration PyInstaller
├── 📁 templates/              # Interface web
│   ├── index.html             # Visualiseur principal
│   ├── config.html            # Page de configuration
│   └── favicon.svg            # Icône web
├── 📄 cert.pem / key.pem      # Certificats SSL
├── 📄 requirements.txt        # Dépendances Python
├── 📄 icon.svg / icon.ico     # Icônes application
└── 📁 build scripts/          # Scripts de compilation
```

### Compilation
```bash
# Installation PyInstaller
pip install pyinstaller

# Compilation
pyinstaller nmea_server.spec --clean --noconfirm

# Résultat
dist/nmea_tracker_server.exe  # Windows
dist/nmea_tracker_server      # Linux/macOS
```

### Technologies utilisées
- **Backend** : Python 3.8+, Flask, SocketIO, gevent
- **Frontend** : HTML5, JavaScript ES6, Leaflet.js
- **Réseau** : WebSocket, HTTP/HTTPS, UDP/TCP
- **Série** : PySerial avec auto-détection Bluetooth

## 🐛 Résolution de problèmes

### Port série non détecté
```bash
# Linux : Permissions
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0

# Windows : Vérifier Device Manager
# Réinstaller les drivers Bluetooth si nécessaire
```

### Erreur "Address already in use"
```bash
# Tuer le processus existant
sudo lsof -i :5000        # Linux/macOS
netstat -ano | find "5000"  # Windows

# Ou changer le port dans le code
HTTPS_PORT = 5001
```

### Certificats SSL manquants
L'application fonctionne automatiquement en HTTP si les certificats HTTPS sont absents.

## 📈 Roadmap

- [ ] 🔐 Interface d'authentification
- [ ] 📊 Graphiques historiques des données
- [ ] 🌍 Support multi-langues
- [ ] 📱 Application mobile companion
- [ ] ⚙️ API REST pour intégrations tierces
- [ ] 📦 Package Docker
- [ ] 🔄 Synchronisation cloud

## 🤝 Contribution

Les contributions sont les bienvenues ! 

1. **Fork** le projet
2. **Créez** votre branche feature (`git checkout -b feature/amazing-feature`)
3. **Committez** vos changements (`git commit -m 'Add amazing feature'`)
4. **Poussez** vers la branche (`git push origin feature/amazing-feature`)
5. **Ouvrez** une Pull Request

### Guidelines
- Code en **Python 3.8+**
- **Tests** pour les nouvelles fonctionnalités
- **Documentation** mise à jour
- **Messages de commit** descriptifs

## 📝 License

Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👨‍💻 Auteur

**Sylvain** - *Développement initial*

## 🙏 Remerciements

- 🗺️ **OpenStreetMap** pour les cartes
- 📦 **Leaflet.js** pour la cartographie interactive
- 🐍 **PyInstaller** pour la compilation d'exécutables
- 🌊 **Communauté maritime** pour les spécifications NMEA

## 📞 Support

- 🐛 **Issues** : [GitHub Issues](https://github.com/VOTRE_USERNAME/nmea-tracker-server/issues)
- 📧 **Email** : votre.email@example.com
- 💬 **Discussions** : [GitHub Discussions](https://github.com/VOTRE_USERNAME/nmea-tracker-server/discussions)

---

<div align="center">

**⭐ Si ce projet vous aide, n'hésitez pas à lui donner une étoile ! ⭐**

[![GitHub stars](https://img.shields.io/github/stars/VOTRE_USERNAME/nmea-tracker-server.svg?style=social&label=Star)](https://github.com/VOTRE_USERNAME/nmea-tracker-server)

</div>
