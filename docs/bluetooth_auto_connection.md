# Connexion GPS Bluetooth Automatique

## Fonctionnalité

Cette fonctionnalité permet la **découverte et connexion automatique** des récepteurs GPS Bluetooth, éliminant le besoin de configuration manuelle avec `sdptool` et `rfcomm`.

## Avantages

### ✅ Avant (Manuel)

```bash
# Étapes manuelles nécessaires
sdptool browse 40:DE:24:A6:F6:11        # Rechercher le canal SPP
sudo rfcomm bind 0 40:DE:24:A6:F6:11 11 # Créer le port rfcomm0
# Configurer le serveur pour utiliser /dev/rfcomm0
```

### 🚀 Maintenant (Automatique)

1. Sélectionner **"AUTO - Bluetooth GPS Auto-Discovery"** dans la configuration
2. Le serveur gère automatiquement tout le reste !

## Comment ça fonctionne

### Découverte Automatique

- **Scan Bluetooth** : Recherche tous les appareils à proximité
- **Détection SPP** : Utilise `sdptool` pour identifier le canal RFCOMM d'un service de classe Serial Port (`0x1101`), sans confondre les autres services dont le nom contient « SPP »
- **Test GPS** : Vérifie que l'appareil envoie bien des trames NMEA
- **Connexion** : Configure automatiquement `rfcomm` si un GPS est trouvé

### Surveillance Continue

- **Vérification périodique** : Toutes les 60 secondes
- **Reconnexion automatique** : En cas de perte de connexion
- **Gestion des erreurs** : Logs détaillés pour le debug

### Commandes Automatisées

```bash
# Le serveur exécute automatiquement :
sudo -n /usr/local/sbin/nmea-bluetooth-helper adapter-up
hcitool scan  # Uniquement si aucune adresse cible n'est configurée
sdptool browse XX:XX:XX:XX:XX:XX
sudo -n /usr/local/sbin/nmea-bluetooth-helper bind 0 XX:XX:XX:XX:XX:XX CANAL
```

## Configuration

### 1. Dans l'interface web

- Aller sur `https://votre-serveur:5000/config.html`
- Sélectionner **"AUTO - Bluetooth GPS Auto-Discovery (Linux only)"**
- Facultatif : renseigner **Bluetooth MAC address** au format `XX:XX:XX:XX:XX:XX` pour contacter directement cet appareil, même s'il n'apparaît pas au scan. Le canal SPP est découvert par `sdptool`.
- Laisser l'adresse vide pour conserver le scan automatique.
- Appliquer la configuration

Le paramètre correspondant dans `.env` est `BLUETOOTH_TARGET_MAC`. L'appareil doit être accessible et exposer un service SPP; son adresse configurée doit être celle utilisée par Bluetooth classique.

### 2. Prérequis système (Linux)

```bash
# Installation des outils Bluetooth
sudo apt-get install bluez bluez-utils

# Installer le helper privilégié limité au Bluetooth
sudo bash scripts/linux/install_bluetooth_helper.sh

# Permissions utilisateur
sudo usermod -a -G dialout $USER

# Redémarrer la session après ajout au groupe
```

### 3. Test des prérequis

```bash
# Utiliser le script de test fourni
./test_bluetooth_auto.sh
```

## Logs et Debug

### Messages de log typiques

```text
[BLUETOOTH] === DÉCOUVERTE AUTOMATIQUE GPS ===
[BLUETOOTH] Scan des appareils Bluetooth...
[BLUETOOTH] Trouvé: 40:DE:24:A6:F6:11 - Android Phone
[BLUETOOTH] Test appareil: Android Phone (40:DE:24:A6:F6:11)
[BLUETOOTH] Recherche canal SPP pour 40:DE:24:A6:F6:11...
[BLUETOOTH] Service Serial Port trouvé
[BLUETOOTH] Canal SPP trouvé: 11
[BLUETOOTH] Configuration rfcomm0 -> 40:DE:24:A6:F6:11:11
[BLUETOOTH] rfcomm configuré: /dev/rfcomm0
[BLUETOOTH] Test connexion GPS sur /dev/rfcomm0
[BLUETOOTH] Trame NMEA reçue: $GPGGA,123456,4805.8112,N,00142.5208,W,1,8,1.0,45.0,M...
[BLUETOOTH] ✅ GPS trouvé: Android Phone (40:DE:24:A6:F6:11) sur canal 11
[BLUETOOTH-MONITOR] Thread de surveillance démarré
[AUTO-DETECT] Port série auto-détecté: /dev/rfcomm0
```

### En cas de problème

```text
[BLUETOOTH] Aucun appareil trouvé
[BLUETOOTH] Échec du scan: Timeout
[BLUETOOTH] Aucun canal SPP trouvé
[BLUETOOTH] ❌ Pas de GPS: Device Name
```

## Compatibilité

### Systèmes supportés

- ✅ **Linux** : Fonctionnalité complète
- ❌ **Windows/macOS** : Fallback vers détection traditionnelle

### Appareils testés

- 📱 **Téléphones Android** avec GPS activé et Bluetooth
- 🛰️ **Récepteurs GPS Bluetooth** dédiés
- 📟 **Appareils compatibles SPP** (Serial Port Profile)

## Sécurité

### Permissions requises

- **Helper Bluetooth** : l'application reste lancée comme utilisateur normal. L'installateur place un helper root-owned dans `/usr/local/sbin` et ajoute une règle `sudoers` sans mot de passe limitée à ce helper.
- **Opérations autorisées** : activation de `hci0`, bind et release du seul `/dev/rfcomm0`; le helper valide l'adresse MAC et le canal SPP, et n'exécute aucune commande via un shell.
- **hcitool/sdptool** : Accès Bluetooth système
- **Groupe dialout** : Accès aux ports série

Pour désinstaller le helper et sa règle :

```bash
sudo rm /etc/sudoers.d/nmea-bluetooth-helper
sudo rm /usr/local/sbin/nmea-bluetooth-helper
```

### Considérations

- La découverte se fait uniquement sur les appareils **découvrables**
- Aucune authentification/pairing automatique
- Connexion en lecture seule (réception NMEA)

## Dépannage

### GPS non détecté

1. Vérifier que l'appareil GPS est **allumé** et **découvrable**
2. Tester manuellement : `hcitool scan`
3. Vérifier les permissions : `sudo rfcomm --help`
4. Exécuter le script de test : `./test_bluetooth_auto.sh`

### Connexion perdue

- Le système se reconnecte automatiquement toutes les 60 secondes
- Vérifier la portée Bluetooth (< 10 mètres généralement)
- Consulter les logs pour diagnostiquer

### Problèmes de permissions

```bash
# Ajouter l'utilisateur au groupe dialout
sudo usermod -a -G dialout $USER

# Vérifier l'appartenance aux groupes
groups $USER

# Redémarrer la session
logout # puis reconnexion
```

## Architecture Technique

### Classes principales

- **`BluetoothGPSManager`** : Gestion complète Bluetooth
- **`bluetooth_monitor()`** : Thread de surveillance
- **`detect_bluetooth_serial_port()`** : Interface avec l'ancien système

### Flux de fonctionnement

1. **Démarrage** → Thread de surveillance créé
2. **Scan** → Découverte des appareils Bluetooth
3. **Test** → Vérification SPP et trames NMEA
4. **Connexion** → Configuration rfcomm automatique
5. **Surveillance** → Vérification périodique de l'état
6. **Reconnexion** → En cas de perte de connexion

Cette fonctionnalité transforme une tâche manuelle complexe en un processus entièrement automatisé, améliorant significativement l'expérience utilisateur pour les connexions GPS Bluetooth.
