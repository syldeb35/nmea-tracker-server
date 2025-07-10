# NMEA Tracker Server - Guide de Build

## 🚀 Création d'un exécutable Windows

### Prérequis

- Python 3.8+ installé
- Toutes les dépendances du projet

### Méthode 1: Script automatique (Recommandé)

**Sur Windows :**

```cmd
build_windows.bat
```

**Sur Linux/macOS :**

```bash
./build_unix.sh
```

### Méthode 2: Commandes manuelles

1. **Installer PyInstaller :**

```bash
pip install pyinstaller
```

2. **Installer les dépendances :**

```bash
pip install -r requirements.txt
```

3. **Créer l'exécutable :**

```bash
pyinstaller nmea_server.spec --clean --noconfirm
```

## 📁 Structure après le build

```bash
dist/
├── nmea_tracker_server.exe    # Exécutable principal (Windows)
├── nmea_tracker_server        # Exécutable principal (Linux/macOS)
```

## 🎯 Test de l'exécutable

**Windows :**

```cmd
test_executable.bat
```

**Linux/macOS :**

```bash
./test_executable.sh
```

**Manuel :**

```bash
cd dist
./nmea_tracker_server          # Linux/macOS
nmea_tracker_server.exe        # Windows
```

## 🛑 Arrêter l'application

- **Ctrl+C** : Arrêt propre (recommandé)
- **Ctrl+Break** : Arrêt forcé (Windows uniquement)
- **Fermer la fenêtre de terminal** : Arrêt immédiat

L'application gère maintenant correctement les signaux d'arrêt et ferme proprement tous les threads et connexions.

L'application sera accessible sur :

- **HTTPS :** <https://localhost:5000/config.html>
- **HTTP :** <http://localhost:5000/config.html>

## 📋 Fichiers inclus dans l'exécutable

- ✅ Code Python principal
- ✅ Templates HTML (config.html, index.html)
- ✅ Favicon SVG
- ✅ Certificats SSL (cert.pem, key.pem)
- ✅ Configuration (.env)
- ✅ Toutes les dépendances Python

## 🔧 Personnalisation

### Icône incluse

L'application utilise une icône personnalisée (`icon.ico`) représentant :

- 🧭 Compas de navigation (thème maritime)
- 📡 Signaux GPS/NMEA
- ⚓ Ancre (symbole nautique)
- 🛰️ Satellite GPS

### Créer une nouvelle icône

1. Modifiez le fichier `icon.svg` selon vos préférences
2. Exécutez le script de conversion :

```bash
python create_icon.py
```

3. L'icône `icon.ico` sera automatiquement mise à jour

### Ajouter une icône personnalisée

1. Créez un fichier `.ico` (ex: `mon_icone.ico`)
2. Modifiez `nmea_server.spec` :

```python
icon='mon_icone.ico'
```

### Modifier les fichiers inclus

Éditez la section `datas` dans `nmea_server.spec` :

```python
datas=[
    ('templates/*.html', 'templates'),
    ('votre_fichier.txt', '.'),
],
```

## 🐛 Résolution de problèmes

### Erreur "Module not found"

Ajoutez le module manquant à `hiddenimports` dans `nmea_server.spec` :

```python
hiddenimports=[
    'module_manquant',
],
```

### Fichiers manquants

Ajoutez-les à la section `datas` :

```python
datas=[
    ('chemin/source', 'chemin/destination'),
],
```

### Taille de l'exécutable

Pour réduire la taille :

- Utilisez `--exclude-module` pour exclure des modules
- Activez la compression UPX (déjà activée dans le .spec)

## 📦 Distribution

L'exécutable final est autonome et peut être distribué sans installer Python ou les dépendances sur la machine cible.

**Taille typique :** ~50-100 MB (includes Python runtime + libraries)
