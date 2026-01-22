# Monitoring & Alerting Quick Start

Quick reference guide to see the monitoring and alerting features in action.

## Quick Demo (5 minutes)

### 1. Initialize Database
```powershell
python -m monitoring.dashboard_setup init_db --sqlite
```

### 2. Record Coverage Metrics
```powershell
# High coverage (no alert)
python -m monitoring.dashboard_setup record_metric --coverage 85.5 --total 1000 --covered 855 --test-suite "tests"

# Low coverage (triggers alert)
python -m monitoring.dashboard_setup record_metric --coverage 75.0 --total 1000 --covered 750 --test-suite "tests"
```

### 3. Check Alerts
```powershell
python -m monitoring.dashboard_setup check_alerts --threshold 80.0
```

**Expected Result:**
```
⚠️  ALERT TRIGGERED!
Coverage: 75.0% is below threshold: 80.0%
```

## Automated Demo

Run the automated demonstration script:

```powershell
.\demo_monitoring.ps1
```

This will:
- Initialize database
- Record multiple coverage levels
- Check alerts automatically
- Show results

## View Latest Coverage

```powershell
python -m monitoring.dashboard_setup latest
```

## View Trends

```powershell
python demo_monitoring.py --show-trends
```

## Start Metrics Exporter

```powershell
# Start exporter (runs on port 8001)
python -m monitoring.dashboard_setup start_exporter

# View metrics in browser
Start-Process "http://localhost:8001/metrics"
```

## Alert Thresholds

- **Warning**: Coverage < 80%
- **Critical**: Coverage < 70%
- **Drop Alert**: Coverage decreases by > 5% in 1 hour

## Common Commands

| Command | Description |
|---------|-------------|
| `init_db` | Initialize database tables |
| `record_metric` | Record a coverage metric |
| `check_alerts` | Check if alerts should trigger |
| `latest` | Get latest coverage metric |
| `start_exporter` | Start Prometheus metrics exporter |

## Troubleshooting

**Database connection error?**
```powershell
# Use SQLite instead
python -m monitoring.dashboard_setup init_db --sqlite
```

**No alerts triggered?**
- Verify metrics are recorded: `python -m monitoring.dashboard_setup latest`
- Check threshold: Coverage must be below threshold

## Next Steps

- See full guide: `monitoring_demo_guide.md`
- Integrate with CI/CD pipelines
- Set up Grafana dashboard for visualization

