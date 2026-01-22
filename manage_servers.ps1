# PowerShell script to manage Planner Agent servers
# Usage:
#   .\manage_servers.ps1              - Start both servers
#   .\manage_servers.ps1 -Status       - Check server status
#   .\manage_servers.ps1 -Stop         - Stop all servers
#   .\manage_servers.ps1 -Restart      - Restart all servers

param(
    [switch]$Status,
    [switch]$Stop,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

# Configuration
$ApiPort = 8000
$FrontendPort = 8080
$LogFile = "server_manager.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    Write-Host $logEntry
    Add-Content -Path $LogFile -Value $logEntry
}

function Test-Port {
    param([int]$Port)
    $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
    return $connection
}

function Get-ProcessId {
    param([int]$Port)
    $netstat = netstat -ano | Select-String ":$Port " | Select-Object -First 1
    if ($netstat) {
        $parts = $netstat.Line -split '\s+'
        return $parts[-1]
    }
    return $null
}

function Stop-Port {
    param([int]$Port)
    $processId = Get-ProcessId -Port $Port
    if ($processId) {
        Write-Log "Killing process $processId on port $Port"
        try {
            Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
            Start-Sleep -Seconds 2
            # Double-check and kill any remaining processes
            for ($i = 0; $i -lt 3; $i++) {
                $remainingPid = Get-ProcessId -Port $Port
                if ($remainingPid) {
                    Write-Log "Found remaining process $remainingPid on port $Port, killing..."
                    Stop-Process -Id $remainingPid -Force -ErrorAction SilentlyContinue
                    Start-Sleep -Seconds 1
                }
            }
        } catch {
            Write-Log "Warning: Could not kill process $processId on port $Port : $($_.Exception.Message)" "WARN"
        }
    } else {
        Write-Log "No process found on port $Port"
    }
}

function Start-ApiServer {
    Write-Log "Starting API Server on port $ApiPort..."

    # Set environment variables
    $env:PLANNER_API_SECRET = "test-secret-key"
    $env:POSTGRES_USER = "postgres"
    $env:POSTGRES_PASSWORD = "Arshiya@10"
    $env:POSTGRES_HOST = "localhost"
    $env:POSTGRES_PORT = "5432"
    $env:POSTGRES_DB = "mydatabase"

    # Determine which Python to use
    $pythonCmd = $null

    # Check if venv exists and has uvicorn
    if (Test-Path "venv\Scripts\python.exe") {
        $venvPython = "venv\Scripts\python.exe"
        $uvicornCheck = & $venvPython -c "import uvicorn; print('ok')" 2>&1
        if ($LASTEXITCODE -eq 0 -or $uvicornCheck -match "ok") {
            $pythonCmd = $venvPython
        }
    }

    # Fallback to .venv
    if (-not $pythonCmd -and (Test-Path ".venv\Scripts\python.exe")) {
        $dotVenvPython = ".venv\Scripts\python.exe"
        $uvicornCheck = & $dotVenvPython -c "import uvicorn; print('ok')" 2>&1
        if ($LASTEXITCODE -eq 0 -or $uvicornCheck -match "ok") {
            $pythonCmd = $dotVenvPython
        }
    }

    # Fallback to system Python
    if (-not $pythonCmd) {
        $pythonCmd = "python"
    }

    # Start API server in background
    $apiJob = Start-Job -ScriptBlock {
        param($pythonCmd, $port)
        try {
            & $pythonCmd -m uvicorn api.planner_api:app --host 0.0.0.0 --port $port --reload
        } catch {
            Write-Host "API Server failed to start: $($_.Exception.Message)"
        }
    } -ArgumentList $pythonCmd, $ApiPort

    # Wait for API server to start
    Start-Sleep -Seconds 2
    if (Test-Port -Port $ApiPort) {
        Write-Log "API Server started"
        return $true
    } else {
        Write-Log "API Server failed to start" "ERROR"
        return $false
    }
}

function Start-FrontendServer {
    Write-Log "Starting Frontend Server on port $FrontendPort..."

    # Start frontend server using Python's built-in HTTP server
    $frontendJob = Start-Job -ScriptBlock {
        param($port)
        try {
            # Change to project root directory and serve files
            Set-Location $using:PWD
            python -m http.server $port
        } catch {
            Write-Host "Frontend Server failed to start: $($_.Exception.Message)"
        }
    } -ArgumentList $FrontendPort

    # Wait for frontend server to start
    Start-Sleep -Seconds 2
    if (Test-Port -Port $FrontendPort) {
        Write-Log "Frontend Server started"
        return $true
    } else {
        Write-Log "Frontend Server failed to start" "ERROR"
        return $false
    }
}

function Check-Status {
    Write-Host "=== Server Status ===" -ForegroundColor Cyan

    # Check API server
    if (Test-Port -Port $ApiPort) {
        Write-Host "✓ API Server: RUNNING on port $ApiPort" -ForegroundColor Green
    } else {
        Write-Host "✗ API Server: STOPPED" -ForegroundColor Red
    }

    # Check Frontend server
    if (Test-Port -Port $FrontendPort) {
        Write-Host "✓ Frontend Server: RUNNING on port $FrontendPort" -ForegroundColor Green
        $processId = Get-ProcessId -Port $FrontendPort
        if ($processId) {
            Write-Host "  Process ID: $processId, Started: $(Get-Date -Format 'MM/dd/yyyy HH:mm:ss')" -ForegroundColor Gray
        }
    } else {
        Write-Host "✗ Frontend Server: STOPPED" -ForegroundColor Red
    }

    # Show recent log entries
    if (Test-Path $LogFile) {
        Write-Host ""
        Write-Host "=== Recent Log Entries ===" -ForegroundColor Cyan
        Get-Content $LogFile -Tail 10 | ForEach-Object {
            Write-Host $_ -ForegroundColor Gray
        }
    }
}

function Stop-AllServers {
    Write-Log "Stopping all servers..."

    Stop-Port -Port $ApiPort
    Stop-Port -Port $FrontendPort

    Write-Log "All servers stopped"
}

function Start-AllServers {
    Write-Log "Starting servers..."

    $apiStarted = Start-ApiServer
    $frontendStarted = Start-FrontendServer

    if ($apiStarted -and $frontendStarted) {
        Write-Log "All servers started successfully"
        Write-Host ""
        Write-Host "Servers started! Use .\manage_servers.ps1 -Status to check status." -ForegroundColor Green
        Write-Host "Frontend URL: http://localhost:$FrontendPort/frontend/task_page_example.html" -ForegroundColor Cyan
        Write-Host "API URL: http://localhost:$ApiPort" -ForegroundColor Cyan
        Write-Host "API Docs: http://localhost:$ApiPort/docs" -ForegroundColor Cyan
    } else {
        Write-Log "Some servers failed to start" "ERROR"
        exit 1
    }
}

# Main logic
if ($Status) {
    Check-Status
} elseif ($Stop) {
    Stop-AllServers
    Check-Status
} elseif ($Restart) {
    Write-Log "Restarting all servers..."
    Stop-AllServers
    Start-Sleep -Seconds 2
    Start-AllServers
} else {
    # Default action: start servers
    Write-Host "Planner Agent Server Management Tool" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\manage_servers.ps1              - Start both servers"
    Write-Host "  .\manage_servers.ps1 -Status       - Check server status"
    Write-Host "  .\manage_servers.ps1 -Stop         - Stop all servers"
    Write-Host "  .\manage_servers.ps1 -Restart      - Restart all servers"
    Write-Host ""

    Start-AllServers
}