# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-08-03

### ✨ Ajouté

- **Support AIS complet** avec décodage des trames fragmentées
- **Gestion des messages AIS multi-fragments** pour noms de navires, destinations et ETA
- **Modes client/serveur** pour connexions TCP et UDP
- **Configuration dynamique** via interface web avec persistence dans .env
- **Auto-chargement** de la configuration au démarrage depuis fichier .env
- **Cache intelligent** pour fragments AIS avec nettoyage automatique
- **API REST étendue** (/api/config, /api/status, /api/nmea_history)
- **Logging structuré** par fichiers (main.log, debug.log, network.log, errors.log, nmea_data.log)

### 🎨 Interface

- **Interface de configuration améliorée** avec modes client/serveur
- **Affichage temps réel** des données AIS avec noms de navires
- **Visualisation des connexions** TCP client vers GPS externes  
- **Couleurs par protocole** (UDP=jaune, TCP=cyan, Serial=vert)
- **Status des connexions** en temps réel via WebSocket
- **Initialisation correcte** des formulaires avec valeurs réelles

### 🔧 Technique

- **Décodage AIS Type 5** pour données statiques (noms, types, destinations)
- **Parser AIS fragmenté** pour messages multi-trames
- **Threads TCP/UDP séparés** selon mode client/serveur
- **Variables de configuration** lues depuis .env au démarrage
- **Cache des navires AIS** avec fusion des données position/statiques
- **Gestion robuste des erreurs** SSL et réseau
- **Suppression des logs HTTP** verbeux pour interface plus propre

### 🚀 Performances

- **Optimisation du parsing** NMEA avec nettoyage intelligent
- **Cache fragment AIS** avec expiration automatique (30s)
- **Émission WebSocket duale** (plugin Windy + interface web)
- **Gestion mémoire améliorée** pour buffer des données temps réel

### 🐛 Corrections

- **UDP/TCP ne démarraient pas** automatiquement au lancement
- **Noms de navires AIS** non récupérés (trames fragmentées)
- **Configuration par défaut** au lieu des valeurs .env
- **Interface non initialisée** avec les modes client/serveur réels
- **Logs HTTP parasites** masqués sur Windows
- **Threads TCP/UDP** mode serveur seulement (client ajouté)

### 📦 Configuration

- **Port UDP par défaut** : 50110 (au lieu de 5005)
- **Mode TCP client** vers appareils GPS externes
- **Variables .env étendues** : UDP_MODE, TCP_MODE, *_TARGET_IP, *_TARGET_PORT
- **Persistence automatique** des paramètres via interface web

## [1.0.0] - 2025-07-10

### ✨ Ajouté

- **Serveur NMEA/AIS** temps réel multi-source (Série, UDP, TCP)
- **Interface web moderne** avec carte interactive Leaflet.js
- **Décodeur NMEA** pour formats GGA, RMC, GLL, VTG, HDT
- **Auto-détection** des ports série Bluetooth
- **Configuration web** intuitive et responsive
- **Serveur HTTPS** avec certificats SSL intégrés
- **WebSocket** pour mise à jour temps réel
- **Logging rotatif** des trames NMEA
- **Gestion d'arrêt propre** avec Ctrl+C
- **Exécutable autonome** PyInstaller avec icône personnalisée
- **Support multi-plateforme** (Windows, Linux, macOS)

### 🎨 Interface

- **Carte temps réel** avec tracking GPS et historique
- **Favicon SVG** personnalisé pour l'application web
- **Design responsive** adaptatif mobile/desktop
- **Thème sombre/maritime** pour le visualiseur
- **Icône application** professionnelle (compas maritime)

### 🔧 Technique

- **Flask + SocketIO** pour le backend
- **gevent** pour les performances réseau
- **PySerial** avec gestion avancée des erreurs
- **Gestion des signaux** Unix/Windows
- **Configuration par variables d'environnement**
- **Scripts de build** automatisés

### 📦 Distribution

- **Scripts de compilation** Windows/Unix
- **Tests automatisés** de l'exécutable
- **Documentation complète** (README, BUILD_README)
- **Icône multi-résolution** pour Windows

### 🔒 Sécurité

- **Certificats SSL** pour HTTPS
- **Fallback HTTP** automatique
- **Gestion des erreurs** robuste
- **Validation des données** NMEA

## [Unreleased]

### 🔮 Planifié

- Interface d'authentification
- Graphiques historiques des données
- Support multi-langues
- Application mobile companion
- API REST pour intégrations tierces
- Package Docker
- Synchronisation cloud

---

**Format des versions :** [Majeur.Mineur.Patch]

- **Majeur** : Changements incompatibles de l'API
- **Mineur** : Nouvelles fonctionnalités rétrocompatibles
- **Patch** : Corrections de bugs rétrocompatibles
