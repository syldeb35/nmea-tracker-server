
# GitHub Actions - NMEA Tracker Server

This directory contains GitHub Actions workflows to automate the build, testing, and release of the NMEA server.

## Available Workflows

### 1. Build System Tray (`build-system-tray.yml`)
**Triggers** : Push on `main`/`develop`, Tags `v*`, PR to `main`

**Features** :
- Automatic build of System Tray version
- Test of generated executable
- Upload artifacts (30 days retention)
- Automatic release creation for tags

**Produced artifacts** :
- `nmea_tracker_tray.exe` - System Tray version
- `build_info.json` - Build information
- `VERSION.txt` - Version information
- `RELEASE_NOTES.md` - Release notes

### 2. Release (`release.yml`)
**Triggered by** : Release creation, Manual

**Features** :
- Build all versions (Console, System Tray, Service)
- Create complete package with documentation
- Automatic upload to GitHub release
- Generate release notes

**Products** :
- `nmea_tracker_tray.exe` - System Tray version (recommended)
- `nmea_tracker_server_console.exe` - Console version
- `nmea_tracker_service.exe` - Windows Service version
- `nmea-tracker-server-vX.X.X-windows.zip` - Complete package
- `QUICK_START.md` - Quick start guide

### 3. Test & Build PR (`test-build.yml`)
**Triggered by** : PR to `main`/`develop`, Push on `develop`

**Features** :
- Build validation on PRs
- Quick functionality test
- Automatic feedback on PRs

## Usage

### Manual Build Triggers

#### Build System Tray only
```bash
# Via GitHub interface
Actions → Build NMEA Tracker Server - System Tray → Run workflow
```

#### Build all versions
```bash
# Via GitHub interface
Actions → Release NMEA Tracker Server → Run workflow
# Choose version (e.g.: v1.2.0)
```

### Creating a Release

1. **Create a tag** :
```bash
git tag v1.2.0
git push origin v1.2.0
```

2. **Or create a release via GitHub** :
   - Go to "Releases"
   - Click "Create a new release"
   - Choose the tag `v1.2.0`
   - The workflow triggers automatically

### Workflow for Developers

1. **Development** : Pushes on `develop` trigger tests
2. **Pull Request** : Automatic build validation
3. **Merge to main** : Build and artifacts generated
4. **Tag/Release** : Complete release with all executables

## Configuration

### Environment Variables
- `PYTHON_VERSION` - Python version used
- `APP_NAME` - Application name

### Required Secrets
- `GITHUB_TOKEN` - Automatic token for releases (provided by GitHub)

### Dependencies
- `requirements.txt` - Python dependencies
- SSL certificates generated automatically for each build

## Artifacts and Releases

### Artifacts Structure
```
nmea-tracker-tray-windows/
├── nmea_tracker_tray.exe
├── build_info.json
├── VERSION.txt
└── RELEASE_NOTES.md
```

### Release Package Structure
```
nmea-tracker-server-v1.2.0-windows.zip
├── nmea_tracker_tray.exe              # Recommended version
├── nmea_tracker_server_console.exe    # Console version
├── nmea_tracker_service.exe           # Service version
├── README.md                          # Main documentation
├── CHANGELOG.md                       # Change history
├── WINDOWS_VERSIONS_GUIDE.md          # Windows versions guide
├── QUICK_START.md                     # Quick start guide
└── VERSION.txt                        # Version information
```

## Troubleshooting

### Build failures
1. Check logs in the "Actions" tab
2. Verify that `requirements.txt` is up to date
3. Check Python dependencies compatibility

### SSL Certificates
Certificates are generated automatically for each build. If problems persist:
- Verify that the `cryptography` module is installed
- Check file permissions

### Permissions
- Workflows use automatic `GITHUB_TOKEN`
- No additional configuration needed

## Monitoring

### Build Status
- Automatic badge in main README
- Email notifications on failure (configurable)

### Metrics
- Average build time: ~5-10 minutes
- Typical artifact size: ~50-80 MB
- Artifact retention: 30 days

## Maintenance

### Updating Workflows
1. Modify `.yml` files in `.github/workflows/`
2. Test with a push on a test branch
3. Merge to `main` after validation

### Updating Dependencies
1. Modify `requirements.txt`
2. Test locally
3. Validate via test workflow

This configuration ensures robust continuous integration for the NMEA Tracker Server project!
