# PowerShell script to demonstrate Monitoring & Alerting features
# Usage: .\demo_monitoring.ps1

Write-Host "=== Monitoring & Alerting Demonstration ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Initialize Database
Write-Host "Step 1: Initializing database..." -ForegroundColor Yellow
try {
    python -m monitoring.dashboard_setup init_db --sqlite 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database initialized" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Database may already exist, continuing..." -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARNING] Database initialization skipped (may already exist)" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Record High Coverage (No Alert)
Write-Host "Step 2: Recording high coverage (85.5%)..." -ForegroundColor Yellow
python -m monitoring.dashboard_setup record_metric `
    --coverage 85.5 `
    --total 1000 `
    --covered 855 `
    --test-suite "unit-tests" `
    --branch-name "main"

Write-Host ""
Write-Host "Checking alerts with threshold 80%..." -ForegroundColor Yellow
$alertResult = python -m monitoring.dashboard_setup check_alerts --threshold 80.0 2>&1
if ($alertResult -match "No alerts triggered") {
    Write-Host "[OK] No alerts (coverage above threshold)" -ForegroundColor Green
} else {
    Write-Host "[ALERT] $alertResult" -ForegroundColor Red
}

Write-Host ""
Start-Sleep -Seconds 2

# Step 3: Record Medium Coverage (Warning Alert)
Write-Host "Step 3: Recording medium coverage (75.0%)..." -ForegroundColor Yellow
python -m monitoring.dashboard_setup record_metric `
    --coverage 75.0 `
    --total 1000 `
    --covered 750 `
    --test-suite "unit-tests" `
    --branch-name "main"

Write-Host ""
Write-Host "Checking alerts with threshold 80%..." -ForegroundColor Yellow
$alertResult = python -m monitoring.dashboard_setup check_alerts --threshold 80.0 2>&1
if ($alertResult -match "ALERT TRIGGERED" -or $alertResult -match "below threshold") {
    Write-Host "[WARNING] Alert triggered (coverage below 80%)" -ForegroundColor Yellow
    Write-Host $alertResult
} else {
    Write-Host "[INFO] $alertResult" -ForegroundColor Cyan
}

Write-Host ""
Start-Sleep -Seconds 2

# Step 4: Record Low Coverage (Critical Alert)
Write-Host "Step 4: Recording low coverage (65.0%)..." -ForegroundColor Yellow
python -m monitoring.dashboard_setup record_metric `
    --coverage 65.0 `
    --total 1000 `
    --covered 650 `
    --test-suite "unit-tests" `
    --branch-name "main"

Write-Host ""
Write-Host "Checking alerts with threshold 70%..." -ForegroundColor Yellow
$alertResult = python -m monitoring.dashboard_setup check_alerts --threshold 70.0 2>&1
if ($alertResult -match "CRITICAL" -or $alertResult -match "below threshold") {
    Write-Host "[CRITICAL] Alert triggered (coverage below 70%)" -ForegroundColor Red
    Write-Host $alertResult
} else {
    Write-Host "[INFO] $alertResult" -ForegroundColor Cyan
}

Write-Host ""
Start-Sleep -Seconds 2

# Step 5: View Latest Coverage
Write-Host "Step 5: Getting latest coverage metric..." -ForegroundColor Yellow
$latest = python -m monitoring.dashboard_setup latest 2>&1
if ($latest -match "coverage_percentage") {
    Write-Host "[OK] Latest coverage:" -ForegroundColor Green
    Write-Host $latest
} else {
    Write-Host "[INFO] $latest" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== Demonstration Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor Yellow
Write-Host "  - High coverage (85.5%): No alerts" -ForegroundColor Green
Write-Host "  - Medium coverage (75.0%): Warning alert (below 80%)" -ForegroundColor Yellow
Write-Host "  - Low coverage (65.0%): Critical alert (below 70%)" -ForegroundColor Red
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  - View trends: python demo_monitoring.py --show-trends" -ForegroundColor Cyan
Write-Host "  - Start exporter: python -m monitoring.dashboard_setup start_exporter" -ForegroundColor Cyan
Write-Host "  - View metrics: http://localhost:8001/metrics" -ForegroundColor Cyan

