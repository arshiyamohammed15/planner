# Grafana Integration Setup Guide

## Overview

This guide explains how to set up Grafana to visualize test coverage metrics from Prometheus.

## Prerequisites

1. **Grafana installed**: https://grafana.com/grafana/download
2. **Prometheus running**: Metrics should be available at `http://localhost:9090`
3. **Metrics exporter running**: `python -m monitoring.prometheus_integration start`

> **Note for Windows/PowerShell users**: PowerShell does not support bash-style line continuation (`\`). Use single-line commands or backticks (`` ` ``) for line continuation. See examples below.

## Quick Start

### Automated Setup

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration setup \
  --grafana-url http://localhost:3000 \
  --username admin \
  --password admin \
  --prometheus-url http://localhost:9090
```

**PowerShell/Windows:**
```powershell
# Option 1: Single line (recommended)
python -m monitoring.grafana_integration setup --grafana-url http://localhost:3000 --username admin --password admin --prometheus-url http://localhost:9090

# Option 2: Using backticks for line continuation
python -m monitoring.grafana_integration setup `
  --grafana-url http://localhost:3000 `
  --username admin `
  --password admin `
  --prometheus-url http://localhost:9090

# Option 3: Use the PowerShell script (easiest)
.\monitoring\setup-grafana.ps1
```

This single command will:
- Connect to Grafana
- Create Prometheus data source
- Import the coverage dashboard
- Configure automatic refresh

### Manual Setup

#### Step 1: Start Grafana

```bash
# Linux/Mac
grafana-server

# Windows
# Run Grafana as a service or use the installer
```

Access Grafana at: http://localhost:3000
Default credentials: `admin` / `admin`

#### Step 2: Create Prometheus Data Source

**Option A: Using CLI**

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration create-datasource \
  --name Prometheus \
  --prometheus-url http://localhost:9090
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration create-datasource --name Prometheus --prometheus-url http://localhost:9090

# Or with backticks
python -m monitoring.grafana_integration create-datasource `
  --name Prometheus `
  --prometheus-url http://localhost:9090
```

**Option B: Using Grafana UI**
1. Go to Configuration → Data Sources
2. Click "Add data source"
3. Select "Prometheus"
4. Set URL: `http://localhost:9090`
5. Click "Save & Test"

#### Step 3: Import Dashboard

**Option A: Using CLI**

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration import-dashboard \
  --title "Test Coverage Dashboard"
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration import-dashboard --title "Test Coverage Dashboard"

# Or with backticks
python -m monitoring.grafana_integration import-dashboard `
  --title "Test Coverage Dashboard"
```

**Option B: Using Grafana UI**
1. Go to Dashboards → Import
2. Click "Upload JSON file"
3. Select `monitoring/grafana_coverage_dashboard.json`
4. Select Prometheus data source
5. Click "Import"

## Dashboard Configuration

### Auto-Refresh

The dashboard is configured to auto-refresh every 10 seconds. To change:

1. Open dashboard
2. Click refresh icon (top right)
3. Select desired interval (5s, 10s, 30s, 1m, etc.)

### Time Range

Default time range is "Last 6 hours". To change:

1. Click time picker (top right)
2. Select desired range:
   - Last 1 hour
   - Last 6 hours
   - Last 24 hours
   - Custom range

### Panel Configuration

Each panel can be customized:

1. Click panel title → Edit
2. Modify queries, visualization, or styling
3. Click "Apply" to save

## Dashboard Panels

### 1. Coverage Percentage Gauge
- **Type**: Gauge
- **Metric**: `test_coverage_percentage`
- **Thresholds**: 
  - Red: < 70%
  - Yellow: 70-80%
  - Green: > 80%

### 2. Coverage Trend Over Time
- **Type**: Time Series (Line Graph)
- **Metric**: `test_coverage_percentage`
- **Shows**: Historical coverage trends

### 3. Covered vs Missing Lines
- **Type**: Bar Chart
- **Metrics**: 
  - `test_coverage_covered_lines`
  - `test_coverage_missing_lines`

### 4. Total Lines Stat
- **Type**: Stat Panel
- **Metric**: `test_coverage_total_lines`

### 5. Branch Coverage
- **Type**: Gauge
- **Metric**: `test_coverage_branch_coverage`

### 6. Coverage Trend Indicator
- **Type**: Stat Panel
- **Metric**: `test_coverage_trend`
- **Values**:
  - 1 = Increasing (Green)
  - 0 = Stable (Blue)
  - -1 = Decreasing (Red)

### 7. Coverage by Test Suite
- **Type**: Table
- **Metric**: `test_coverage_percentage`
- **Shows**: Coverage breakdown by test suite and branch

### 8. Coverage Change
- **Type**: Time Series
- **Metric**: `test_coverage_percentage - test_coverage_percentage offset 1h`
- **Shows**: Coverage change over time (delta)

### 9. Last Updated
- **Type**: Stat Panel
- **Metric**: `test_coverage_last_updated_timestamp`
- **Shows**: When metrics were last updated

## Verification

### Check Grafana Connection

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration verify \
  --grafana-url http://localhost:3000 \
  --username admin \
  --password admin
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration verify --grafana-url http://localhost:3000 --username admin --password admin

# Or with backticks
python -m monitoring.grafana_integration verify `
  --grafana-url http://localhost:3000 `
  --username admin `
  --password admin
```

Expected output:
```
[OK] Connected to Grafana
  Version: 10.x.x
  Data sources: 1
    - Prometheus (prometheus)
```

### Check Dashboard

1. Open Grafana: http://localhost:3000
2. Go to Dashboards → Browse
3. Find "Test Coverage Dashboard"
4. Verify panels are displaying data

### Check Data Source

1. Go to Configuration → Data Sources
2. Click "Prometheus"
3. Click "Save & Test"
4. Should see: "Data source is working"

## Troubleshooting

### No Data in Dashboard

**Check Prometheus:**
```bash
# Verify Prometheus is running
curl http://localhost:9090/api/v1/query?query=test_coverage_percentage

# Check targets
# Open: http://localhost:9090/targets
```

**Check Metrics Exporter:**
```bash
# Verify metrics are exposed
curl http://localhost:8001/metrics | grep test_coverage
```

**Check Time Range:**
- Adjust dashboard time range to include when metrics were recorded
- Try "Last 24 hours" or custom range

### Dashboard Not Updating

1. **Check Auto-Refresh:**
   - Top right of dashboard
   - Should show refresh interval (e.g., "10s")

2. **Check Prometheus Scrape:**
   - Verify Prometheus is scraping every 15 seconds
   - Check Prometheus targets page

3. **Check Metrics Exporter:**
   - Ensure exporter is running: `python -m monitoring.prometheus_integration start`
   - Check for errors in exporter logs

### Data Source Connection Failed

1. **Verify Prometheus URL:**
   - Should be: `http://localhost:9090`
   - Test: `curl http://localhost:9090/api/health`

2. **Check Network:**
   - Grafana must be able to reach Prometheus
   - If running in Docker, use container names or host network

3. **Check Prometheus Access:**
   - Prometheus must be running
   - Check Prometheus logs for errors

### Authentication Errors

If you changed Grafana default credentials:

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration setup \
  --username your_username \
  --password your_password
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration setup --username your_username --password your_password

# Or with backticks
python -m monitoring.grafana_integration setup `
  --username your_username `
  --password your_password
```

## Advanced Configuration

### Custom Dashboard

Create a custom dashboard:

```python
from monitoring.grafana_integration import GrafanaIntegration

grafana = GrafanaIntegration()
dashboard = grafana.create_coverage_dashboard(
    dashboard_title="My Custom Dashboard"
)

# Modify dashboard as needed
# Then import
grafana.import_dashboard(dashboard)
```

### Multiple Dashboards

You can create multiple dashboards for different views:

**Bash/Linux/Mac:**
```bash
# Create dashboard for specific branch
python -m monitoring.grafana_integration import-dashboard \
  --title "Main Branch Coverage"
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration import-dashboard --title "Main Branch Coverage"

# Or with backticks
python -m monitoring.grafana_integration import-dashboard `
  --title "Main Branch Coverage"
```

### Dashboard Variables

Add variables for filtering:

1. Dashboard Settings → Variables
2. Add variable:
   - Name: `branch`
   - Type: Query
   - Data source: Prometheus
   - Query: `label_values(test_coverage_percentage, branch)`
3. Use in panel queries: `test_coverage_percentage{branch="$branch"}`

## Production Deployment

For production:

1. **Use HTTPS** for Grafana
2. **Set strong passwords** (change default admin password)
3. **Configure authentication** (LDAP, OAuth, etc.)
4. **Set up alerts** in Grafana (integrate with Alertmanager)
5. **Use persistent storage** for Grafana data
6. **Monitor Grafana** itself

## Files

- `grafana_integration.py` - Main integration module
- `grafana_coverage_dashboard.json` - Dashboard configuration
- `GRAFANA_SETUP.md` - This guide

