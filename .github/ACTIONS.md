
# GitHub Actions Workflows

This project uses GitHub Actions to automate cross-platform builds and tests.

## Available Workflows

### 1. `build.yml` - Build Cross-Platform Executables

**Triggers :**

- Tags `v*` (example: `v1.0.0`)
- Manual trigger (workflow_dispatch)

**Supported platforms :**

- Ubuntu Linux (x86_64)
- Windows (x86_64)
- macOS (ARM64 + Intel)

**Generated artifacts :**

- `nmea_tracker_server_linux` (Linux executable)
- `nmea_tracker_server_windows.exe` (Windows executable)
- `nmea_tracker_server_macos` (macOS ARM64)
- `nmea_tracker_server_macos-intel` (macOS Intel)

### 2. `test-python.yml` - Test Python Distribution

**Triggers :**

- Push on `main` or `develop`
- Pull requests
- Manual trigger

**Tests performed :**

- Python import test on multiple versions (3.8, 3.11)
- Cross-platform test (Linux, Windows, macOS)
- Portable Python distribution creation
- Template verification

**Generated artifacts :**

- `nmea_tracker_server_python_portable.zip`
- `nmea_tracker_server_python_portable.tar.gz`

## How to trigger a build

### Method 1: Git Tag (Recommended)

```bash
# Create and push a tag
git tag v1.0.0
git push --tags
```

### Method 2: Manual trigger

1. Go to GitHub → Actions
2. Select the workflow
3. Click "Run workflow"

## Troubleshooting

### "The strategy configuration was canceled"

**Cause:** A matrix job failed, canceling others.

**Solution:** The workflow is now configured with `fail-fast: false` to avoid this problem.

### Missing cert.pem/key.pem files

**Solution:** The workflow automatically creates temporary files if needed.

### PyInstaller build fails

**Possible solutions:**

1. Check dependencies in `requirements.txt`
2. Check the `nmea_server.spec` file
3. Look at detailed build logs

## Artifact Retrieval

1. Go to GitHub → Actions
2. Click on the completed workflow
3. Download artifacts in the "Artifacts" section

## Local Debug

Before pushing to GitHub, test locally :

```bash
# Structure and import test
./scripts/common/test_workflow.sh

# Python distribution test
./scripts/common/create_python_distribution.sh

# PyInstaller build test (optional)
pyinstaller nmea_server.spec
```

## Monitoring

The workflows include detailed checks :

- Project structure
- Python imports
- Generated file sizes
- Multi-OS compatibility

## Tips

1. **For releases:** Use semantic tags (`v1.0.0`, `v1.1.0`)
2. **For tests:** The Python workflow triggers automatically
3. **Distribution:** Prefer portable Python distribution (more compatible)
4. **Debugging:** Look at detailed logs in Actions
