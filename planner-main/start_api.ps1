# PowerShell script to start the Planner Agent API
# Usage: .\start_api.ps1

Write-Host "=== Starting Planner Agent API ===" -ForegroundColor Cyan
Write-Host ""

# Set environment variables
Write-Host "Setting up environment variables..." -ForegroundColor Yellow
$env:PLANNER_API_SECRET = "test-secret-key"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "Arshiya@10"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "mydatabase"

Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "  PLANNER_API_SECRET: $env:PLANNER_API_SECRET"
Write-Host "  POSTGRES_USER: $env:POSTGRES_USER"
Write-Host "  POSTGRES_HOST: $env:POSTGRES_HOST"
Write-Host "  POSTGRES_DB: $env:POSTGRES_DB"
Write-Host ""

# Check if port 8000 is available
$portCheck = Test-NetConnection -ComputerName localhost -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue
if ($portCheck) {
    Write-Host "WARNING: Port 8000 is already in use!" -ForegroundColor Yellow
    Write-Host "  The API might already be running." -ForegroundColor Yellow
    Write-Host "  Access it at: http://localhost:8000" -ForegroundColor Cyan
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

Write-Host "Starting API server..." -ForegroundColor Yellow
Write-Host "  URL: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Docs: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

# Determine which Python to use
$pythonCmd = $null

# Check if venv exists and has uvicorn
if (Test-Path "venv\Scripts\python.exe") {
    $venvPython = "venv\Scripts\python.exe"
    Write-Host "Checking venv for uvicorn..." -ForegroundColor Yellow
    $uvicornCheck = & $venvPython -c "import uvicorn; print('ok')" 2>&1
    if ($LASTEXITCODE -eq 0 -or $uvicornCheck -match "ok") {
        $pythonCmd = $venvPython
        Write-Host "[OK] Using venv Python" -ForegroundColor Green
    }
}

# Fallback to .venv if venv doesn't work
if (-not $pythonCmd -and (Test-Path ".venv\Scripts\python.exe")) {
    $dotVenvPython = ".venv\Scripts\python.exe"
    Write-Host "Checking .venv for uvicorn..." -ForegroundColor Yellow
    $uvicornCheck = & $dotVenvPython -c "import uvicorn; print('ok')" 2>&1
    if ($LASTEXITCODE -eq 0 -or $uvicornCheck -match "ok") {
        $pythonCmd = $dotVenvPython
        Write-Host "[OK] Using .venv Python" -ForegroundColor Green
    }
}

# Fallback to system Python
if (-not $pythonCmd) {
    Write-Host "Checking system Python..." -ForegroundColor Yellow
    $sysPython = "python"
    $uvicornCheck = & $sysPython -c "import uvicorn; print('ok')" 2>&1
    if ($LASTEXITCODE -eq 0 -or $uvicornCheck -match "ok") {
        $pythonCmd = $sysPython
        Write-Host "[OK] Using system Python" -ForegroundColor Green
    }
}

# If still no Python found, try to install uvicorn or give error
if (-not $pythonCmd) {
    Write-Host "[ERROR] uvicorn not found in any Python environment!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install uvicorn:" -ForegroundColor Yellow
    Write-Host "  pip install uvicorn[standard] fastapi" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Or activate your virtual environment first:" -ForegroundColor Yellow
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
    Write-Host "  pip install uvicorn[standard] fastapi" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the API server
# Note: Environment variables set above should be inherited by the Python process
# If they're not, you may need to restart PowerShell or set them system-wide
& $pythonCmd -m uvicorn api.planner_api:app --host 0.0.0.0 --port 8000 --reload

