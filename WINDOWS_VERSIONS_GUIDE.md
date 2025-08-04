# 🖥️ NMEA Tracker Server - Versions Avancées Windows

Ce guide présente les trois versions disponibles du serveur NMEA pour Windows, chacune adaptée à des besoins différents.

## 📦 Versions Disponibles

### 1. **Version Console** (Standard)
- Interface en ligne de commande
- Fenêtre visible dans la barre des tâches
- Facile à déboguer et surveiller
- **Fichier** : `nmea_tracker_server.exe`

### 2. **Version System Tray** (Recommandée)
- Icône dans la zone de notification (system tray)
- Interface discrète, pas de fenêtre visible
- Menu contextuel avec contrôles
- **Fichier** : `nmea_tracker_tray.exe`

### 3. **Version Service Windows**
- Service système en arrière-plan
- Démarrage automatique avec Windows
- Gestion via Services Windows
- **Fichier** : `nmea_tracker_service.exe`

## 🔧 Installation et Configuration

### Construction des Versions

```batch
# Build toutes les versions
build_enhanced.bat

# Ou choisir une version spécifique
# 1 = Console, 2 = System Tray, 3 = Service, 4 = Toutes
```

### Dépendances Requises

```batch
# Installation des dépendances avancées
pip install -r requirements_enhanced.txt
```

## 🎯 Utilisation des Versions

### Version System Tray 🥇 **RECOMMANDÉE**

```batch
# Lancement
cd dist
nmea_tracker_tray.exe

# L'icône apparaît dans la zone de notification
# Clic droit sur l'icône pour :
# - 📊 Ouvrir le tableau de bord
# - ⚙️ Ouvrir la configuration
# - ▶️ Démarrer/Arrêter le serveur
# - ❌ Quitter l'application
```

**Avantages** :
- ✅ Interface discrète (pas dans la barre des tâches)
- ✅ Contrôle facile via menu contextuel
- ✅ Démarrage/arrêt à la demande
- ✅ Accès rapide à l'interface web

### Version Service Windows

```batch
# Installation du service
cd dist
nmea_tracker_service.exe install

# Démarrage du service
net start NMEATrackerServer

# Arrêt du service
net stop NMEATrackerServer

# Désinstallation du service
nmea_tracker_service.exe remove
```

**Configuration pour démarrage automatique** :
```batch
# Démarrage automatique au boot
sc config NMEATrackerServer start= auto
```

**Gestion via interface Windows** :
1. Ouvrir `services.msc`
2. Chercher "NMEA Tracker Server"
3. Clic droit → Propriétés pour configurer

### Version Console (Standard)

```batch
# Lancement
cd dist
nmea_tracker_server.exe

# Mode console uniquement pour la version tray
nmea_tracker_tray.exe --console
```

## 🌐 Interface Web

Toutes les versions exposent la même interface web :

- **Tableau de bord** : `https://localhost:8443/`
- **Configuration** : `https://localhost:8443/config.html`

## 🔍 Comparaison des Versions

| Caractéristique | Console | System Tray | Service Windows |
|------------------|---------|-------------|-----------------|
| **Visibilité** | Fenêtre visible | Icône système | Invisible |
| **Démarrage** | Manuel | Manuel | Auto/Manuel |
| **Contrôle** | Terminal | Menu contextuel | Services Windows |
| **Debugging** | Facile | Moyen | Difficile |
| **Usage recommandé** | Développement | Usage quotidien | Serveur permanent |

## 🚀 Utilisation Recommandée par Scénario

### 👨‍💻 **Développement et Tests**
- **Version** : Console
- **Pourquoi** : Logs visibles, arrêt facile avec Ctrl+C

### 🏠 **Usage Personnel Quotidien**
- **Version** : System Tray
- **Pourquoi** : Interface discrète, contrôle facile, pas d'encombrement

### 🖥️ **Serveur Dédié / Production**
- **Version** : Service Windows
- **Pourquoi** : Démarrage automatique, fonctionnement en arrière-plan

## 🛠️ Dépannage

### System Tray ne démarre pas
```batch
# Vérifier les dépendances
pip install pystray pillow

# Mode console pour debug
nmea_tracker_tray.exe --console
```

### Service ne s'installe pas
```batch
# Vérifier les droits administrateur
# Exécuter en tant qu'administrateur

# Vérifier les dépendances
pip install pywin32
```

### Port déjà utilisé
- Modifier `HTTPS_PORT` dans le fichier `.env`
- Ou arrêter l'autre instance du serveur

## 📋 Logs et Monitoring

### System Tray
- Logs visibles dans le menu contextuel
- Messages dans la console si lancé avec `--console`

### Service Windows
- Logs dans l'Observateur d'événements Windows
- Catégorie : Applications et services → NMEA Tracker Server

### Interface Web
- Logs en temps réel dans l'interface de configuration
- Debug activable via l'interface web

## 🔧 Configuration Avancée

### Variables d'Environnement (.env)
```bash
# Port d'écoute
HTTPS_PORT=8443

# Modes de connexion
ENABLE_UDP=true
UDP_MODE=server
UDP_PORT=2000

ENABLE_TCP=true
TCP_MODE=server
TCP_PORT=2001

# Série (Bluetooth)
ENABLE_SERIAL=true
SERIAL_PORT=AUTO
SERIAL_BAUDRATE=38400

# Debug
DEBUG=false
```

### Intégration avec d'autres Outils

Le serveur NMEA peut être intégré avec :
- **OpenCPN** : Source de données UDP/TCP
- **Windy Plugin** : Transmission de données GPS/AIS
- **Applications GPS** : Réception de données NMEA

## 📞 Support

- **Interface web** : `https://localhost:8443/config.html`
- **Logs** : Selon la version utilisée (console/system tray/service)
- **Configuration** : Fichier `.env` dans le répertoire d'installation
