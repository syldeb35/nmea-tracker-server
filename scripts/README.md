# 🛠️ Scripts de build et installation

Ce répertoire contient tous les scripts de build et d'installation organisés par système d'exploitation.

## 📁 Structure

```text
scripts/
├── linux/          # Scripts pour Linux (Ubuntu, Debian, CentOS, etc.)
├── windows/         # Scripts pour Windows (.bat)
├── macos/           # Scripts pour macOS
└── README.md        # Ce fichier
```

## 🚀 Utilisation rapide

### Script principal d'orchestration

```bash
# Lancement du menu interactif (Linux/macOS)
./run.sh
```

### Par système d'exploitation

#### 🐧 Linux

```bash
# Installation complète
./scripts/linux/setup.sh

# Vérification des prérequis
./scripts/linux/check_requirements.sh

# Compilation
./scripts/linux/build.sh

# Test
./scripts/linux/test.sh

# Diagnostic
./scripts/linux/diagnose.sh
```

#### 🪟 Windows

```batch
REM Installation complète
scripts\windows\setup.bat

REM Compilation
scripts\windows\build.bat

REM Test
scripts\windows\test.bat
```

#### 🍎 macOS

```bash
# Installation complète
./scripts/macos/setup.sh

# Compilation
./scripts/macos/build.sh

# Test
./scripts/macos/test.sh
```

## 📋 Description des scripts

### Scripts communs à tous les OS

| Script | Description | Fonctionnalité |
|--------|-------------|----------------|
| `setup` | Installation complète | Crée l'environnement virtuel, installe les dépendances |
| `build` | Compilation | Crée l'exécutable avec PyInstaller |
| `test` | Test | Lance et teste l'exécutable généré |

### Scripts spécifiques Linux/macOS

| Script | Description | Fonctionnalité |
|--------|-------------|----------------|
| `check_requirements` | Vérification | Contrôle les prérequis avant build |
| `diagnose` | Diagnostic | Analyse complète de l'environnement |

## 🔧 Prérequis par OS

### Linux

- Python 3.8+ (`sudo apt install python3 python3-pip python3-venv`)
- Permissions série (`sudo usermod -a -G dialout $USER`)

### Windows

- Python 3.8+ (depuis [python.org](https://python.org))
- "Add Python to PATH" coché lors de l'installation

### macOS

- Python 3.8+ (`brew install python` ou depuis python.org)
- Xcode Command Line Tools (`xcode-select --install`)

## 🚨 Résolution de problèmes

### Erreurs courantes

#### "Permission denied"

```bash
# Linux/macOS
chmod +x scripts/linux/*.sh
```

#### "Python not found"

```bash
# Vérifier l'installation
which python3
python3 --version
```

#### "pip not found"

```bash
# Linux
sudo apt install python3-pip

# macOS
python3 -m ensurepip --upgrade
```

### Diagnostic automatique

```bash
# Linux/macOS
./scripts/linux/diagnose.sh    # ou macos/diagnose.sh
```

## 📊 Logs et sorties

Les scripts génèrent des informations détaillées :

- ✅ Succès avec émoji vert
- ❌ Erreurs avec émoji rouge  
- ⚠️ Avertissements avec émoji orange
- ℹ️ Informations avec émoji bleu

## 🔄 Workflow recommandé

1. **Première installation**

   ```bash
   ./scripts/linux/setup.sh
   ```

2. **Vérification** (optionnel)

   ```bash
   ./scripts/linux/check_requirements.sh
   ```

3. **Compilation**

   ```bash
   ./scripts/linux/build.sh
   ```

4. **Test**

   ```bash
   ./scripts/linux/test.sh
   ```

5. **En cas de problème**

   ```bash
   ./scripts/linux/diagnose.sh
   ```

## 🆘 Support

En cas de problème, exécutez le script de diagnostic et partagez la sortie :

```bash
./scripts/[OS]/diagnose.sh > diagnostic.log 2>&1
```
