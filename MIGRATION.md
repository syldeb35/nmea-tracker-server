# 🔄 Migration vers la nouvelle organisation des scripts

Cette note documente la migration des scripts de build et installation vers une structure organisée par OS.

## 📋 Changements effectués

### Structure précédente (racine du projet)
```
nmea-tracker-server/
├── build_unix.sh
├── setup.sh  
├── check_requirements.sh
├── test_executable.sh
├── diagnose.sh
└── ...
```

### Nouvelle structure (organisée par OS)
```
nmea-tracker-server/
├── run.sh                    # 🆕 Script principal avec menu
├── scripts/
│   ├── linux/
│   │   ├── setup.sh
│   │   ├── check_requirements.sh
│   │   ├── build.sh
│   │   ├── test.sh
│   │   └── diagnose.sh
│   ├── windows/
│   │   ├── setup.bat
│   │   ├── build.bat
│   │   └── test.bat
│   ├── macos/
│   │   ├── setup.sh
│   │   ├── build.sh
│   │   └── test.sh
│   └── README.md
└── ...
```

## 🚀 Migration d'utilisation

### Avant (anciens scripts)
```bash
# Installation
./setup.sh

# Vérification
./check_requirements.sh

# Build
./build_unix.sh

# Test
./test_executable.sh

# Diagnostic
./diagnose.sh
```

### Après (nouveaux scripts)

#### Option 1: Menu interactif (recommandé)
```bash
./run.sh
# Puis choisir l'option souhaitée dans le menu
```

#### Option 2: Scripts directs par OS
```bash
# Linux
./scripts/linux/setup.sh
./scripts/linux/check_requirements.sh
./scripts/linux/build.sh
./scripts/linux/test.sh
./scripts/linux/diagnose.sh

# Windows
scripts\windows\setup.bat
scripts\windows\build.bat
scripts\windows\test.bat

# macOS
./scripts/macos/setup.sh
./scripts/macos/build.sh
./scripts/macos/test.sh
```

## ✨ Avantages de la nouvelle organisation

### 🗂️ **Organisation claire**
- Scripts regroupés logiquement par OS
- Évite l'encombrement de la racine du projet
- Maintenance facilitée

### 🌐 **Support multi-OS amélioré**
- Scripts spécialisés pour chaque plateforme
- Gestion des spécificités OS (permissions, chemins, etc.)
- Instructions adaptées par système

### 🎯 **Expérience utilisateur**
- Menu interactif guidé avec `./run.sh`
- Détection automatique de l'OS
- Messages d'erreur plus clairs

### 🔧 **Robustesse technique**
- Gestion des chemins relatifs améliorée
- Activation automatique des environnements virtuels
- Meilleure gestion des erreurs

## 📚 Documentation mise à jour

- ✅ **README.md principal** - Instructions de build mises à jour
- ✅ **scripts/README.md** - Documentation complète des scripts
- ✅ **.gitignore** - Exclusion des fichiers temporaires
- ✅ **run.sh** - Script d'orchestration principal

## 🔄 Compatibilité

### Scripts supprimés de la racine
- `build_unix.sh` → `scripts/linux/build.sh`
- `setup.sh` → `scripts/linux/setup.sh`
- `check_requirements.sh` → `scripts/linux/check_requirements.sh`
- `test_executable.sh` → `scripts/linux/test.sh`
- `diagnose.sh` → `scripts/linux/diagnose.sh`

### Nouveaux scripts
- `run.sh` - Menu principal interactif
- `scripts/windows/*.bat` - Support Windows complet
- `scripts/macos/*.sh` - Support macOS spécialisé

## 📈 Prochaines étapes

1. **Tester** la nouvelle organisation sur différents OS
2. **Mettre à jour** la documentation externe si nécessaire
3. **Former** les utilisateurs à la nouvelle interface
4. **Supprimer** définitivement les anciens scripts (déjà fait)

---

**Date de migration :** 11 juillet 2025  
**Version :** v2.0.0 (Scripts organisés)
