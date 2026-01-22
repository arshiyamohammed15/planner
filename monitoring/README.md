# Test Coverage Dashboard

This module provides infrastructure for tracking and visualizing test coverage metrics over time using Prometheus and Grafana.

## Overview

The dashboard system consists of:
- **Database Model**: Stores coverage metrics with timestamps for historical tracking
- **Prometheus Exporter**: Exposes metrics in Prometheus format for scraping
- **Grafana Dashboard**: Pre-configured dashboard for visualization

## Quick Start

### 1. Initialize Database

```bash
python -m monitoring.dashboard_setup init_db
```

This creates the `coverage_metrics` table in your database.

### 2. Record Coverage Metrics

```bash
python -m monitoring.dashboard_setup record_metric \
  --coverage 85.5 \
  --total 1000 \
  --covered 855 \
  --test-suite "unit-tests" \
  --branch-name "main"
```

### 3. Start Prometheus Exporter

```bash
python -m monitoring.dashboard_setup start_exporter
```

This starts a metrics server on port 8001 that Prometheus can scrape.

### 4. Setup Prometheus

1. Install Prometheus: https://prometheus.io/download/
2. Configure `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'coverage-metrics'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8001']
```

3. Start Prometheus:
```bash
prometheus --config.file=prometheus.yml
```

### 5. Setup Grafana

1. Install Grafana: https://grafana.com/grafana/download
2. Start Grafana:
```bash
grafana-server
```

3. Add Prometheus as data source:
   - URL: `http://localhost:9090`
   - Access: Server (default)

4. Import dashboard:
   - Go to Dashboards → Import
   - Upload `monitoring/grafana_dashboard.json`
   - Or paste the JSON content

## Usage Examples

### Record Coverage from pytest-cov

```bash
# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Extract coverage percentage and record
COVERAGE=$(pytest --cov=. --cov-report=term | grep TOTAL | awk '{print $NF}' | sed 's/%//')
TOTAL=$(pytest --cov=. --cov-report=term | grep TOTAL | awk '{print $2}')
COVERED=$(echo "$TOTAL * $COVERAGE / 100" | bc)

python -m monitoring.dashboard_setup record_metric \
  --coverage $COVERAGE \
  --total $TOTAL \
  --covered $COVERED \
  --test-suite "pytest"
```

### Get Latest Coverage

```bash
python -m monitoring.dashboard_setup latest
```

### View Setup Instructions

```bash
python -m monitoring.dashboard_setup instructions
```

## Dashboard Features

The Grafana dashboard includes:

1. **Coverage Percentage Over Time**: Line graph showing coverage trends
2. **Covered vs Missing Lines**: Comparison graph
3. **Current Coverage**: Stat panel with color-coded thresholds
4. **Total Lines**: Total lines of code tracked
5. **Branch Coverage**: Branch coverage percentage (if available)

## API Usage

### Record Metrics Programmatically

```python
from monitoring.prometheus_exporter import record_coverage_metric

metric = record_coverage_metric(
    coverage_percentage=85.5,
    total_lines=1000,
    covered_lines=855,
    missing_lines=145,
    branch_coverage=82.0,
    test_suite="unit-tests",
    commit_hash="abc123",
    branch_name="main"
)
```

### Start Exporter Programmatically

```python
from monitoring.prometheus_exporter import CoverageMetricsExporter

exporter = CoverageMetricsExporter(port=8001)
exporter.start_server()
exporter.update_metrics()  # Update metrics periodically
```

## Metrics Exposed

Prometheus metrics available at `http://localhost:8001/metrics`:

- `test_coverage_percentage`: Coverage percentage (0-100)
- `test_coverage_total_lines`: Total lines of code
- `test_coverage_covered_lines`: Covered lines
- `test_coverage_missing_lines`: Missing lines
- `test_coverage_branch_coverage`: Branch coverage percentage

All metrics include labels: `test_suite`, `branch`

## Database Schema

The `coverage_metrics` table stores:

- `id`: Primary key
- `timestamp`: When the metric was recorded
- `coverage_percentage`: Overall coverage percentage
- `total_lines`: Total lines of code
- `covered_lines`: Lines covered by tests
- `missing_lines`: Lines not covered
- `branch_coverage`: Branch coverage (optional)
- `test_suite`: Test suite name (optional)
- `commit_hash`: Git commit hash (optional)
- `branch_name`: Git branch name (optional)

## Integration with CI/CD

### Option 1: Using coverage_tracking module (Recommended)

```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: |
    pytest --cov=. --cov-report=xml --cov-report=term

- name: Record coverage metrics
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    python -c "
    from monitoring.coverage_tracking import track_coverage_from_file
    track_coverage_from_file(
        'coverage.xml',
        test_suite='pytest',
        commit_hash='${{ github.sha }}',
        branch_name='${{ github.ref_name }}'
    )
    "
```

### Option 2: Using CLI command

```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=. --cov-report=term

- name: Record coverage metrics
  run: |
    python -m monitoring.dashboard_setup record_metric \
      --coverage ${{ env.COVERAGE }} \
      --total ${{ env.TOTAL_LINES }} \
      --covered ${{ env.COVERED_LINES }} \
      --commit-hash ${{ github.sha }} \
      --branch-name ${{ github.ref_name }}
```

See `ci_cd_example.yml` for a complete example.

## Alerting

### Setup Coverage Alerts

The alerting system notifies teams when coverage drops below configured thresholds.

#### Check Alerts Manually

```bash
python -m monitoring.dashboard_setup check_alerts --threshold 80.0
```

#### Configure Alert Thresholds

```python
from monitoring.alerting import AlertConfig, CoverageAlertManager

alert_config = AlertConfig(
    threshold=80.0,  # Alert if below 80%
    duration_minutes=5,  # Must be below for 5 minutes
)

manager = CoverageAlertManager(alert_config=alert_config)
result = manager.check_and_alert()
```

#### Notification Channels

**Slack:**
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export SLACK_CHANNEL="#alerts"
```

**Email:**
```bash
export SMTP_SERVER="smtp.gmail.com"
export ALERT_EMAIL_FROM="alerts@example.com"
export ALERT_EMAIL_TO="team@example.com,manager@example.com"
```

**Webhook:**
```bash
export ALERT_WEBHOOK_URL="https://your-webhook-url.com/alerts"
```

#### Prometheus Alertmanager

1. Create alert rules:
```bash
python -m monitoring.dashboard_setup create_alert_rules
```

2. Configure Prometheus to use the rules file:
```yaml
# prometheus.yml
rule_files:
  - "prometheus_alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093
```

3. Configure Alertmanager notifications in `alertmanager.yml`

#### Grafana Alerts

Import `monitoring/grafana_alerts.json` into Grafana:
1. Go to Alerting → Alert Rules
2. Import the JSON configuration
3. Configure notification channels in Grafana

## Troubleshooting

### Database connection errors
- Ensure database is running and accessible
- Check `DATABASE_URL` or PostgreSQL environment variables

### Prometheus not scraping
- Verify exporter is running: `curl http://localhost:8001/metrics`
- Check Prometheus targets page: `http://localhost:9090/targets`

### Grafana no data
- Verify Prometheus data source is connected
- Check time range in Grafana (may need to adjust)
- Ensure metrics are being recorded and exported

### Alerts not triggering
- Verify coverage metrics are being recorded
- Check alert threshold configuration
- Ensure notification channels are properly configured
- Check alert duration (coverage must be below threshold for specified time)

## Grafana Integration

### Quick Setup

1. **Install Grafana**: https://grafana.com/grafana/download

2. **Start Grafana**:
   ```bash
   grafana-server
   ```
   Default credentials: `admin` / `admin`

3. **Complete Setup** (automated):

   **Bash/Linux/Mac:**
   ```bash
   python -m monitoring.grafana_integration setup \
     --grafana-url http://localhost:3000 \
     --prometheus-url http://localhost:9090
   ```

   **PowerShell/Windows:**
   ```powershell
   # Single line (recommended)
   python -m monitoring.grafana_integration setup --grafana-url http://localhost:3000 --prometheus-url http://localhost:9090
   
   # Or use the PowerShell script (easiest)
   .\monitoring\setup-grafana.ps1
   ```

   This will:
   - Create Prometheus data source in Grafana
   - Import the coverage dashboard
   - Configure automatic refresh (10 seconds)

### Manual Setup

#### 1. Create Prometheus Data Source

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration create-datasource \
  --prometheus-url http://localhost:9090
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration create-datasource --prometheus-url http://localhost:9090
```

Or manually in Grafana UI:
1. Go to Configuration → Data Sources
2. Add data source → Prometheus
3. URL: `http://localhost:9090`
4. Save & Test

#### 2. Import Dashboard

**Bash/Linux/Mac:**
```bash
python -m monitoring.grafana_integration import-dashboard \
  --title "Test Coverage Dashboard"
```

**PowerShell/Windows:**
```powershell
# Single line
python -m monitoring.grafana_integration import-dashboard --title "Test Coverage Dashboard"
```

Or manually:
1. Go to Dashboards → Import
2. Upload `monitoring/grafana_coverage_dashboard.json`
3. Select Prometheus data source
4. Import

### Dashboard Features

The coverage dashboard includes:

1. **Coverage Percentage Gauge** - Current coverage with color-coded thresholds
2. **Coverage Trend Over Time** - Line graph showing historical trends
3. **Covered vs Missing Lines** - Bar chart comparison
4. **Total Lines Stat** - Total lines of code
5. **Branch Coverage** - Branch coverage percentage gauge
6. **Coverage Trend Indicator** - Shows if coverage is increasing/decreasing/stable
7. **Coverage by Test Suite** - Table view with color coding
8. **Coverage Change** - Delta chart showing changes over time
9. **Last Updated** - Timestamp of last metric update

### Automatic Updates

The dashboard is configured to:
- **Auto-refresh**: Every 10 seconds
- **Time range**: Last 6 hours (configurable)
- **Real-time updates**: As Prometheus scrapes new metrics

### Verify Integration

```bash
python -m monitoring.grafana_integration verify \
  --grafana-url http://localhost:3000 \
  --username admin \
  --password admin
```

### Troubleshooting

#### Grafana not accessible
- Verify Grafana is running: `curl http://localhost:3000/api/health`
- Check default port: 3000
- Verify firewall settings

#### No data in dashboard
- Ensure Prometheus is scraping metrics
- Verify Prometheus data source is configured correctly
- Check time range in dashboard (may need to adjust)
- Verify metrics are being recorded: `curl http://localhost:8001/metrics`

#### Dashboard not updating
- Check auto-refresh is enabled (top right of dashboard)
- Verify Prometheus is scraping every 15 seconds
- Check metrics exporter is running and updating

#### Data source connection failed
- Verify Prometheus URL is correct
- Check Prometheus is accessible from Grafana server
- Test connection in Grafana UI: Configuration → Data Sources → Test

## Coverage Tracking Module

The `coverage_tracking.py` module provides functions to automatically track coverage trends:

### Basic Usage

```python
from monitoring.coverage_tracking import store_coverage

# Record coverage after CI/CD run
store_coverage(
    coverage_percentage=85.5,
    total_lines=1000,
    covered_lines=855,
    missing_lines=145,
    test_suite="pytest",
    # commit_hash and branch_name are auto-detected
)
```

### From Coverage Files

```python
from monitoring.coverage_tracking import track_coverage_from_file

# Automatically parse and record from coverage.xml
track_coverage_from_file("coverage.xml", test_suite="pytest")
```

### Run Pytest and Track

```python
from monitoring.coverage_tracking import track_coverage_from_pytest

# Run pytest with coverage and automatically record
metric = track_coverage_from_pytest(test_suite="pytest")
```

### Get Historical Trends

```python
from monitoring.coverage_tracking import get_coverage_trends

# Get coverage trends for last 30 days
trends = get_coverage_trends(days=30, test_suite="pytest")
for metric in trends:
    print(f"{metric.timestamp}: {metric.coverage_percentage}%")
```

## Files

- `dashboard_setup.py`: Main CLI and setup utilities
- `coverage_metrics.py`: Database model for storing metrics
- `coverage_tracking.py`: Functions for tracking coverage trends over time
- `prometheus_exporter.py`: Prometheus metrics exporter
- `grafana_dashboard.json`: Pre-configured Grafana dashboard
- `example_ci_integration.py`: Example usage scripts
- `ci_cd_example.yml`: Complete CI/CD integration example

