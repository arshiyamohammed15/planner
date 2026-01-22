# PowerShell script to test coverage analysis endpoints
# Usage: .\test_coverage_endpoints.ps1 <plan_id>

param(
    [Parameter(Mandatory=$true)]
    [string]$PlanId
)

$baseUrl = "http://localhost:8000"

Write-Host "=== Testing Coverage Analysis Endpoints ===" -ForegroundColor Cyan
Write-Host "Plan ID: $PlanId" -ForegroundColor Yellow
Write-Host ""

# Step 1: Get authentication token
Write-Host "Step 1: Getting authentication token..." -ForegroundColor Yellow
$tokenResponse = Invoke-RestMethod -Uri "$baseUrl/token" -Method POST -ContentType "application/json"
$token = $tokenResponse.access_token
Write-Host "Token obtained: $($token.Substring(0, 20))..." -ForegroundColor Green
Write-Host ""

# Step 2: Test coverage gaps endpoint
Write-Host "Step 2: Testing GET /plans/$PlanId/coverage-gaps" -ForegroundColor Yellow
try {
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    $gapsResponse = Invoke-RestMethod -Uri "$baseUrl/plans/$PlanId/coverage-gaps" -Method GET -Headers $headers
    Write-Host "✓ Coverage Gaps Response:" -ForegroundColor Green
    Write-Host "  Plan ID: $($gapsResponse.plan_id)" -ForegroundColor White
    Write-Host "  Total Tasks: $($gapsResponse.total_tasks)" -ForegroundColor White
    Write-Host "  Missing Count: $($gapsResponse.missing_count)" -ForegroundColor White
    Write-Host "  Summary: $($gapsResponse.summary)" -ForegroundColor White
    if ($gapsResponse.gaps.Count -gt 0) {
        Write-Host "  Gaps:" -ForegroundColor White
        foreach ($gap in $gapsResponse.gaps) {
            Write-Host "    - $($gap.task_id): $($gap.test_type) (priority: $($gap.priority))" -ForegroundColor Cyan
        }
    }
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
Write-Host ""

# Step 3: Test comprehensive analysis endpoint
Write-Host "Step 3: Testing GET /plans/$PlanId/analysis" -ForegroundColor Yellow
try {
    $analysisResponse = Invoke-RestMethod -Uri "$baseUrl/plans/$PlanId/analysis" -Method GET -Headers $headers
    Write-Host "✓ Comprehensive Analysis Response:" -ForegroundColor Green
    Write-Host "  Plan ID: $($analysisResponse.plan_id)" -ForegroundColor White
    Write-Host "  Coverage Percentage: $($analysisResponse.coverage_percentage)%" -ForegroundColor White
    Write-Host "  Missing Test Types: $($analysisResponse.missing_test_types -join ', ')" -ForegroundColor White
    Write-Host "  Coverage by Type:" -ForegroundColor White
    foreach ($type in $analysisResponse.coverage_by_type.PSObject.Properties.Name) {
        $typeData = $analysisResponse.coverage_by_type.$type
        Write-Host "    $type : Total=$($typeData.total), Missing=$($typeData.missing), Complete=$($typeData.complete)" -ForegroundColor Cyan
    }
    Write-Host "  Prioritized Gaps: $($analysisResponse.prioritized_gaps.Count)" -ForegroundColor White
} catch {
    Write-Host "✗ Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "  Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "=== Test Complete ===" -ForegroundColor Cyan

