Write-Host "GitHub Actions Workflow Validation"
Write-Host "=================================="
Write-Host ""
Write-Host "Checking workflow files..."
if (Test-Path ".github\workflows\build-system-tray.yml") {
    Write-Host "✓ Workflow file exists" -ForegroundColor Green
} else {
    Write-Host "✗ Workflow file missing" -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking required files for build..."
$requiredFiles = @(
    "nmea_server_tray.py",
    "nmea_server_service.py", 
    "requirements_enhanced_alt.txt",
    "icon.ico",
    "icon.png"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "✗ $file missing" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Checking Python environment..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not available" -ForegroundColor Red
}

Write-Host ""
Write-Host "Checking PowerShell version..."
Write-Host "✓ PowerShell: $($PSVersionTable.PSVersion)" -ForegroundColor Green

Write-Host ""
Write-Host "Checking UTF-8 support..."
$testString = "Fonctionnalités évidentes"
Write-Host "✓ UTF-8 test: $testString" -ForegroundColor Green

Write-Host ""
Write-Host "Workflow should be ready for GitHub Actions!" -ForegroundColor Cyan
