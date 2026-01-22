# Simple Docker Run Command for PowerShell
# Usage: .\docker-run-simple.ps1

# Single-line command (easiest for PowerShell)
docker run -d --name planner-agent-dev -p 8000:8000 -e APP_ENV=development -e PLANNER_API_SECRET=dev-secret-key-change-me arshiyamohammed15/planner-agent:latest

Write-Host "Container started! Check status: docker ps --filter name=planner-agent-dev" -ForegroundColor Green

