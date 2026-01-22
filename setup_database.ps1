# Database Setup Script for Planner_1
# This script sets environment variables and creates database tables

Write-Host "Setting up database environment variables..." -ForegroundColor Cyan

# Option 1: Set individual environment variables
# Replace these values with your actual PostgreSQL credentials
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "Arshiya@10"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB = "mydatabase"

# Option 2: Or use a single DATABASE_URL (uncomment and use this instead)
# $env:DATABASE_URL = "postgresql+psycopg2://myuser:mypassword@localhost:5432/mydatabase"

Write-Host "Environment variables set:" -ForegroundColor Green
Write-Host "  POSTGRES_USER: $env:POSTGRES_USER"
Write-Host "  POSTGRES_HOST: $env:POSTGRES_HOST"
Write-Host "  POSTGRES_PORT: $env:POSTGRES_PORT"
Write-Host "  POSTGRES_DB: $env:POSTGRES_DB"
Write-Host ""

Write-Host "Creating database tables..." -ForegroundColor Cyan
python create_tables.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[OK] Database tables created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Verifying tables..." -ForegroundColor Cyan
    python verify_tables.py
    
    Write-Host ""
    Write-Host "Alternative verification methods:" -ForegroundColor Yellow
    Write-Host "  1. Run: python verify_tables.py"
    Write-Host "  2. Use pgAdmin or another PostgreSQL client"
    Write-Host "  3. If psql is installed, run:"
    $psqlCmd = "psql `"postgresql://$env:POSTGRES_USER:$env:POSTGRES_PASSWORD@$env:POSTGRES_HOST:$env:POSTGRES_PORT/$env:POSTGRES_DB`" -c `"\dt`""
    Write-Host "     $psqlCmd"
} else {
    Write-Host ""
    Write-Host "[ERROR] Failed to create tables. Please check:" -ForegroundColor Red
    Write-Host "  1. PostgreSQL is running"
    Write-Host "  2. Database '$env:POSTGRES_DB' exists"
    Write-Host "  3. Credentials are correct"
    Write-Host "  4. User has CREATE TABLE permissions"
}

