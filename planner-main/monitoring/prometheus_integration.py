"""
Prometheus integration for test coverage monitoring.

This module provides complete Prometheus setup for scraping and storing
coverage metrics from the Planner Agent.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional

from prometheus_client import Gauge, start_http_server, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry

from monitoring.coverage_tracking import get_coverage_trends
from monitoring.prometheus_exporter import CoverageMetricsExporter


class PrometheusCoverageIntegration:
    """
    Complete Prometheus integration for coverage monitoring.
    
    Exposes coverage metrics as Prometheus endpoints and provides
    configuration for Prometheus server setup.
    """

    def __init__(self, port: int = 8001):
        """
        Initialize Prometheus integration.
        
        Args:
            port: Port to expose metrics on (default: 8001)
        """
        self.port = port
        self.exporter = CoverageMetricsExporter(port=port)
        
        # Additional metrics for integration
        self.coverage_trend = Gauge(
            "test_coverage_trend",
            "Coverage trend (1 = increasing, -1 = decreasing, 0 = stable)",
            ["test_suite", "branch"]
        )
        self.coverage_last_updated = Gauge(
            "test_coverage_last_updated_timestamp",
            "Timestamp when coverage was last updated",
            ["test_suite", "branch"]
        )

    def start_metrics_server(self) -> None:
        """
        Start the Prometheus metrics HTTP server.
        
        This exposes metrics at http://localhost:{port}/metrics
        """
        self.exporter.start_server()
        print(f"Prometheus metrics server started on port {self.port}")
        print(f"Metrics endpoint: http://localhost:{self.port}/metrics")
        print(f"Prometheus scrape config: http://localhost:{self.port}/metrics")

    def update_all_metrics(self) -> None:
        """
        Update all Prometheus metrics from the latest coverage data.
        
        Handles database connection errors gracefully.
        """
        try:
            self.exporter.update_metrics()
        except Exception as e:
            # Log error but don't crash - metrics server should keep running
            print(f"Warning: Could not update metrics from database: {e}")
            # Set default values so Prometheus still gets metrics
            self.exporter.coverage_percentage.labels(
                test_suite="default", branch="main"
            ).set(0)
            return
        
        # Update additional metrics
        try:
            from sqlalchemy.orm import Session
            from database.postgresql_setup import get_sessionmaker
            from sqlalchemy import select, func
            from monitoring.coverage_metrics import CoverageMetricsModel
            
            sessionmaker = get_sessionmaker()
            session = sessionmaker()
            try:
                # Get latest metrics for trend calculation
                stmt = (
                    select(CoverageMetricsModel)
                    .order_by(CoverageMetricsModel.timestamp.desc())
                    .limit(2)
                )
                recent_metrics = list(session.scalars(stmt).all())
                
                if len(recent_metrics) >= 2:
                    latest = recent_metrics[0]
                    previous = recent_metrics[1]
                    
                    test_suite = latest.test_suite or "default"
                    branch = latest.branch_name or "main"
                    
                    # Calculate trend
                    if latest.coverage_percentage > previous.coverage_percentage:
                        trend = 1  # Increasing
                    elif latest.coverage_percentage < previous.coverage_percentage:
                        trend = -1  # Decreasing
                    else:
                        trend = 0  # Stable
                    
                    self.coverage_trend.labels(
                        test_suite=test_suite, branch=branch
                    ).set(trend)
                    
                    # Update last updated timestamp
                    self.coverage_last_updated.labels(
                        test_suite=test_suite, branch=branch
                    ).set(latest.timestamp.timestamp())
                elif len(recent_metrics) == 1:
                    latest = recent_metrics[0]
                    test_suite = latest.test_suite or "default"
                    branch = latest.branch_name or "main"
                    
                    self.coverage_last_updated.labels(
                        test_suite=test_suite, branch=branch
                    ).set(latest.timestamp.timestamp())
            finally:
                session.close()
        except Exception as e:
            # Silently handle errors - metrics server should keep running
            pass

    def run(self, update_interval: int = 60) -> None:
        """
        Run the Prometheus integration, updating metrics periodically.
        
        Args:
            update_interval: Seconds between metric updates (default: 60)
        """
        self.start_metrics_server()
        
        print(f"Updating metrics every {update_interval} seconds...")
        print("Press Ctrl+C to stop")
        
        while True:
            try:
                self.update_all_metrics()
                time.sleep(update_interval)
            except KeyboardInterrupt:
                print("\nStopping Prometheus integration...")
                break
            except Exception as e:
                print(f"Error updating metrics: {e}")
                time.sleep(update_interval)

    def get_metrics_output(self) -> str:
        """
        Get the current metrics in Prometheus format.
        
        Returns:
            String containing metrics in Prometheus text format
        """
        self.update_all_metrics()
        return generate_latest(REGISTRY).decode("utf-8")

    def verify_metrics(self) -> dict:
        """
        Verify that metrics are being exposed correctly.
        
        Returns:
            Dictionary with verification results
        """
        import urllib.request
        
        results = {
            "server_running": False,
            "metrics_accessible": False,
            "metrics_count": 0,
            "coverage_metrics_found": False,
            "errors": [],
        }
        
        try:
            # Check if server is running
            url = f"http://localhost:{self.port}/metrics"
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=5)
            
            results["server_running"] = True
            results["metrics_accessible"] = True
            
            # Parse metrics
            metrics_text = response.read().decode("utf-8")
            metrics_lines = [line for line in metrics_text.split("\n") if line and not line.startswith("#")]
            results["metrics_count"] = len(metrics_lines)
            
            # Check for coverage metrics
            coverage_metrics = [
                "test_coverage_percentage",
                "test_coverage_total_lines",
                "test_coverage_covered_lines",
                "test_coverage_missing_lines",
            ]
            
            found_metrics = [m for m in coverage_metrics if m in metrics_text]
            results["coverage_metrics_found"] = len(found_metrics) > 0
            results["found_metrics"] = found_metrics
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results


def create_prometheus_config(
    output_file: str = "prometheus.yml",
    scrape_interval: str = "15s",
    scrape_timeout: str = "10s",
    metrics_port: int = 8001,
) -> None:
    """
    Create Prometheus configuration file.
    
    Args:
        output_file: Path to output configuration file
        scrape_interval: How often to scrape metrics
        scrape_timeout: Timeout for scraping
        metrics_port: Port where metrics are exposed
    """
    config = {
        "global": {
            "scrape_interval": scrape_interval,
            "scrape_timeout": scrape_timeout,
            "evaluation_interval": "15s",
        },
        "rule_files": [
            "prometheus_alerts.yml"  # Reference to alert rules
        ],
        "scrape_configs": [
            {
                "job_name": "coverage-metrics",
                "scrape_interval": scrape_interval,
                "scrape_timeout": scrape_timeout,
                "metrics_path": "/metrics",
                "static_configs": [
                    {
                        "targets": [f"localhost:{metrics_port}"],
                        "labels": {
                            "service": "planner-agent",
                            "environment": "production"
                        }
                    }
                ]
            }
        ],
        "alerting": {
            "alertmanagers": [
                {
                    "static_configs": [
                        {
                            "targets": ["localhost:9093"]
                        }
                    ]
                }
            ]
        }
    }
    
    import yaml
    
    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"[OK] Prometheus configuration saved to: {output_file}")
    print(f"  Metrics endpoint: http://localhost:{metrics_port}/metrics")
    print(f"  Scrape interval: {scrape_interval}")


def create_alertmanager_config(
    output_file: str = "alertmanager.yml",
    slack_webhook: Optional[str] = None,
    email_smtp: Optional[str] = None,
    email_from: Optional[str] = None,
    email_to: Optional[str] = None,
) -> None:
    """
    Create Alertmanager configuration file.
    
    Args:
        output_file: Path to output configuration file
        slack_webhook: Slack webhook URL
        email_smtp: SMTP server for email notifications
        email_from: From email address
        email_to: Comma-separated list of email addresses
    """
    config = {
        "global": {
            "resolve_timeout": "5m"
        },
        "route": {
            "group_by": ["alertname", "cluster", "service"],
            "group_wait": "10s",
            "group_interval": "10s",
            "repeat_interval": "12h",
            "receiver": "default-receiver",
            "routes": [
                {
                    "match": {
                        "severity": "critical"
                    },
                    "receiver": "critical-receiver"
                }
            ]
        },
        "receivers": [
            {
                "name": "default-receiver",
                "webhook_configs": []
            },
            {
                "name": "critical-receiver",
                "webhook_configs": []
            }
        ]
    }
    
    # Add Slack if configured
    if slack_webhook:
        config["receivers"][0]["slack_configs"] = [
            {
                "api_url": slack_webhook,
                "channel": "#alerts",
                "title": "Coverage Alert",
                "text": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
            }
        ]
        config["receivers"][1]["slack_configs"] = config["receivers"][0]["slack_configs"]
    
    # Add email if configured
    if email_smtp and email_from and email_to:
        config["receivers"][0]["email_configs"] = [
            {
                "to": email_to,
                "from": email_from,
                "smarthost": email_smtp,
                "headers": {
                    "Subject": "Coverage Alert"
                }
            }
        ]
        config["receivers"][1]["email_configs"] = config["receivers"][0]["email_configs"]
    
    import yaml
    
    with open(output_file, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"[OK] Alertmanager configuration saved to: {output_file}")


def verify_prometheus_connection(prometheus_url: str = "http://localhost:9090") -> dict:
    """
    Verify that Prometheus is running and can scrape metrics.
    
    Args:
        prometheus_url: Prometheus server URL
    
    Returns:
        Dictionary with verification results
    """
    import urllib.request
    import json
    
    results = {
        "prometheus_running": False,
        "targets_healthy": False,
        "metrics_available": False,
        "errors": [],
    }
    
    try:
        # Check Prometheus health
        health_url = f"{prometheus_url}/-/healthy"
        req = urllib.request.Request(health_url)
        response = urllib.request.urlopen(req, timeout=5)
        results["prometheus_running"] = response.status == 200
        
        # Check targets
        targets_url = f"{prometheus_url}/api/v1/targets"
        req = urllib.request.Request(targets_url)
        response = urllib.request.urlopen(req, timeout=5)
        targets_data = json.loads(response.read().decode("utf-8"))
        
        active_targets = [
            t for t in targets_data.get("data", {}).get("activeTargets", [])
            if t.get("health") == "up"
        ]
        results["targets_healthy"] = len(active_targets) > 0
        results["active_targets"] = len(active_targets)
        
        # Check if coverage metrics are available
        query_url = f"{prometheus_url}/api/v1/query?query=test_coverage_percentage"
        req = urllib.request.Request(query_url)
        response = urllib.request.urlopen(req, timeout=5)
        query_data = json.loads(response.read().decode("utf-8"))
        
        if query_data.get("status") == "success":
            results["metrics_available"] = len(query_data.get("data", {}).get("result", [])) > 0
        
    except Exception as e:
        results["errors"].append(str(e))
    
    return results


def setup_prometheus_integration(
    metrics_port: int = 8001,
    prometheus_config_file: str = "prometheus.yml",
    alertmanager_config_file: str = "alertmanager.yml",
) -> None:
    """
    Complete setup of Prometheus integration.
    
    Creates configuration files and provides setup instructions.
    
    Args:
        metrics_port: Port for metrics endpoint
        prometheus_config_file: Path to Prometheus config
        alertmanager_config_file: Path to Alertmanager config
    """
    print("Setting up Prometheus integration...")
    print("=" * 70)
    
    # Create Prometheus configuration
    create_prometheus_config(
        output_file=prometheus_config_file,
        metrics_port=metrics_port,
    )
    
    # Create Alertmanager configuration
    create_alertmanager_config(output_file=alertmanager_config_file)
    
    print("\n" + "=" * 70)
    print("Prometheus Integration Setup Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Start the metrics exporter:")
    print(f"   python -m monitoring.prometheus_integration start --port {metrics_port}")
    print("\n2. Start Prometheus:")
    print(f"   prometheus --config.file={prometheus_config_file}")
    print("\n3. Start Alertmanager (optional):")
    print(f"   alertmanager --config.file={alertmanager_config_file}")
    print("\n4. Verify integration:")
    print("   python -m monitoring.prometheus_integration verify")
    print("\n5. Access Prometheus UI:")
    print("   http://localhost:9090")
    print("\n6. View metrics:")
    print(f"   http://localhost:{metrics_port}/metrics")


def main() -> None:
    """CLI entry point for Prometheus integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prometheus Integration for Coverage Monitoring")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start server command
    start_parser = subparsers.add_parser("start", help="Start Prometheus metrics server")
    start_parser.add_argument(
        "--port", type=int, default=8001,
        help="Port for metrics server (default: 8001)"
    )
    start_parser.add_argument(
        "--update-interval", type=int, default=60,
        help="Seconds between metric updates (default: 60)"
    )
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Create Prometheus configuration files")
    setup_parser.add_argument(
        "--port", type=int, default=8001,
        help="Metrics port (default: 8001)"
    )
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify Prometheus integration")
    verify_parser.add_argument(
        "--prometheus-url", type=str, default="http://localhost:9090",
        help="Prometheus server URL (default: http://localhost:9090)"
    )
    
    # Get metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Display current metrics")
    
    args = parser.parse_args()
    
    if args.command == "start":
        integration = PrometheusCoverageIntegration(port=args.port)
        integration.run(update_interval=args.update_interval)
    elif args.command == "setup":
        setup_prometheus_integration(metrics_port=args.port)
    elif args.command == "verify":
        integration = PrometheusCoverageIntegration()
        print("Verifying metrics endpoint...")
        metrics_result = integration.verify_metrics()
        print(f"Metrics server: {'OK' if metrics_result['server_running'] else 'FAILED'}")
        print(f"Metrics accessible: {'OK' if metrics_result['metrics_accessible'] else 'FAILED'}")
        print(f"Metrics count: {metrics_result['metrics_count']}")
        print(f"Coverage metrics found: {'YES' if metrics_result['coverage_metrics_found'] else 'NO'}")
        if metrics_result.get("found_metrics"):
            print(f"Found metrics: {', '.join(metrics_result['found_metrics'])}")
        
        print("\nVerifying Prometheus connection...")
        prometheus_result = verify_prometheus_connection(args.prometheus_url)
        print(f"Prometheus running: {'OK' if prometheus_result['prometheus_running'] else 'FAILED'}")
        print(f"Targets healthy: {'OK' if prometheus_result['targets_healthy'] else 'FAILED'}")
        if prometheus_result.get("active_targets"):
            print(f"Active targets: {prometheus_result['active_targets']}")
        print(f"Metrics available: {'OK' if prometheus_result['metrics_available'] else 'FAILED'}")
        
        if prometheus_result.get("errors"):
            print(f"\nErrors: {prometheus_result['errors']}")
    elif args.command == "metrics":
        integration = PrometheusCoverageIntegration()
        integration.update_all_metrics()
        print(integration.get_metrics_output())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


__all__ = [
    "PrometheusCoverageIntegration",
    "create_prometheus_config",
    "create_alertmanager_config",
    "verify_prometheus_connection",
    "setup_prometheus_integration",
]

