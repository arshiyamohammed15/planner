# PowerShell script for automated API testing
# Usage: .\test_api_scenarios.ps1

param(
    [string]$BaseUrl = "http://localhost:8000",
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"
$testResults = @()
$passed = 0
$failed = 0
$skipped = 0

function Write-TestResult {
    param(
        [string]$TestId,
        [string]$TestName,
        [string]$Status,
        [string]$Message = ""
    )
    
    $color = switch ($Status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "SKIP" { "Yellow" }
        default { "White" }
    }
    
    Write-Host "[$Status] $TestId - $TestName" -ForegroundColor $color
    if ($Message) {
        Write-Host "  $Message" -ForegroundColor Gray
    }
    
    $script:testResults += [PSCustomObject]@{
        TestId = $TestId
        TestName = $TestName
        Status = $Status
        Message = $Message
    }
    
    switch ($Status) {
        "PASS" { $script:passed++ }
        "FAIL" { $script:failed++ }
        "SKIP" { $script:skipped++ }
    }
}

function Get-AuthToken {
    param([string]$Subject = "test-user")
    
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/token?subject=$Subject&expires_minutes=60" -Method POST -ErrorAction Stop
        return $response.access_token
    } catch {
        Write-TestResult "TC-AUTH-001" "Generate Token" "FAIL" "Failed to generate token: $($_.Exception.Message)"
        return $null
    }
}

function Test-Authentication {
    Write-Host "`n=== Authentication Tests ===" -ForegroundColor Cyan
    
    # TC-AUTH-001: Generate Token
    $token = Get-AuthToken
    if ($token) {
        Write-TestResult "TC-AUTH-001" "Generate Token Successfully" "PASS"
    }
    
    # TC-AUTH-002: Generate Token with Custom Subject
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/token?subject=developer&expires_minutes=30" -Method POST -ErrorAction Stop
        if ($response.subject -eq "developer") {
            Write-TestResult "TC-AUTH-002" "Generate Token with Custom Subject" "PASS"
        } else {
            Write-TestResult "TC-AUTH-002" "Generate Token with Custom Subject" "FAIL" "Subject mismatch"
        }
    } catch {
        Write-TestResult "TC-AUTH-002" "Generate Token with Custom Subject" "FAIL" $_.Exception.Message
    }
    
    # TC-AUTH-003: Access Protected Endpoint Without Token
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/plan" -Method POST -Body (@{goal="test";feature="test"} | ConvertTo-Json) -ContentType "application/json" -ErrorAction Stop
        Write-TestResult "TC-AUTH-003" "Access Protected Endpoint Without Token" "FAIL" "Should have returned 401"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 401) {
            Write-TestResult "TC-AUTH-003" "Access Protected Endpoint Without Token" "PASS"
        } else {
            Write-TestResult "TC-AUTH-003" "Access Protected Endpoint Without Token" "FAIL" "Expected 401, got $($_.Exception.Response.StatusCode.value__)"
        }
    }
    
    # TC-AUTH-006: Access Public Endpoints
    try {
        $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -ErrorAction Stop
        Write-TestResult "TC-AUTH-006" "Access Public Endpoints" "PASS" "Health endpoint accessible"
    } catch {
        Write-TestResult "TC-AUTH-006" "Access Public Endpoints" "FAIL" $_.Exception.Message
    }
    
    return $token
}

function Test-PlanGeneration {
    param([string]$Token)
    
    Write-Host "`n=== Plan Generation Tests ===" -ForegroundColor Cyan
    $headers = @{Authorization = "Bearer $Token"}
    
    # TC-PLAN-001: Generate Plan with Basic Template
    try {
        $body = @{
            goal = "Ensure secure authentication"
            feature = "User Authentication"
            template_name = "basic"
            save_to_database = $true
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$BaseUrl/plan" -Method POST -Headers $headers -Body $body -ContentType "application/json" -ErrorAction Stop
        if ($response.tasks.Count -eq 3) {
            Write-TestResult "TC-PLAN-001" "Generate Plan with Basic Template" "PASS" "Plan created with 3 tasks"
            $script:testPlanId = $response.plan_id
            $script:testTaskId = $response.tasks[0].id
        } else {
            Write-TestResult "TC-PLAN-001" "Generate Plan with Basic Template" "FAIL" "Expected 3 tasks, got $($response.tasks.Count)"
        }
    } catch {
        Write-TestResult "TC-PLAN-001" "Generate Plan with Basic Template" "FAIL" $_.Exception.Message
    }
    
    # TC-PLAN-002: Generate Plan with Complex Template
    try {
        $body = @{
            goal = "Verify payment processing"
            feature = "Payment Processing"
            template_name = "complex"
            save_to_database = $true
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$BaseUrl/plan" -Method POST -Headers $headers -Body $body -ContentType "application/json" -ErrorAction Stop
        if ($response.tasks.Count -eq 6) {
            Write-TestResult "TC-PLAN-002" "Generate Plan with Complex Template" "PASS" "Plan created with 6 tasks"
        } else {
            Write-TestResult "TC-PLAN-002" "Generate Plan with Complex Template" "FAIL" "Expected 6 tasks, got $($response.tasks.Count)"
        }
    } catch {
        Write-TestResult "TC-PLAN-002" "Generate Plan with Complex Template" "FAIL" $_.Exception.Message
    }
    
    # TC-PLAN-009: Generate Plan with Missing Goal
    try {
        $body = @{
            feature = "User Authentication"
            template_name = "basic"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$BaseUrl/plan" -Method POST -Headers $headers -Body $body -ContentType "application/json" -ErrorAction Stop
        Write-TestResult "TC-PLAN-009" "Generate Plan with Missing Goal" "FAIL" "Should have returned validation error"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 422 -or $_.Exception.Message -match "required") {
            Write-TestResult "TC-PLAN-009" "Generate Plan with Missing Goal" "PASS"
        } else {
            Write-TestResult "TC-PLAN-009" "Generate Plan with Missing Goal" "FAIL" "Expected validation error"
        }
    }
    
    # TC-PLAN-011: Generate Plan with Blank Goal
    try {
        $body = @{
            goal = ""
            feature = "User Authentication"
            template_name = "basic"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$BaseUrl/plan" -Method POST -Headers $headers -Body $body -ContentType "application/json" -ErrorAction Stop
        Write-TestResult "TC-PLAN-011" "Generate Plan with Blank Goal" "FAIL" "Should have returned validation error"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 422 -or $_.Exception.Message -match "empty") {
            Write-TestResult "TC-PLAN-011" "Generate Plan with Blank Goal" "PASS"
        } else {
            Write-TestResult "TC-PLAN-011" "Generate Plan with Blank Goal" "FAIL" "Expected validation error"
        }
    }
    
    # TC-PLAN-013: Generate Plan with Invalid Template
    try {
        $body = @{
            goal = "Test invalid template"
            feature = "Test Feature"
            template_name = "invalid_template"
            save_to_database = $true
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "$BaseUrl/plan" -Method POST -Headers $headers -Body $body -ContentType "application/json" -ErrorAction Stop
        Write-TestResult "TC-PLAN-013" "Generate Plan with Invalid Template" "FAIL" "Should have returned 400 error"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 400) {
            Write-TestResult "TC-PLAN-013" "Generate Plan with Invalid Template" "PASS"
        } else {
            Write-TestResult "TC-PLAN-013" "Generate Plan with Invalid Template" "FAIL" "Expected 400 error"
        }
    }
}

function Test-TaskRetrieval {
    param([string]$Token, [string]$TaskId)
    
    Write-Host "`n=== Task Retrieval Tests ===" -ForegroundColor Cyan
    $headers = @{Authorization = "Bearer $Token"}
    
    if (-not $TaskId) {
        Write-TestResult "TC-TASK-001" "Get Task Details" "SKIP" "No task ID available"
        return
    }
    
    # TC-TASK-001: Get Task Details
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/tasks/$TaskId" -Method GET -Headers $headers -ErrorAction Stop
        if ($response.id -and $response.description) {
            Write-TestResult "TC-TASK-001" "Get Task Details Successfully" "PASS"
        } else {
            Write-TestResult "TC-TASK-001" "Get Task Details Successfully" "FAIL" "Missing required fields"
        }
    } catch {
        Write-TestResult "TC-TASK-001" "Get Task Details Successfully" "FAIL" $_.Exception.Message
    }
    
    # TC-TASK-002: Get Non-Existent Task
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/tasks/non-existent-task-id" -Method GET -Headers $headers -ErrorAction Stop
        Write-TestResult "TC-TASK-002" "Get Non-Existent Task" "FAIL" "Should have returned 404"
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) {
            Write-TestResult "TC-TASK-002" "Get Non-Existent Task" "PASS"
        } else {
            Write-TestResult "TC-TASK-002" "Get Non-Existent Task" "FAIL" "Expected 404"
        }
    }
    
    # TC-TASK-003: List All Tasks
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/tasks" -Method GET -Headers $headers -ErrorAction Stop
        if ($response -is [array]) {
            Write-TestResult "TC-TASK-003" "List All Tasks" "PASS" "Retrieved $($response.Count) tasks"
        } else {
            Write-TestResult "TC-TASK-003" "List All Tasks" "FAIL" "Expected array"
        }
    } catch {
        Write-TestResult "TC-TASK-003" "List All Tasks" "FAIL" $_.Exception.Message
    }
}

function Test-Templates {
    param([string]$Token)
    
    Write-Host "`n=== Template Management Tests ===" -ForegroundColor Cyan
    $headers = @{Authorization = "Bearer $Token"}
    
    # TC-TEMPLATE-001: List Available Templates
    try {
        $response = Invoke-RestMethod -Uri "$BaseUrl/templates" -Method GET -Headers $headers -ErrorAction Stop
        if ($response -is [array] -and $response.Count -ge 4) {
            Write-TestResult "TC-TEMPLATE-001" "List Available Templates" "PASS" "Found $($response.Count) templates"
        } else {
            Write-TestResult "TC-TEMPLATE-001" "List Available Templates" "FAIL" "Expected at least 4 templates"
        }
    } catch {
        Write-TestResult "TC-TEMPLATE-001" "List Available Templates" "FAIL" $_.Exception.Message
    }
}

function Show-Summary {
    Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
    Write-Host "Total Tests: $($testResults.Count)" -ForegroundColor White
    Write-Host "Passed: $passed" -ForegroundColor Green
    Write-Host "Failed: $failed" -ForegroundColor Red
    Write-Host "Skipped: $skipped" -ForegroundColor Yellow
    
    if ($testResults.Count -gt 0) {
        $passRate = [math]::Round(($passed / $testResults.Count) * 100, 2)
        Write-Host "Pass Rate: $passRate%" -ForegroundColor $(if ($passRate -ge 80) { "Green" } else { "Red" })
    }
    
    if ($failed -gt 0) {
        Write-Host "`nFailed Tests:" -ForegroundColor Red
        $testResults | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
            Write-Host "  - $($_.TestId): $($_.TestName)" -ForegroundColor Red
            if ($_.Message) {
                Write-Host "    $($_.Message)" -ForegroundColor Gray
            }
        }
    }
}

# Main execution
Write-Host "=== Planner Agent API Test Suite ===" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl`n" -ForegroundColor Yellow

# Check if API is running
try {
    $health = Invoke-RestMethod -Uri "$BaseUrl/health" -Method GET -ErrorAction Stop
    Write-Host "[OK] API is running`n" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] API is not accessible at $BaseUrl" -ForegroundColor Red
    Write-Host "Please start the API server: .\start_api.ps1" -ForegroundColor Yellow
    exit 1
}

# Run tests
$token = Test-Authentication
if ($token) {
    Test-Templates -Token $token
    Test-PlanGeneration -Token $token
    Test-TaskRetrieval -Token $token -TaskId $script:testTaskId
}

Show-Summary

