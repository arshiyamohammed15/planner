# Monitoring & Alerting Demo Guide

This guide demonstrates how the Planner Agent tracks test coverage over time and alerts when coverage drops below configured thresholds.

## Overview

The monitoring system:
- **Tracks** coverage metrics with timestamps
- **Stores** data in `coverage_metrics` database table
- **Alerts** when coverage drops below thresholds (80% warning, 70% critical)
- **Visualizes** trends via Prometheus and Grafana

## Prerequisites

- Planner Agent API running (or database accessible)
- Python environment with dependencies installed
- PostgreSQL database (or use SQLite for local testing)

## Step-by-Step Demonstration

### Step 1: Initialize Database

First, set up the database tables for storing coverage metrics.

**PowerShell:**
```powershell
# Using PostgreSQL (default)
python -m monitoring.dashboard_setup init_db

# OR using SQLite (for local testing without PostgreSQL)
python -m monitoring.dashboard_setup init_db --sqlite
```

**Expected Output:**
```
Initializing coverage metrics database tables...
Connected to PostgreSQL database
[OK] Database tables created successfully
  Table: coverage_metrics
```

### Step 2: Record High Coverage (No Alert)

Record coverage above the threshold to show normal operation.

**PowerShell:**
```powershell
python -m monitoring.dashboard_setup record_metric `
    --coverage 85.5 `
    --total 1000 `
    --covered 855 `
    --test-suite "unit-tests" `
    --branch-name "main"
```

**Expected Output:**
```
Recording coverage metric: 85.5% (855/1000 lines)
[OK] Metric recorded successfully
```

**Check Alerts:**
```powershell
python -m monitoring.dashboard_setup check_alerts --threshold 80.0
```

**Expected Output:**
```
Checking coverage alerts...
No alerts triggered - coverage is above threshold (85.5% >= 80.0%)
```

### Step 3: Record Low Coverage (Trigger Warning Alert)

Record coverage below the warning threshold (80%).

**PowerShell:**
```powershell
python -m monitoring.dashboard_setup record_metric `
    --coverage 75.0 `
    --total 1000 `
    --covered 750 `
    --test-suite "unit-tests" `
    --branch-name "main"
```

**Check Alerts:**
```powershell
python -m monitoring.dashboard_setup check_alerts --threshold 80.0
```

**Expected Output:**
```
⚠️  ALERT TRIGGERED!
Coverage: 75.0% is below threshold: 80.0%
Metric ID: 2
Timestamp: 2024-01-15T10:30:00
```

### Step 4: Record Critical Coverage (Trigger Critical Alert)

Record coverage below the critical threshold (70%).

**PowerShell:**
```powershell
python -m monitoring.dashboard_setup record_metric `
    --coverage 65.0 `
    --total 1000 `
    --covered 650 `
    --test-suite "unit-tests" `
    --branch-name "main"
```

**Check Alerts:**
```powershell
python -m monitoring.dashboard_setup check_alerts --threshold 70.0
```

**Expected Output:**
```
🚨 CRITICAL ALERT TRIGGERED!
Coverage: 65.0% is below critical threshold: 70.0%
Metric ID: 3
Timestamp: 2024-01-15T10:35:00
```

### Step 5: View Latest Coverage

Get the most recent coverage metric.

**PowerShell:**
```powershell
python -m monitoring.dashboard_setup latest
```

**Expected Output:**
```json
{
  "id": 3,
  "coverage_percentage": 65.0,
  "total_lines": 1000,
  "covered_lines": 650,
  "missing_lines": 350,
  "timestamp": "2024-01-15T10:35:00",
  "test_suite": "unit-tests",
  "branch_name": "main"
}
```

### Step 6: View Coverage Trends (Python)

Use the Python script to view historical trends.

**PowerShell:**
```powershell
python demo_monitoring.py --show-trends
```

**Expected Output:**
```
Coverage Trends (Last 30 days):
2024-01-15 10:35:00 - 65.0%
2024-01-15 10:30:00 - 75.0%
2024-01-15 10:25:00 - 85.5%
```

### Step 7: Start Prometheus Metrics Exporter

Start the metrics server to expose coverage data in Prometheus format.

**PowerShell:**
```powershell
# Start exporter (runs in foreground, press Ctrl+C to stop)
python -m monitoring.dashboard_setup start_exporter --port 8001
```

**In another terminal, view metrics:**
```powershell
# Open in browser
Start-Process "http://localhost:8001/metrics"

# OR view via curl
Invoke-WebRequest -Uri "http://localhost:8001/metrics" | Select-Object -ExpandProperty Content
```

**Expected Output (metrics format):**
```
# HELP test_coverage_percentage Test coverage percentage (0-100)
# TYPE test_coverage_percentage gauge
test_coverage_percentage{test_suite="unit-tests",branch="main"} 65.0

# HELP test_coverage_total_lines Total lines of code
# TYPE test_coverage_total_lines gauge
test_coverage_total_lines{test_suite="unit-tests",branch="main"} 1000.0
```

### Step 8: (Optional) View Grafana Dashboard

If Grafana is installed and configured:

1. **Setup Grafana:**
```powershell
.\monitoring\setup-grafana.ps1
```

2. **Access Dashboard:**
```
http://localhost:3000/dashboards
```

3. **View Coverage Visualization:**
   - Coverage percentage gauge
   - Coverage trend over time
   - Covered vs missing lines
   - Branch coverage

## Alert Types

The system supports three alert types:

1. **Low Test Coverage (< 80%)**: Warning alert
   - Triggers when coverage drops below 80%
   - Duration: Must be below threshold for 5 minutes

2. **Critical Test Coverage (< 70%)**: Critical alert
   - Triggers when coverage drops below 70%
   - Duration: Must be below threshold for 2 minutes

3. **Coverage Drop (> 5% decrease)**: Warning for significant drops
   - Triggers when coverage drops by more than 5% in 1 hour
   - Helps catch sudden regressions

## Automated Demonstration

For a fully automated demonstration, run:

```powershell
.\demo_monitoring.ps1
```

This script will:
- Initialize the database
- Record multiple coverage levels
- Check alerts automatically
- Display results with color-coded output

## Troubleshooting

### Database Connection Issues

If you see connection errors:
```powershell
# Use SQLite instead
python -m monitoring.dashboard_setup init_db --sqlite
```

### No Alerts Triggered

- Verify metrics are recorded: `python -m monitoring.dashboard_setup latest`
- Check threshold: Coverage must be below threshold
- Check duration: Coverage must be below threshold for specified time

### Metrics Exporter Not Starting

- Check if port 8001 is available
- Verify database connection
- Check for error messages in console

## Next Steps

- Integrate with CI/CD pipelines
- Configure notification channels (Slack, Email, Webhooks)
- Set up Prometheus and Grafana for visualization
- Customize alert thresholds for your project

