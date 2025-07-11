# 🤖 GitHub Actions Workflows

Ce projet utilise GitHub Actions pour automatiser les builds cross-platform et les tests.

## 📋 Workflows disponibles

### 1. 🏗️ `build.yml` - Build Cross-Platform Executables

**Déclenché par :**
- Tags `v*` (exemple: `v1.0.0`)
- Déclenchement manuel (workflow_dispatch)

**Plateformes supportées :**
- ✅ Ubuntu Linux (x86_64)
- ✅ Windows (x86_64)
- ✅ macOS (ARM64 + Intel)

**Artefacts générés :**
- `nmea_tracker_server_linux` (Linux executable)
- `nmea_tracker_server_windows.exe` (Windows executable)
- `nmea_tracker_server_macos` (macOS ARM64)
- `nmea_tracker_server_macos-intel` (macOS Intel)

### 2. 🐍 `test-python.yml` - Test Python Distribution

**Déclenché par :**
- Push sur `main` ou `develop`
- Pull requests
- Déclenchement manuel

**Tests effectués :**
- ✅ Test d'import Python sur multiples versions (3.8, 3.11)
- ✅ Test cross-platform (Linux, Windows, macOS)
- ✅ Création de distribution Python portable
- ✅ Vérification des templates

**Artefacts générés :**
- `nmea_tracker_server_python_portable.zip`
- `nmea_tracker_server_python_portable.tar.gz`

## 🚀 Comment déclencher un build

### Method 1: Tag Git (Recommandé)
```bash
# Créer et pousser un tag
git tag v1.0.0
git push --tags
```

### Method 2: Déclenchement manuel
1. Aller sur GitHub → Actions
2. Sélectionner le workflow
3. Cliquer "Run workflow"

## 🔧 Résolution des problèmes

### ❌ "The strategy configuration was canceled"

**Cause :** Un job de la matrice a échoué, annulant les autres.

**Solution :** Le workflow est maintenant configuré avec `fail-fast: false` pour éviter ce problème.

### ❌ Fichiers cert.pem/key.pem manquants

**Solution :** Le workflow créé automatiquement des fichiers temporaires si nécessaire.

### ❌ Build PyInstaller échoue

**Solutions possibles :**
1. Vérifier les dépendances dans `requirements.txt`
2. Vérifier le fichier `nmea_server.spec`
3. Regarder les logs de build détaillés

## 📦 Récupération des artefacts

1. Aller sur GitHub → Actions
2. Cliquer sur le workflow terminé
3. Télécharger les artefacts dans la section "Artifacts"

## 🐛 Debug local

Avant de pousser sur GitHub, testez localement :

```bash
# Test de structure et import
./scripts/common/test_workflow.sh

# Test de distribution Python
./scripts/common/create_python_distribution.sh

# Test de build PyInstaller (optionnel)
pyinstaller nmea_server.spec
```

## 🔍 Monitoring

Les workflows incluent des vérifications détaillées :
- Structure de projet
- Imports Python
- Taille des fichiers générés
- Compatibilité multi-OS

## 💡 Tips

1. **Pour des releases :** Utilisez les tags sémantiques (`v1.0.0`, `v1.1.0`)
2. **Pour les tests :** Le workflow Python se déclenche automatiquement
3. **Distribution :** Privilégiez la distribution Python portable (plus compatible)
4. **Debugging :** Regardez les logs détaillés dans Actions
