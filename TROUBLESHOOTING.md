# 🚨 Guide de Dépannage - Build Enhanced

## ✅ **Solution Rapide (Recommandée)**

Si le build échoue, suivez ces étapes dans l'ordre :

### 1. 🔧 Setup Automatique
```cmd
.\setup_enhanced.bat
```
Ce script va :
- Vérifier Python
- Créer l'environnement virtuel
- Installer toutes les dépendances

### 2. 🧪 Test de Build
```cmd
.\test_build.bat
```
Ce script va tester le build de façon automatisée.

### 3. 🏗️ Build Final
```cmd
.\build_enhanced.bat
```
Choisir l'option 2 pour System Tray.

## 🔍 **Diagnostic des Problèmes**

### Problème : "Python non trouvé"
```cmd
.\diagnostic.bat
```
**Solutions** :
- Installer Python depuis https://python.org
- **IMPORTANT** : Cocher "Add Python to PATH"
- Redémarrer PowerShell après installation

### Problème : "pip non trouvé" 
**Cause** : Environnement virtuel non activé

**Solution** :
```cmd
.\.venv\Scripts\activate.bat
pip --version
```

### Problème : "Fichier .spec non trouvé"
**Cause** : Mauvais répertoire de travail

**Solution** :
```cmd
# Vérifier que vous êtes dans le bon répertoire
dir *.spec
# Doit afficher : nmea_server_tray.spec, etc.
```

### Problème : "Dépendances manquantes"
**Solutions** :
```cmd
# Réinstaller les dépendances
.\.venv\Scripts\activate.bat
pip install -r requirements_enhanced.txt
```

## 📋 **Ordre de Dépannage Complet**

1. **Diagnostic** : `.\diagnostic.bat`
2. **Setup** : `.\setup_enhanced.bat` 
3. **Test** : `.\test_build.bat`
4. **Build** : `.\build_enhanced.bat`

## 🎯 **Vérifications Essentielles**

### Répertoire Correct
```cmd
# Vous devez être dans le répertoire contenant :
dir nmea_server*.py     # Scripts Python principaux
dir *.spec              # Fichiers PyInstaller
dir requirements*.txt   # Fichiers de dépendances
```

### Environnement Virtuel
```cmd
# Doit exister :
dir .venv\Scripts\activate.bat
```

### Python Accessible
```cmd
# Après activation de l'environnement :
.\.venv\Scripts\activate.bat
python --version        # Doit afficher la version
pip --version          # Doit afficher la version
```

## 🚀 **Si Tout Échoue**

### Reset Complet
```cmd
# 1. Supprimer l'environnement virtuel
rmdir /s /q .venv

# 2. Recréer tout
.\setup_enhanced.bat

# 3. Tester
.\test_build.bat
```

### Méthode Manuelle
```cmd
# 1. Créer environnement virtuel
python -m venv .venv

# 2. Activer
.\.venv\Scripts\activate.bat

# 3. Installer dépendances
pip install --upgrade pip
pip install -r requirements_enhanced.txt

# 4. Builder
pyinstaller nmea_server_tray.spec --clean --noconfirm
```

## 📞 **Support**

Si les problèmes persistent :

1. Exécuter `.\diagnostic.bat` et noter les erreurs
2. Vérifier que vous avez les droits administrateur si nécessaire
3. Vérifier que Windows Defender ne bloque pas les fichiers
4. S'assurer que l'antivirus n'interfère pas avec PyInstaller

## ✨ **Versions Alternatives**

Si la version System Tray pose problème, essayez :
- **Console** : `.\scripts\windows\build.bat` (version de base)
- **Service** : Option 3 dans `.\build_enhanced.bat`

La version Console est plus simple et peut aider à identifier les problèmes.
