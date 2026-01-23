# Prometheus Integration Setup Guide

## Overview

This guide explains how to set up Prometheus to scrape and monitor test coverage metrics from the Planner Agent.

## Quick Setup

### 1. Create Configuration Files

```bash
python -m monitoring.prometheus_integration setup
```

This creates:
- `prometheus.yml` - Prometheus server configuration
- `alertmanager.yml` - Alertmanager configuration (optional)

### 2. Start Metrics Exporter

```bash
python -m monitoring.prometheus_integration start --port 8001
```

This starts the metrics server that Prometheus will scrape.

### 3. Start Prometheus

```bash
prometheus --config.file=prometheus.yml
```

Prometheus will be available at: http://localhost:9090

### 4. Verify Integration

```bash
python -m monitoring.prometheus_integration verify
```

## Configuration Details

### Prometheus Configuration (prometheus.yml)

The configuration includes:
- **Scrape interval**: 15 seconds
- **Target**: `localhost:8001/metrics`
- **Alert rules**: References `prometheus_alerts.yml`
- **Alertmanager**: Configured to send alerts to `localhost:9093`

### Metrics Exposed

The following metrics are available at `http://localhost:8001/metrics`:

- `test_coverage_percentage` - Coverage percentage (0-100)
- `test_coverage_total_lines` - Total lines of code
- `test_coverage_covered_lines` - Covered lines
- `test_coverage_missing_lines` - Missing lines
- `test_coverage_branch_coverage` - Branch coverage percentage
- `test_coverage_trend` - Coverage trend (1=increasing, -1=decreasing, 0=stable)
- `test_coverage_last_updated_timestamp` - Last update timestamp

All metrics include labels: `test_suite`, `branch`

## Prometheus Queries

### Get Current Coverage

```
test_coverage_percentage
```

### Get Coverage for Specific Branch

```
test_coverage_percentage{branch="main"}
```

### Get Coverage Trend

```
test_coverage_trend
```

### Calculate Coverage Change

```
test_coverage_percentage - test_coverage_percentage offset 1h
```

## Verification Steps

### 1. Check Metrics Endpoint

```bash
curl http://localhost:8001/metrics
```

You should see Prometheus-formatted metrics.

### 2. Check Prometheus Targets

1. Open http://localhost:9090/targets
2. Verify `coverage-metrics` target is "UP"
3. Check that metrics are being scraped

### 3. Query Metrics in Prometheus

1. Open http://localhost:9090
2. Go to "Graph" tab
3. Enter query: `test_coverage_percentage`
4. Click "Execute"

### 4. Verify Data Storage

1. Go to http://localhost:9090/graph
2. Query: `test_coverage_percentage[1h]`
3. Should show coverage data over the last hour

## Integration with Existing System

The Prometheus integration works with:

1. **Coverage Tracking** (`coverage_tracking.py`)
   - Records coverage metrics to database
   - Metrics are automatically exposed to Prometheus

2. **Prometheus Exporter** (`prometheus_exporter.py`)
   - Exposes metrics in Prometheus format
   - Updates metrics from database

3. **Alerting** (`alerting.py`)
   - Uses Prometheus metrics for alerts
   - Integrates with Alertmanager

## Troubleshooting

### Metrics endpoint not accessible

- Verify exporter is running: `python -m monitoring.prometheus_integration start`
- Check port is not in use: `netstat -an | findstr 8001`
- Test endpoint: `curl http://localhost:8001/metrics`

### Prometheus not scraping

- Check Prometheus targets: http://localhost:9090/targets
- Verify target is "UP" and not showing errors
- Check Prometheus logs for scrape errors

### No metrics in Prometheus

- Ensure coverage metrics are being recorded
- Verify database has coverage data
- Check exporter is updating metrics: `python -m monitoring.prometheus_integration metrics`

### Database connection errors

- Use SQLite for local testing: Ensure database is initialized
- For PostgreSQL: Set correct environment variables
- Check database is accessible

## Advanced Configuration

### Custom Scrape Interval

Edit `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: coverage-metrics
    scrape_interval: 30s  # Change to 30 seconds
```

### Multiple Targets

Add more targets in `prometheus.yml`:
```yaml
static_configs:
  - targets:
    - localhost:8001
    - localhost:8002  # Additional exporter
```

### Service Discovery

For dynamic target discovery, use service discovery instead of static_configs:
```yaml
scrape_configs:
  - job_name: coverage-metrics
    consul_sd_configs:
      - server: 'localhost:8500'
```

## Production Deployment

For production:

1. **Use persistent storage** for Prometheus data
2. **Configure retention** policies
3. **Set up Alertmanager** for alert routing
4. **Use HTTPS** for metrics endpoint (if exposed externally)
5. **Monitor Prometheus** itself (self-monitoring)

## Files

- `prometheus_integration.py` - Main integration module
- `prometheus.yml` - Prometheus server configuration
- `alertmanager.yml` - Alertmanager configuration
- `prometheus_alerts.yml` - Alert rules

