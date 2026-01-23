# Docker Run Script for Local Development (PowerShell)
# Usage: .\docker-run-dev.ps1

$ErrorActionPreference = "Stop"

$CONTAINER_NAME = "planner-agent-dev"
$IMAGE = "arshiyamohammed15/planner-agent:latest"
$HOST_PORT = 8000
$CONTAINER_PORT = 8000

# Stop and remove existing container if it exists
$existing = docker ps -aq -f name=$CONTAINER_NAME
if ($existing) {
    Write-Host "Stopping and removing existing container..." -ForegroundColor Yellow
    docker rm -f $CONTAINER_NAME
}

# Run the container
Write-Host "Starting Planner Agent container..." -ForegroundColor Cyan

docker run -d `
  --name $CONTAINER_NAME `
  -p "${HOST_PORT}:${CONTAINER_PORT}" `
  -e APP_ENV=development `
  -e POSTGRES_USER=$(if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "postgres" }) `
  -e POSTGRES_PASSWORD=$(if ($env:POSTGRES_PASSWORD) { $env:POSTGRES_PASSWORD } else { "postgres" }) `
  -e POSTGRES_HOST=$(if ($env:POSTGRES_HOST) { $env:POSTGRES_HOST } else { "localhost" }) `
  -e POSTGRES_PORT=$(if ($env:POSTGRES_PORT) { $env:POSTGRES_PORT } else { "5432" }) `
  -e POSTGRES_DB=$(if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "planner_dev" }) `
  -e SQLALCHEMY_ECHO=true `
  -e PLANNER_API_SECRET=$(if ($env:PLANNER_API_SECRET) { $env:PLANNER_API_SECRET } else { "dev-secret-key-change-me" }) `
  -e PLANNER_ALLOWED_ORIGINS=$(if ($env:PLANNER_ALLOWED_ORIGINS) { $env:PLANNER_ALLOWED_ORIGINS } else { "http://localhost:3000,http://localhost:8080" }) `
  $IMAGE

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to start container" -ForegroundColor Red
    exit 1
}

Write-Host "`nContainer started successfully!" -ForegroundColor Green
Write-Host "View logs: docker logs -f $CONTAINER_NAME" -ForegroundColor Cyan
Write-Host "Stop container: docker stop $CONTAINER_NAME" -ForegroundColor Cyan
Write-Host "Health check: Invoke-WebRequest http://localhost:$HOST_PORT/health" -ForegroundColor Cyan

