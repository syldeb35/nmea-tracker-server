# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
