# 🤝 Guide de Contribution

Merci de votre intérêt pour contribuer au **NMEA Tracker Server** ! Ce guide vous aidera à comprendre comment participer au développement du projet.

## 🌟 Types de contributions

Nous accueillons tous types de contributions :

- 🐛 **Rapports de bugs** et corrections
- ✨ **Nouvelles fonctionnalités** et améliorations
- 📚 **Documentation** et traductions
- 🧪 **Tests** et validation
- 🎨 **Interface utilisateur** et design
- 🔧 **Optimisations** et refactoring

## 🚀 Démarrage rapide

### 1. Fork et clone
```bash
# Fork le repository sur GitHub puis :
git clone https://github.com/VOTRE_USERNAME/nmea-tracker-server.git
cd nmea-tracker-server
```

### 2. Configuration de l'environnement
```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt
```

### 3. Tester que tout fonctionne
```bash
python nmea_server.py
# Ouvrir https://localhost:5000/config.html
```

## 📋 Processus de contribution

### 1. Créer une issue (recommandé)
Avant de commencer, [créez une issue](https://github.com/VOTRE_USERNAME/nmea-tracker-server/issues/new) pour :
- 🐛 Signaler un bug
- 💡 Proposer une fonctionnalité
- 🤔 Poser une question

### 2. Créer une branche
```bash
git checkout -b feature/nom-de-votre-fonctionnalite
# ou
git checkout -b fix/description-du-bug
```

### 3. Développer
- ✅ Écrivez du code propre et documenté
- ✅ Suivez les conventions Python (PEP 8)
- ✅ Ajoutez des tests si possible
- ✅ Mettez à jour la documentation

### 4. Tester
```bash
# Tester manuellement
python nmea_server.py

# Compiler l'exécutable
./build_unix.sh  # ou build_windows.bat
./test_executable.sh
```

### 5. Commit et push
```bash
git add .
git commit -m "✨ Ajouter nouvelle fonctionnalité XYZ

- Description de ce qui a été ajouté
- Pourquoi c'était nécessaire
- Comment cela fonctionne"

git push origin feature/nom-de-votre-fonctionnalite
```

### 6. Pull Request
1. Allez sur GitHub et créez une **Pull Request**
2. Décrivez clairement vos changements
3. Liez l'issue correspondante si applicable
4. Attendez la review et les commentaires

## 📝 Standards de code

### Python
```python
# Utiliser des docstrings
def ma_fonction(param: str) -> bool:
    """
    Description de la fonction.
    
    Args:
        param: Description du paramètre
        
    Returns:
        Description du retour
    """
    return True

# Noms descriptifs
enable_serial = True  # ✅
es = True            # ❌
```

### Messages de commit
Utilisez des **emojis** et soyez descriptifs :
```bash
✨ Ajouter support du protocole AIS
🐛 Corriger erreur de décodage NMEA
📚 Améliorer documentation API
🎨 Refactorer interface web
🔧 Optimiser performance UDP
♻️ Refactorer code série
```

### Structure des fichiers
```
nmea-tracker-server/
├── nmea_server.py          # 🚫 NE PAS toucher structure principale
├── templates/              # ✅ Améliorations UI autorisées
├── requirements.txt        # ✅ Nouvelles dépendances OK
├── docs/                   # ✅ Documentation supplémentaire
└── tests/                  # ✅ Tests encouragés
```

## 🧪 Tests

### Tests manuels
1. **Fonctionnalité de base** : Serveur démarre et interface accessible
2. **Connexions** : UDP, TCP, Série fonctionnent
3. **Interface** : Configuration et visualisation opérationnelles
4. **Build** : Exécutable se compile et fonctionne

### Tests automatisés (à venir)
Nous planifions d'ajouter :
- Tests unitaires pour le décodage NMEA
- Tests d'intégration pour les connexions réseau
- Tests de performance

## 🚫 Ce qu'il faut éviter

- ❌ Modifier les certificats SSL sans raison
- ❌ Changer la structure principale sans discussion
- ❌ Ajouter des dépendances lourdes inutiles
- ❌ Casser la compatibilité existante
- ❌ Code non documenté ou non testé

## 🎯 Idées de contributions

### 🥇 Priorité haute
- 🔐 Interface d'authentification web
- 📊 Graphiques historiques des données GPS
- 🌍 Support multi-langues (EN, ES, DE)
- 📱 Interface mobile responsive améliorée

### 🥈 Priorité moyenne  
- 🧪 Suite de tests automatisés
- 📦 Package Docker
- ⚙️ API REST pour intégrations
- 🔄 Synchronisation cloud des données

### 🥉 Idées futures
- 🤖 Interface en ligne de commande
- 🎨 Thèmes d'interface personnalisables
- 📈 Métriques de performance en temps réel
- 🔌 Système de plugins

## 💬 Communication

- 🐛 **Bugs** : [GitHub Issues](https://github.com/VOTRE_USERNAME/nmea-tracker-server/issues)
- 💡 **Discussions** : [GitHub Discussions](https://github.com/VOTRE_USERNAME/nmea-tracker-server/discussions)
- 📧 **Contact direct** : votre.email@example.com

## 🏆 Reconnaissance

Tous les contributeurs seront :
- ✨ Mentionnés dans le **CHANGELOG.md**
- 🎖️ Ajoutés à la section **Contributors** du README
- 💝 Remerciés personnellement

## 📄 License

En contribuant, vous acceptez que vos contributions soient sous licence **MIT** comme le reste du projet.

---

**Merci de faire de NMEA Tracker Server un meilleur outil pour la communauté maritime ! ⚓🧭**
