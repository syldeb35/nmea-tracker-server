# 🚀 NOUVELLE FONCTIONNALITÉ : Connexion GPS Bluetooth Automatique

## ✨ Fini les commandes manuelles !

Avant, pour connecter votre GPS Bluetooth, vous deviez :

```bash
sdptool browse 40:DE:24:A6:F6:11        # Trouver le canal SPP
sudo rfcomm bind 0 40:DE:24:A6:F6:11 11 # Créer rfcomm0
# Puis configurer le serveur manuellement
```

**Maintenant, tout est automatique !** 🎉

## 🔧 Comment l'utiliser

### 1. Activer le mode AUTO

1. Ouvrir votre navigateur sur `http://localhost:5000/config`
2. Dans "Serial port", choisir **"AUTO - Bluetooth GPS Auto-Discovery"**
3. Cliquer sur "Apply"

### 2. C'est tout !

Le serveur va automatiquement :

- 🔍 Scanner les appareils Bluetooth toutes les minutes
- 🔗 Détecter votre GPS et trouver le bon canal
- ⚡ Créer la connexion rfcomm automatiquement
- 🔄 Se reconnecter si la connexion est perdue

## 📋 Prérequis (Linux uniquement)

```bash
# Installer les outils Bluetooth (une seule fois)
sudo apt-get install bluez bluez-utils

# Donner les permissions nécessaires
sudo usermod -a -G dialout $USER

# Redémarrer votre session
logout  # puis reconnexion
```

## 🧪 Tester votre configuration

Utilisez le script de test fourni :

```bash
./test_bluetooth_auto.sh
```

Il vérifiera automatiquement :

- ✅ Outils Bluetooth installés
- ✅ Bluetooth activé  
- ✅ Permissions correctes
- 🔍 Scan de test des appareils

## 📊 Logs de fonctionnement

Dans la console du serveur, vous verrez :

```text
[BLUETOOTH] === DÉCOUVERTE AUTOMATIQUE GPS ===
[BLUETOOTH] Trouvé: 40:DE:24:A6:F6:11 - Mon Téléphone
[BLUETOOTH] Canal SPP trouvé: 11
[BLUETOOTH] ✅ GPS trouvé: Mon Téléphone (40:DE:24:A6:F6:11)
[AUTO-DETECT] Port série auto-détecté: /dev/rfcomm0
[BLUETOOTH-MONITOR] Connexion GPS OK
```

## 🔧 Dépannage

### GPS pas trouvé ?

- Vérifiez que votre GPS/téléphone est **allumé** et **découvrable**
- Rapprochez-vous (< 10 mètres)
- Lancez le test : `./test_bluetooth_auto.sh`

### Problèmes de permissions ?

```bash
# Vérifier les groupes
groups $USER

# Si "dialout" n'apparaît pas :
sudo usermod -a -G dialout $USER
logout  # puis reconnexion
```

## 💡 Avantages

- 🚀 **Zéro configuration manuelle** 
- 🔄 **Reconnexion automatique**
- 🔍 **Découverte intelligente** des GPS
- 📝 **Logs détaillés** pour le debug
- ⚡ **Surveillance continue** (toutes les minutes)

## 🎯 Appareils compatibles

- 📱 **Téléphones Android** avec GPS et Bluetooth
- 🛰️ **Récepteurs GPS Bluetooth** dédiés  
- 📟 **Tout appareil** supportant SPP (Serial Port Profile)

---

Cette fonctionnalité transforme une tâche technique complexe en un simple clic ! 
Plus besoin de retenir les commandes `sdptool` et `rfcomm`. 🎉
