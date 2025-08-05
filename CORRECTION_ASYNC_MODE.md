# 🔧 CORRECTION MAJEURE - Erreur "Invalid async_mode specified"

## 🐛 Problème identifié

L'erreur `Invalid async_mode specified` survenait parce que :

1. **nmea_server_tray.py** tentait d'importer `socketio` du serveur principal
2. **nmea_server.py** définit `socketio = SocketIO(app, async_mode='gevent')`
3. Dans l'environnement GitHub Actions **gevent n'est pas disponible**
4. Résultat : SocketIO essayait d'utiliser `async_mode='gevent'` sans gevent installé

## ✅ Solution appliquée

### Modification de la logique d'import dans `nmea_server_tray.py`

**AVANT :**
```python
# Tentait toujours d'importer nmea_server en premier
try:
    from nmea_server import socketio  # <- Problème: async_mode='gevent'
except ImportError as e:
    # Fallback seulement après échec
```

**APRÈS :**
```python
# Vérifier d'abord la disponibilité de gevent
try:
    import gevent
    GEVENT_AVAILABLE = True
except ImportError:
    GEVENT_AVAILABLE = False

# Importer le serveur approprié selon la disponibilité de gevent
if GEVENT_AVAILABLE:
    # Utiliser nmea_server.py (avec gevent)
    from nmea_server import socketio  # async_mode='gevent'
else:
    # Utiliser nmea_server_fallback.py (sans gevent)
    from nmea_server_fallback import socketio  # async_mode='threading'
```

### Résultat

✅ **Test local réussi :**
```
[FALLBACK] gevent non disponible - utilisation du serveur HTTP alternatif
[WARNING] flask_cors non disponible - CORS désactivé
[FALLBACK] NMEA Server Fallback - Version sans gevent
[INFO] Serveur NMEA fallback chargé (sans gevent)
[INFO] Starting threads - UDP:True, TCP:True, Serial:False
[INFO] Starting HTTP server on port 5000
```

## 🚀 Impact sur GitHub Actions

Maintenant GitHub Actions devrait :
1. ✅ Détecter que gevent n'est pas disponible
2. ✅ Charger directement `nmea_server_fallback.py`
3. ✅ Utiliser `async_mode='threading'` au lieu de `'gevent'`
4. ✅ Passer le test d'exécutable : "✅ Executable starts successfully"

## 📊 Tags créés

- `v1.3.2-cors-fix` : Correction CORS optionnel
- `v1.3.3-async-fix` : **Correction async_mode Invalid** (ce tag)

## 🎯 Prochaine étape

GitHub Actions va maintenant builder avec cette correction et devrait produire un exécutable fonctionnel sans l'erreur "Invalid async_mode specified".

## 🔍 Validation

Pour valider que la correction fonctionne :
1. Vérifier les logs GitHub Actions pour `v1.3.3-async-fix`
2. Rechercher : "✅ Executable starts successfully" 
3. Télécharger l'artefact produit
4. Tester l'exécutable en local
