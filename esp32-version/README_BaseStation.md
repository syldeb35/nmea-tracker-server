# NMEA Base Station ESP32 - Setup Guide

## 🏗️ Base Station Configuration

La configuration station de base est optimisée pour la collecte et la redistribution de données NMEA/AIS en mode stationnaire.

### 📁 Fichiers de Configuration

1. **`base_station.py`** - Configuration principale pour station de base
2. **`base_station_main.py`** - Application avancée avec fonctionnalités étendues
3. **`main.py`** - Application standard avec interface web améliorée

### 🌐 Interface Web Améliorée

La nouvelle interface web inclut :

#### 🎯 **Fonctionnalités Principales**
- **Carte interactive** avec Leaflet.js
- **Monitoring temps réel** des données GPS/AIS
- **Statistiques système** détaillées
- **Console NMEA** avec contrôles
- **Export de données** en JSON
- **Indicateurs visuels** de qualité du signal

#### 📊 **Panneaux d'Information**
1. **Position & Navigation**
   - Latitude/Longitude avec précision 6 décimales
   - Vitesse sur fond (SOG)
   - Route sur fond (COG)

2. **Statut GPS**
   - Qualité du fix (avec code couleur)
   - Nombre de satellites
   - HDOP (dilution de précision)
   - Dernière mise à jour

3. **Carte Interactive**
   - Position en temps réel
   - Trace des positions précédentes
   - Zoom automatique

4. **Statistiques Système**
   - Total des phrases NMEA reçues
   - Taux de réception (phrases/minute)
   - Clients connectés
   - Temps de fonctionnement

5. **Console NMEA**
   - Flux de données brutes
   - Contrôles Pause/Resume
   - Fonction Clear
   - Export des données

### ⚙️ Configuration Station de Base

#### **WiFi en Mode Station**
```python
WIFI_CONFIG = {
    "mode": "STA",  # Connexion réseau existant
    "sta_ssid": "BaseStationNetwork",
    "sta_password": "station2024"
}
```

#### **Ports Réseau Étendus**
```python
NETWORK_CONFIG = {
    "http_port": 80,
    "websocket_port": 81,
    "tcp_relay_port": 10110,      # Relais NMEA standard
    "udp_broadcast_port": 4001    # Diffusion UDP
}
```

#### **Configuration Série Haute Performance**
```python
SERIAL_CONFIG = {
    "baudrate": 38400,            # Débit élevé
    "timeout": 500                # Réactivité optimisée
}
```

#### **Phrases NMEA Complètes**
```python
NMEA_CONFIG = {
    "sentences": [
        # GPS Standard
        "GGA", "RMC", "GLL", "VTG", "ZDA",
        # Navigation
        "HDT", "HDG", "ROT", "VHW",
        # AIS
        "VDM", "VDO", "AIV", "ABK", "BBM",
        # Profondeur/Météo
        "DPT", "DBT", "MWV", "MWD"
    ]
}
```

### 🔧 Fonctionnalités Avancées

#### **1. Relais TCP/UDP**
- Redistribution des données NMEA vers d'autres systèmes
- Support du port standard 10110
- Diffusion UDP pour clients multiples

#### **2. Monitoring Système**
- Surveillance de l'alimentation
- Watchdog automatique
- Statistiques détaillées
- Gestion de la mémoire

#### **3. Logging et Export**
- Enregistrement des positions
- Export JSON des données
- Buffer circulaire pour l'historique

#### **4. API REST Étendue**
```
GET /                    - Interface web
GET /api/status         - Statut complet du système
GET /api/config         - Configuration actuelle
GET /api/reset          - Redémarrage système
```

### 🚀 Installation Station de Base

#### **1. Upload des Fichiers**
```bash
# Fichiers principaux
ampy --port COM3 put main.py
ampy --port COM3 put base_station.py config.py

# Application avancée (optionnel)
ampy --port COM3 put base_station_main.py
```

#### **2. Configuration Réseau**
Modifiez `base_station.py` :
```python
WIFI_CONFIG = {
    "mode": "STA",
    "sta_ssid": "VotreReseau",
    "sta_password": "VotreMotDePasse"
}
```

#### **3. Connexions Matériel**
```
Source NMEA    ESP32
-----------    -----
TX (Data)   -> GPIO16 (RX)
GND         -> GND
VCC         -> 3.3V/5V
```

### 🎛️ Interface Web - Guide d'Utilisation

#### **Accès**
1. **Mode Station** : `http://[IP_ESP32]`
2. **Mode AP** : `http://192.168.4.1`

#### **Contrôles Console**
- **Clear** : Vide la console
- **Pause/Resume** : Contrôle l'affichage
- **Export** : Télécharge les données JSON

#### **Monitoring**
- **Indicateur de connexion** : Vert = connecté, Rouge = déconnecté
- **Codes couleur GPS** : 
  - Vert = fix de qualité
  - Orange = fix partiel
  - Rouge = pas de fix

### 📈 Cas d'Usage Station de Base

#### **🏢 Installation Portuaire**
- Collecte AIS multi-sources
- Redistribution vers systèmes VTS
- Monitoring trafic maritime

#### **🌊 Station Côtière**
- Réception GPS différentiel
- Diffusion corrections DGPS
- Surveillance navigation

#### **🏭 Site Industriel**
- Centralisation données de flotte
- Monitoring véhicules/équipements
- Intégration systèmes de gestion

### 🔍 Surveillance et Maintenance

#### **Indicateurs de Santé**
- Nombre de phrases reçues/minute
- Qualité du signal GPS
- Clients connectés
- Mémoire disponible

#### **Auto-Diagnostic**
- Watchdog automatique (5 min sans données = redémarrage)
- Monitoring alimentation
- Détection déconnexions

#### **Logs et Debug**
- Console web en temps réel
- Export périodique des données
- Statistiques de performance

### 🛠️ Dépannage Station de Base

#### **Pas de Données NMEA**
1. Vérifier connexions série
2. Contrôler baudrate (38400)
3. Tester avec différentes sources

#### **Connexion Réseau**
1. Vérifier SSID/mot de passe
2. Contrôler force du signal WiFi
3. Tester mode AP en secours

#### **Performance Dégradée**
1. Monitorer utilisation mémoire
2. Réduire le nombre de clients
3. Optimiser taux de mise à jour

La station de base ESP32 offre une solution complète et professionnelle pour la collecte et redistribution de données NMEA/AIS avec une interface web moderne et des fonctionnalités avancées de monitoring.
