# PowerShell script to set up Grafana integration
# Usage: .\monitoring\setup-grafana.ps1

param(
    [string]$GrafanaUrl = "http://localhost:3000",
    [string]$PrometheusUrl = "http://localhost:9090",
    [string]$Username = "admin",
    [string]$Password = "admin"
)

Write-Host "=== Grafana Integration Setup ===" -ForegroundColor Cyan
Write-Host ""

# Check if Grafana is accessible
Write-Host "Checking Grafana connection..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$GrafanaUrl/api/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    Write-Host "[OK] Grafana is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Grafana is not accessible at $GrafanaUrl" -ForegroundColor Red
    Write-Host "Please ensure Grafana is installed and running." -ForegroundColor Yellow
    Write-Host "Download: https://grafana.com/grafana/download" -ForegroundColor Cyan
    exit 1
}

# Run setup
Write-Host ""
Write-Host "Setting up Grafana integration..." -ForegroundColor Yellow
python -m monitoring.grafana_integration setup `
    --grafana-url $GrafanaUrl `
    --prometheus-url $PrometheusUrl `
    --username $Username `
    --password $Password

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Setup complete!" -ForegroundColor Green
    Write-Host "Access your dashboard at: $GrafanaUrl/dashboards" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "[ERROR] Setup failed. Check the error messages above." -ForegroundColor Red
    exit 1
}

