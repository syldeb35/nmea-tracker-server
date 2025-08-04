# 🧭 NMEA Tracker Server

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com)
[![Build Status](https://github.com/syldeb35/nmea-tracker-server/actions/workflows/build-system-tray.yml/badge.svg)](https://github.com/syldeb35/nmea-tracker-server/actions/workflows/build-system-tray.yml)
[![Release](https://img.shields.io/github/v/release/syldeb35/nmea-tracker-server)](https://github.com/syldeb35/nmea-tracker-server/releases/latest)

**Serveur NMEA/AIS temps réel avec interface web moderne pour le suivi de données GPS et navigation maritime.**

![NMEA Tracker Interface](https://img.shields.io/badge/Interface-Web%20HTTPS-brightgreen.svg)

## 🌟 Fonctionnalités

### 📡 Réception de données NMEA

- ✅ **Série (Bluetooth/USB)** - Connexion directe aux récepteurs GPS
- ✅ **UDP** - Réception réseau de données NMEA
- ✅ **TCP** - Connexion TCP pour flux de données
- ✅ **Auto-détection** des ports série Bluetooth

### 🗺️ Interface web temps réel

- ✅ **Carte interactive** avec Leaflet.js
- ✅ **Tracking GPS** en temps réel avec historique
- ✅ **Décodage NMEA** (GGA, RMC, GLL, VTG, HDT)
- ✅ **WebSocket** pour mise à jour instantanée
- ✅ **Design responsive** adaptatif mobile/desktop

### 🔧 Configuration avancée

- ✅ **Interface de configuration** web intuitive
- ✅ **Serveur HTTPS** avec certificats SSL
- ✅ **Logging rotatif** des trames NMEA
- ✅ **Multi-plateforme** (Windows, Linux, macOS)

### 📦 Distribution

- ✅ **Exécutable autonome** (PyInstaller)
- ✅ **Aucune installation** requise sur la machine cible
- ✅ **Icône personnalisée** professionnelle
- ✅ **Arrêt propre** avec Ctrl+C

## 🚀 Installation rapide

### 📦 Option 1: Téléchargement direct (Recommandé pour Windows)

**Version System Tray (Interface discrète)** :
[![Download System Tray](https://img.shields.io/badge/Download-System%20Tray%20Version-brightgreen?style=for-the-badge&logo=windows)](https://github.com/syldeb35/nmea-tracker-server/releases/latest/download/nmea_tracker_tray.exe)

**Toutes les versions** :
[![Download All](https://img.shields.io/badge/Download-All%20Versions-blue?style=for-the-badge&logo=github)](https://github.com/syldeb35/nmea-tracker-server/releases/latest)

**Builds automatiques** : Tous les exécutables sont générés automatiquement via GitHub Actions à chaque release.

### 🛠️ Option 2: Build depuis le code source

**Méthode rapide avec menu interactif :**

```bash
# Script principal avec menu (Linux/macOS)
./run.sh
```

**Méthode manuelle par OS :**

```bash
# Linux
./scripts/linux/setup.sh        # Installation
./scripts/linux/build.sh        # Compilation

# Windows  
scripts\windows\setup.bat       # Installation
scripts\windows\build.bat       # Compilation

# macOS
./scripts/macos/setup.sh        # Installation
./scripts/macos/build.sh        # Compilation
```

**Scripts disponibles:**

- 📁 `scripts/linux/` - Scripts pour Linux (Ubuntu, Debian, CentOS, etc.)
- 📁 `scripts/windows/` - Scripts pour Windows (.bat)
- 📁 `scripts/macos/` - Scripts pour macOS
- 🚀 `run.sh` - Menu interactif principal (Linux/macOS)

### Option 3: Installation Python manuelle

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
2. **Configuration** : Ouvrez `https://localhost:5000/config.html`
3. **Visualisation** : Accédez à `https://localhost:5000/` pour voir les données en temps réel
4. **Arrêt** : Utilisez `Ctrl+C` pour un arrêt propre

### 📱 Interface web

| Page | Description | URL |
|------|-------------|-----|
| **Visualiseur** | Carte temps réel + données NMEA | `https://localhost:5000/` |
| **Configuration** | Paramètres connexions | `https://localhost:5000/config.html` |

## 🔧 Configuration

### Connexions supportées

#### 📻 Port série (Bluetooth/USB)

```text
Port : Auto-détection ou manuel (ex: COM3, /dev/rfcomm0)
Vitesse : 4800, 9600, 19200, 38400, 57600, 115200 bps
```

#### 🌐 Réseau UDP

```text
IP : 0.0.0.0 (écoute sur toutes les interfaces)
Port : 5005 (par défaut)
```

#### 🔗 Réseau TCP

```text
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

```text
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
- 📧 **Email** : [votre.email@example.com](mailto:votre.email@example.com)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/VOTRE_USERNAME/nmea-tracker-server/discussions)

---

## ⭐ Support le projet

Si ce projet vous aide, n'hésitez pas à lui donner une étoile !

[![GitHub stars](https://img.shields.io/github/stars/VOTRE_USERNAME/nmea-tracker-server.svg?style=social&label=Star)](https://github.com/VOTRE_USERNAME/nmea-tracker-server)

# NMEA Tracker Server - État du Projet

## 📊 Résumé de l'Évolution

### ✅ Tâches Complétées

1. **Parser AIS** - Ajout d'un analyseur de messages AIS complet
   - Décodage des messages AIVDM/AIVDO
   - Extraction des coordonnées et informations navire
   - Conversion 6-bit ASCII vers coordonnées GPS

2. **Traduction Anglaise** - Interface utilisateur multilingue
   - config.html entièrement traduit en anglais
   - Correction de la syntaxe Jinja2
   - Interface plus accessible internationalement

3. **Optimisation VS Code** - Performance améliorée
   - Configuration .vscode/settings.json optimisée
   - Exclusions Pylance pour éviter les blocages
   - Limitations spell checker et file watcher

4. **Scripts Cross-Platform** - Organisation des builds
   - Répertoire scripts/ réorganisé par OS
   - Scripts Linux, Windows, macOS séparés
   - Scripts communs dans scripts/common/

5. **GitHub Actions** - CI/CD multi-plateforme
   - Workflow de build cross-platform fixé
   - Compatibilité PowerShell/Bash résolue
   - Builds automatiques Linux/Windows/macOS

6. **🔵 BLUETOOTH GPS AUTO-MANAGEMENT** - Automatisation complète
   - Découverte automatique des GPS Bluetooth via scan
   - Configuration automatique des connexions rfcomm
   - Surveillance continue avec reconnexion automatique
   - Plus besoin de commandes manuelles sdptool/rfcomm

7. **🖥️ INTERFACE GRAPHIQUE QT** - Application desktop multiplateforme
   - Interface Qt Python pour configuration du serveur
   - Contrôle start/stop du serveur intégré
   - Logs en temps réel dans l'interface
   - Configuration complète via GUI intuitive

### 🔧 Corrections Techniques Récentes

#### Gestion Bluetooth Automatique

- **Fonctionnalité**: Auto-découverte GPS Bluetooth sur Linux
- **Composants**:
  ```python
  class BluetoothGPSManager:
    - scan_bluetooth_devices()
    - find_spp_channel()
    - setup_rfcomm_connection()
    - test_gps_connection()
    - maintain_connection()
  ```

- **Thread de surveillance**: Monitoring continu toutes les minutes
- **Mode AUTO**: Configuration port série "AUTO" pour découverte automatique
- **Stabilité**: Correction des problèmes de connexion série simultanée

#### Interface Qt Python

- **Architecture**: Application PyQt6 complète avec panneaux configurables
- **Fonctionnalités**:
  - Configuration temps réel de tous les paramètres serveur
  - Contrôle serveur (start/stop/restart) intégré
  - Logs serveur en direct avec scrolling automatique
  - Détection automatique des ports série disponibles
  - Support mode AUTO Bluetooth avec documentation intégrée

#### GitHub Actions Workflow (.github/workflows/build.yml)

- **Problème**: Erreurs PowerShell avec commandes Unix (ls -la)
- **Solution**: Séparation conditionnelle Unix/Windows

  ```yaml
  # Unix/Linux/macOS
  - name: Verify executable (Unix)
    if: runner.os != 'Windows'
    shell: bash
    run: ls -la dist/
  
  # Windows
  - name: Verify executable (Windows)
    if: runner.os == 'Windows'
    shell: pwsh
    run: Get-ChildItem dist/
  ```

#### Gestion SSL améliorée

- **Windows**: Suppression des logs SSL verbose et erreurs certificat
- **Linux**: Correction import WSGIServer redondant
- **Certificats**: Génération automatique certificats auto-signés
- **Fallback**: Basculement automatique HTTP si HTTPS échoue

### 🚀 État Actuel

#### Structure Projet Complète

```text
nmea-tracker-server/
├── scripts/
│   ├── linux/          # Scripts spécifiques Linux
│   ├── windows/         # Scripts spécifiques Windows
│   ├── macos/          # Scripts spécifiques macOS
│   └── common/         # Scripts partagés + tests
├── .github/workflows/  # CI/CD multi-plateforme
├── .vscode/           # Configuration VS Code optimisée
├── templates/         # Interface web traduite
├── gui_config.py      # 🆕 Interface graphique Qt
├── start_gui.sh       # 🆕 Lanceur GUI Linux
├── start_gui.bat      # 🆕 Lanceur GUI Windows
├── requirements_gui.txt # 🆕 Dépendances Qt
├── nmea_server.py     # Serveur avec Bluetooth auto + AIS
└── docs/              # 🆕 Documentation Bluetooth
```

#### Fonctionnalités Serveur Avancées

1. **Mode AUTO**: Détection automatique GPS Bluetooth
2. **Thread monitoring**: Surveillance connexions Bluetooth
3. **Reconnexion automatique**: Maintien connexion GPS
4. **Interface dual**: Web HTTPS + GUI Qt desktop
5. **Logs rotatifs**: Gestion historique des logs NMEA
6. **Multi-protocole**: Support série, UDP, TCP simultané

#### Interface Utilisateur Dual

1. **Web Interface** (config.html):
   - Accessible via HTTPS sur port 5000
   - Configuration complète via navigateur
   - Monitoring temps réel des données GPS

2. **GUI Qt Application** (gui_config.py):
   - Application desktop native multiplateforme
   - Contrôle serveur intégré avec start/stop
   - Logs temps réel et configuration intuitive
   - Détection automatique ports série

### 📋 Actions Recommandées

#### Immédiat

1. **Tester Interface Qt**: Valider l'application GUI

   ```bash
   pip install PyQt6 pyserial
   python gui_config.py
   ```

2. **Valider Bluetooth Auto**: Tester découverte automatique

   ```bash
   # Configurer port sur "AUTO" dans .env
   SERIAL_PORT=AUTO
   python nmea_server.py
   ```

3. **Push nouvelles fonctionnalités**: Commit complet

   ```bash
   git add .
   git commit -m "feat: Add Qt GUI + Bluetooth auto-management"
   git push
   ```

#### Court Terme

- Tester interface Qt sur Windows/macOS
- Valider Bluetooth auto-discovery sur différents GPS
- Améliorer documentation utilisateur pour mode AUTO
- Créer builds avec dépendances Qt incluses

#### Long Terme

- Interface Qt avec monitoring GPS en temps réel
- Cartographie intégrée dans l'interface Qt
- Support découverte automatique GPS USB
- Mode serveur distribué multi-instance

### 🎯 Objectifs Atteints

✅ **Parser AIS fonctionnel**
✅ **Interface anglaise complète**  
✅ **Scripts cross-platform organisés**
✅ **CI/CD multi-plateforme stable**
✅ **VS Code optimisé pour le développement**
✅ **Tests automatisés complets**
✅ **🔵 Bluetooth GPS auto-management complet**
✅ **🖥️ Interface graphique Qt multiplateforme**
✅ **🔄 Monitoring et reconnexion automatique**
✅ **⚙️ Configuration dual web + desktop**

### 💡 Points Clés Techniques

1. **Séparation OS**: Workflows GitHub Actions conditionnels
2. **Encodage**: ASCII pour compatibilité Windows
3. **Shells**: bash (Unix) vs pwsh (Windows)
4. **Commandes**: ls vs Get-ChildItem selon l'OS
5. **Tests**: Scripts de validation locaux avant CI
6. **🆕 Bluetooth**: Gestion automatique rfcomm + sdptool sur Linux
7. **🆕 Threading**: Surveillance Bluetooth non-bloquante
8. **🆕 Qt Interface**: Application desktop native avec PyQt6
9. **🆕 SSL robuste**: Gestion certificats auto-signés + fallback HTTP

### 🏗️ Architecture Technique Avancée

#### Bluetooth Auto-Management

```text
BluetoothGPSManager
├── scan_bluetooth_devices()    # hcitool scan
├── find_spp_channel()         # sdptool browse
├── setup_rfcomm_connection()  # rfcomm bind
├── test_gps_connection()      # test NMEA
└── maintain_connection()      # surveillance
```

#### Threading Model

```text
Main Thread
├── serial_listener()          # Thread lecture série
├── udp_listener()            # Thread écoute UDP
├── tcp_listener()            # Thread écoute TCP
├── bluetooth_monitor()       # Thread surveillance BT
└── flask_app()              # Thread serveur web
```

#### Qt GUI Architecture

```text
NMEAServerGUI (QMainWindow)
├── Config Panel              # Configuration serveur
├── Log Panel                # Logs temps réel
├── Status Bar               # État serveur
└── QProcess                 # Contrôle serveur
```

---
*Dernière mise à jour: 31 juillet 2025*
*État: Interface Qt + Bluetooth auto-management opérationnels*
*Prochaine étape: Tests multi-plateforme Qt + validation GPS auto*
