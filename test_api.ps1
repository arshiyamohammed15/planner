# PowerShell script to test the Planner Agent API
# Usage: .\test_api.ps1

param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$ApiSecret = "test-secret-key"
)

Write-Host "=== Planner Agent API Testing ===" -ForegroundColor Cyan
Write-Host ""

# Set environment variable for API secret
$env:PLANNER_API_SECRET = $ApiSecret

# Generate auth token
Write-Host "Generating authentication token..." -ForegroundColor Yellow
$tokenScript = @"
from api.authentication import create_access_token
token = create_access_token('test-user')
print(token)
"@
$token = python -c $tokenScript
Write-Host "Token generated: $($token.Substring(0, 20))..." -ForegroundColor Green
Write-Host ""

# Test 1: Health Check (no auth required)
Write-Host "1. Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$ApiUrl/health" -Method Get
    Write-Host "   [OK] Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Health check failed: $_" -ForegroundColor Red
    Write-Host "   Make sure the API server is running!" -ForegroundColor Yellow
    exit 1
}

# Test 2: Generate Test Plan
Write-Host ""
Write-Host "2. Testing Generate Test Plan..." -ForegroundColor Yellow
$planPayload = @{
    goal = "Ensure checkout flow reliability"
    feature = "Checkout"
    constraints = @("PCI compliance", "limited staging data")
    owner = "qa-team"
} | ConvertTo-Json

try {
    $planResponse = Invoke-RestMethod -Uri "$ApiUrl/plan" `
        -Method Post `
        -Body $planPayload `
        -ContentType "application/json" `
        -Headers @{Authorization = "Bearer $token"}
    
    Write-Host "   [OK] Plan generated successfully!" -ForegroundColor Green
    Write-Host "   Plan ID: $($planResponse.plan_id)" -ForegroundColor Cyan
    Write-Host "   Feature: $($planResponse.feature)" -ForegroundColor Cyan
    Write-Host "   Tasks: $($planResponse.tasks.Count)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "   Tasks:" -ForegroundColor Yellow
    $planResponse.tasks | ForEach-Object {
        Write-Host "     - [$($_.test_type)] $($_.description)" -ForegroundColor White
    }
    
    # Save task ID for next test
    $global:testTaskId = $planResponse.tasks[0].id
} catch {
    Write-Host "   [ERROR] Failed to generate plan: $_" -ForegroundColor Red
}

# Test 3: Assign Task
Write-Host ""
Write-Host "3. Testing Assign Task..." -ForegroundColor Yellow
if ($global:testTaskId) {
    $assignPayload = @{
        task_id = $global:testTaskId
        owner = "qa-engineer"
    } | ConvertTo-Json
    
    try {
        $assignResponse = Invoke-RestMethod -Uri "$ApiUrl/assign_task" `
            -Method Post `
            -Body $assignPayload `
            -ContentType "application/json" `
            -Headers @{Authorization = "Bearer $token"}
        
        Write-Host "   [OK] Task assigned successfully!" -ForegroundColor Green
        Write-Host "   Task ID: $($assignResponse.task_id)" -ForegroundColor Cyan
        Write-Host "   Owner: $($assignResponse.owner)" -ForegroundColor Cyan
        Write-Host "   Message: $($assignResponse.message)" -ForegroundColor Cyan
    } catch {
        Write-Host "   [ERROR] Failed to assign task: $_" -ForegroundColor Red
    }
} else {
    Write-Host "   [SKIP] Skipping (no task ID from previous test)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== API Testing Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor Yellow
Write-Host "  Swagger UI: $ApiUrl/docs" -ForegroundColor White
Write-Host "  ReDoc: $ApiUrl/redoc" -ForegroundColor White