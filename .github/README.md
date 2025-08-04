# 🤖 GitHub Actions - NMEA Tracker Server

Ce répertoire contient les workflows GitHub Actions pour automatiser le build et la release du serveur NMEA.

## 📋 Workflows Disponibles

### 1. 🏗️ Build System Tray (`build-system-tray.yml`)
**Déclenché par** : Push sur `main`/`develop`, Tags `v*`, PR vers `main`

**Fonctionnalités** :
- ✅ Build automatique de la version System Tray
- ✅ Test de l'exécutable généré
- ✅ Upload des artifacts (30 jours de rétention)
- ✅ Création automatique de releases pour les tags

**Artifacts produits** :
- `nmea_tracker_tray.exe` - Version System Tray
- `build_info.json` - Informations de build
- `VERSION.txt` - Information de version
- `RELEASE_NOTES.md` - Notes de release

### 2. 🚀 Release (`release.yml`)
**Déclenché par** : Création de release, Manuel

**Fonctionnalités** :
- ✅ Build de toutes les versions (Console, System Tray, Service)
- ✅ Création d'un package complet avec documentation
- ✅ Upload automatique vers la release GitHub
- ✅ Génération de notes de release

**Produits** :
- `nmea_tracker_tray.exe` - Version System Tray (recommandée)
- `nmea_tracker_server_console.exe` - Version Console
- `nmea_tracker_service.exe` - Version Service Windows
- `nmea-tracker-server-vX.X.X-windows.zip` - Package complet
- `QUICK_START.md` - Guide de démarrage rapide

### 3. 🧪 Test & Build PR (`test-build.yml`)
**Déclenché par** : PR vers `main`/`develop`, Push sur `develop`

**Fonctionnalités** :
- ✅ Validation des builds sur les PR
- ✅ Test rapide de fonctionnement
- ✅ Feedback automatique sur les PR

## 🎯 Utilisation

### Déclenchement Manuel des Builds

#### Build System Tray uniquement
```bash
# Via l'interface GitHub
Actions → Build NMEA Tracker Server - System Tray → Run workflow
```

#### Build de toutes les versions
```bash
# Via l'interface GitHub
Actions → Release NMEA Tracker Server → Run workflow
# Choisir la version (ex: v1.2.0)
```

### Création d'une Release

1. **Créer un tag** :
```bash
git tag v1.2.0
git push origin v1.2.0
```

2. **Ou créer une release via GitHub** :
   - Aller dans "Releases"
   - Cliquer "Create a new release"
   - Choisir le tag `v1.2.0`
   - Le workflow se déclenche automatiquement

### Workflow pour les Développeurs

1. **Développement** : Les push sur `develop` déclenchent les tests
2. **Pull Request** : Validation automatique du build
3. **Merge vers main** : Build et artifacts générés
4. **Tag/Release** : Release complète avec tous les exécutables

## 🔧 Configuration

### Variables d'Environnement
- `PYTHON_VERSION: '3.11'` - Version de Python utilisée
- `APP_NAME: 'NMEA-Tracker-Server'` - Nom de l'application

### Secrets Requis
- `GITHUB_TOKEN` - Token automatique pour les releases (fourni par GitHub)

### Dépendances
- `requirements_enhanced.txt` - Dépendances Python complètes
- Certificats SSL générés automatiquement pour chaque build

## 📦 Artifacts et Releases

### Structure des Artifacts
```
nmea-tracker-tray-windows/
├── nmea_tracker_tray.exe
├── build_info.json
├── VERSION.txt
└── RELEASE_NOTES.md
```

### Structure du Package de Release
```
nmea-tracker-server-v1.2.0-windows.zip
├── nmea_tracker_tray.exe              # Version recommandée
├── nmea_tracker_server_console.exe    # Version console
├── nmea_tracker_service.exe           # Version service
├── README.md                          # Documentation principale
├── CHANGELOG.md                       # Historique des changements
├── WINDOWS_VERSIONS_GUIDE.md          # Guide des versions Windows
├── QUICK_START.md                     # Guide de démarrage rapide
└── VERSION.txt                        # Informations de version
```

## 🚨 Dépannage

### Build qui échoue
1. Vérifier les logs dans l'onglet "Actions"
2. Contrôler que `requirements_enhanced.txt` est à jour
3. Vérifier la compatibilité des dépendances Python

### Certificats SSL
Les certificats sont générés automatiquement pour chaque build. Si des problèmes persistent :
- Vérifier que le module `cryptography` est bien installé
- Contrôler les permissions de fichier

### Permissions
- Les workflows utilisent `GITHUB_TOKEN` automatique
- Pas de configuration supplémentaire nécessaire

## 📈 Monitoring

### Statut des Builds
- Badge automatique dans le README principal
- Notifications par email en cas d'échec (configurable)

### Métriques
- Temps de build moyen : ~5-10 minutes
- Taille typique des artifacts : ~50-80 MB
- Rétention des artifacts : 30 jours

## 🔄 Maintenance

### Mise à jour des Workflows
1. Modifier les fichiers `.yml` dans `.github/workflows/`
2. Tester avec un push sur une branche de test
3. Merger vers `main` après validation

### Mise à jour des Dépendances
1. Modifier `requirements_enhanced.txt`
2. Tester localement avec `build_enhanced.bat`
3. Valider via un workflow de test

Cette configuration assure une intégration continue robuste pour le projet NMEA Tracker Server ! 🎯
