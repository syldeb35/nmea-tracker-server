# GitHub Actions Test Script - Avec Diagnostic

## Pour le workflow GitHub Actions, ajoutez cette étape de diagnostic :

```yaml
- name: 🔍 Diagnostic Executable
  run: |
    echo "=== Diagnostic Executable ==="
    cd dist
    echo "Contenu du répertoire dist:"
    dir
    echo ""
    echo "Lancement du diagnostic..."
    .\nmea_tracker_tray.exe --diagnostic
    echo ""
    echo "Test de démarrage..."
    $process = Start-Process -FilePath ".\nmea_tracker_tray.exe" -ArgumentList "--console" -PassThru -NoNewWindow
    Start-Sleep -Seconds 8
    if (!$process.HasExited) {
        Write-Host "✅ Executable starts successfully" -ForegroundColor Green
        Stop-Process -Id $process.Id -Force
    } else {
        Write-Host "❌ Executable failed to start" -ForegroundColor Red
        
        # En cas d'échec, afficher plus d'infos
        echo "=== Informations de debug ==="
        echo "Fichiers dans dist:"
        Get-ChildItem -Recurse | Select-Object Name, Length
        
        exit 1
    }
```

## Objectif du diagnostic

Le script `--diagnostic` va nous dire exactement :
1. Si `flask_cors` est inclus dans l'exécutable
2. Si `nmea_server_fallback.py` est présent
3. Quels modules sont disponibles/manquants
4. L'état du bundle PyInstaller

## Si le diagnostic montre que flask_cors est manquant

Cela confirmera que nos modifications des fichiers `.spec` n'ont pas encore été prises en compte dans le build GitHub Actions actuel.

## Actions correctives possibles

1. **Forcer le rebuild** : Modifier un commentaire dans le workflow
2. **Vérifier les dépendances** : S'assurer que `flask_cors` est dans requirements_enhanced_alt.txt
3. **Fallback sans CORS** : Modifier le fallback pour rendre CORS optionnel

## Test de fallback sans CORS

Si nécessaire, nous pourrions modifier `nmea_server_fallback.py` ainsi :

```python
# Import CORS optionnel
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("[WARNING] flask_cors non disponible - CORS désactivé")

# Configuration Flask
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Activer CORS seulement si disponible
if CORS_AVAILABLE:
    CORS(app)
else:
    print("[WARNING] CORS non configuré - connexions cross-origin limitées")
```
