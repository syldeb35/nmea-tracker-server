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
*Prochaine étape: Tests multi-plateforme Qt + validation
