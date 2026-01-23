"""
Dashboard setup for test coverage visualization.

This module sets up a basic dashboard infrastructure for displaying
test coverage trends over time using Prometheus and Grafana.

Usage:
    # Initialize database tables
    python -m monitoring.dashboard_setup init_db

    # Start Prometheus exporter
    python -m monitoring.dashboard_setup start_exporter

    # Record a coverage metric
    python -m monitoring.dashboard_setup record_metric --coverage 85.5 --total 1000 --covered 855
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import inspect

from database.postgresql_setup import Base, get_engine
from monitoring.coverage_metrics import CoverageMetricsModel

# Lazy import for prometheus_exporter (only needed for exporter commands)
def _get_exporter():
    try:
        from monitoring.prometheus_exporter import CoverageMetricsExporter, record_coverage_metric
        return CoverageMetricsExporter, record_coverage_metric
    except ImportError:
        raise ImportError(
            "prometheus_client not installed. Install with: pip install prometheus-client"
        )


def init_database(use_sqlite: bool = False, auto_fallback: bool = True) -> None:
    """
    Initialize database tables for coverage metrics.
    
    Args:
        use_sqlite: If True, use SQLite instead of PostgreSQL (for local dev)
        auto_fallback: If True, automatically fall back to SQLite if PostgreSQL fails
    """
    from sqlalchemy import create_engine, text
    
    print("Initializing coverage metrics database tables...")
    
    if use_sqlite:
        # Use SQLite for local development/testing
        db_path = os.path.join(os.path.dirname(__file__), "..", "coverage_metrics.db")
        engine = create_engine(f"sqlite:///{db_path}", echo=False)
        print(f"Using SQLite database: {db_path}")
    else:
        try:
            engine = get_engine()
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Connected to PostgreSQL database")
        except Exception as e:
            if auto_fallback:
                # Automatically fall back to SQLite
                error_msg = str(e).split('\n')[0] if '\n' in str(e) else str(e)
                print(f"⚠️  Failed to connect to PostgreSQL: {error_msg}")
                print("   Automatically falling back to SQLite for local development...")
                print("")
                db_path = os.path.join(os.path.dirname(__file__), "..", "coverage_metrics.db")
                engine = create_engine(f"sqlite:///{db_path}", echo=False)
                print(f"Using SQLite database: {db_path}")
                print("")
                print("Note: To use PostgreSQL, set environment variables:")
                print("   $env:POSTGRES_USER='your_user'")
                print("   $env:POSTGRES_PASSWORD='your_password'")
                print("   $env:POSTGRES_HOST='localhost'")
                print("   $env:POSTGRES_DB='mydatabase'")
            else:
                print(f"❌ Failed to connect to PostgreSQL: {e}")
                print("\nOptions:")
                print("1. Set correct PostgreSQL credentials:")
                print("   $env:POSTGRES_USER='your_user'")
                print("   $env:POSTGRES_PASSWORD='your_password'")
                print("   $env:POSTGRES_HOST='localhost'")
                print("   $env:POSTGRES_DB='mydatabase'")
                print("\n2. Use SQLite for local development:")
                print("   python -m monitoring.dashboard_setup init_db --sqlite")
                raise
    
    # Create tables
    Base.metadata.create_all(engine, tables=[CoverageMetricsModel.__table__])
    
    print("[OK] Database tables created successfully")
    print(f"  Table: {CoverageMetricsModel.__tablename__}")


def start_prometheus_exporter(port: int = 8001, update_interval: int = 60) -> None:
    """
    Start the Prometheus metrics exporter.
    
    Args:
        port: Port to expose metrics on
        update_interval: Seconds between metric updates
    """
    CoverageMetricsExporter, _ = _get_exporter()
    print(f"Starting Prometheus exporter on port {port}...")
    exporter = CoverageMetricsExporter(port=port)
    exporter.run(update_interval=update_interval)


def record_metric(
    coverage: float,
    total: int,
    covered: int,
    missing: int | None = None,
    branch_coverage: float | None = None,
    test_suite: str | None = None,
    commit_hash: str | None = None,
    branch_name: str | None = None,
) -> None:
    """
    Record a coverage metric in the database.
    
    Args:
        coverage: Coverage percentage
        total: Total lines of code
        covered: Covered lines
        missing: Missing lines (calculated if not provided)
        branch_coverage: Branch coverage percentage
        test_suite: Test suite name
        commit_hash: Git commit hash
        branch_name: Git branch name
    """
    _, record_coverage_metric = _get_exporter()
    
    if missing is None:
        missing = total - covered
    
    print(f"Recording coverage metric: {coverage}% ({covered}/{total} lines)")
    
    metric = record_coverage_metric(
        coverage_percentage=coverage,
        total_lines=total,
        covered_lines=covered,
        missing_lines=missing,
        branch_coverage=branch_coverage,
        test_suite=test_suite,
        commit_hash=commit_hash,
        branch_name=branch_name,
    )
    
    print(f"[OK] Metric recorded with ID: {metric.id}")


def get_latest_coverage() -> dict | None:
    """Get the latest coverage metrics from the database."""
    from sqlalchemy.orm import Session
    from database.postgresql_setup import get_sessionmaker
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    try:
        from sqlalchemy import select
        
        stmt = (
            select(CoverageMetricsModel)
            .order_by(CoverageMetricsModel.timestamp.desc())
            .limit(1)
        )
        latest = session.scalars(stmt).first()
        
        if latest:
            return {
                "id": latest.id,
                "timestamp": latest.timestamp.isoformat(),
                "coverage_percentage": latest.coverage_percentage,
                "total_lines": latest.total_lines,
                "covered_lines": latest.covered_lines,
                "missing_lines": latest.missing_lines,
                "branch_coverage": latest.branch_coverage,
                "test_suite": latest.test_suite,
                "branch_name": latest.branch_name,
            }
        return None
    finally:
        session.close()


def create_grafana_dashboard_config() -> dict:
    """
    Create Grafana dashboard configuration for test coverage visualization.
    
    Returns:
        Dictionary representing Grafana dashboard JSON
    """
    dashboard = {
        "dashboard": {
            "title": "Test Coverage Dashboard",
            "tags": ["coverage", "testing", "metrics"],
            "timezone": "browser",
            "panels": [
                {
                    "id": 1,
                    "title": "Coverage Percentage Over Time",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                    "targets": [
                        {
                            "expr": "test_coverage_percentage",
                            "legendFormat": "{{branch}} - {{test_suite}}",
                            "refId": "A"
                        }
                    ],
                    "yaxes": [
                        {
                            "format": "percent",
                            "label": "Coverage %",
                            "max": 100,
                            "min": 0
                        },
                        {"format": "short"}
                    ]
                },
                {
                    "id": 2,
                    "title": "Covered vs Missing Lines",
                    "type": "graph",
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                    "targets": [
                        {
                            "expr": "test_coverage_covered_lines",
                            "legendFormat": "Covered - {{branch}}",
                            "refId": "A"
                        },
                        {
                            "expr": "test_coverage_missing_lines",
                            "legendFormat": "Missing - {{branch}}",
                            "refId": "B"
                        }
                    ],
                    "yaxes": [
                        {"format": "short", "label": "Lines"},
                        {"format": "short"}
                    ]
                },
                {
                    "id": 3,
                    "title": "Current Coverage",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8},
                    "targets": [
                        {
                            "expr": "test_coverage_percentage",
                            "refId": "A"
                        }
                    ],
                    "options": {
                        "graphMode": "none",
                        "colorMode": "value",
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "yellow", "value": 70},
                                {"color": "green", "value": 80}
                            ]
                        }
                    },
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "min": 0,
                            "max": 100
                        }
                    }
                },
                {
                    "id": 4,
                    "title": "Total Lines",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 6, "y": 8},
                    "targets": [
                        {
                            "expr": "test_coverage_total_lines",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "short"
                        }
                    }
                },
                {
                    "id": 5,
                    "title": "Branch Coverage",
                    "type": "stat",
                    "gridPos": {"h": 4, "w": 6, "x": 12, "y": 8},
                    "targets": [
                        {
                            "expr": "test_coverage_branch_coverage",
                            "refId": "A"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percent",
                            "min": 0,
                            "max": 100
                        }
                    }
                }
            ],
            "refresh": "10s",
            "schemaVersion": 27,
            "version": 1
        }
    }
    return dashboard


def save_grafana_dashboard() -> None:
    """Save Grafana dashboard configuration to JSON file."""
    import json
    
    dashboard_dir = Path(__file__).parent
    dashboard_file = dashboard_dir / "grafana_dashboard.json"
    
    dashboard_config = create_grafana_dashboard_config()
    
    with open(dashboard_file, "w") as f:
        json.dump(dashboard_config, f, indent=2)
    
    print(f"[OK] Grafana dashboard configuration saved to: {dashboard_file}")
    print("  Import this file into Grafana to visualize coverage metrics")


def print_setup_instructions() -> None:
    """Print setup instructions for Prometheus and Grafana."""
    print("\n" + "=" * 70)
    print("Test Coverage Dashboard Setup Instructions")
    print("=" * 70)
    print("\n1. PROMETHEUS SETUP:")
    print("   - Install Prometheus: https://prometheus.io/download/")
    print("   - Add to prometheus.yml:")
    print("     scrape_configs:")
    print("       - job_name: 'coverage-metrics'")
    print("         static_configs:")
    print("           - targets: ['localhost:8001']")
    print("\n2. GRAFANA SETUP:")
    print("   - Install Grafana: https://grafana.com/grafana/download")
    print("   - Add Prometheus as data source:")
    print("     URL: http://localhost:9090")
    print("   - Import dashboard from: monitoring/grafana_dashboard.json")
    print("\n3. START EXPORTER:")
    print("   python -m monitoring.dashboard_setup start_exporter")
    print("\n4. RECORD METRICS:")
    print("   python -m monitoring.dashboard_setup record_metric \\")
    print("     --coverage 85.5 --total 1000 --covered 855")
    print("\n" + "=" * 70)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test Coverage Dashboard Setup"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init database command
    init_parser = subparsers.add_parser("init_db", help="Initialize database tables")
    init_parser.add_argument(
        "--sqlite", action="store_true",
        help="Use SQLite instead of PostgreSQL (for local development)"
    )
    init_parser.add_argument(
        "--no-auto-fallback", action="store_true",
        help="Don't automatically fall back to SQLite if PostgreSQL fails"
    )
    
    # Start exporter command
    exporter_parser = subparsers.add_parser("start_exporter", help="Start Prometheus exporter")
    exporter_parser.add_argument(
        "--port", type=int, default=8001,
        help="Port for metrics server (default: 8001)"
    )
    exporter_parser.add_argument(
        "--update-interval", type=int, default=60,
        help="Seconds between metric updates (default: 60)"
    )
    
    # Record metric command
    record_parser = subparsers.add_parser("record_metric", help="Record a coverage metric")
    record_parser.add_argument("--coverage", type=float, required=True, help="Coverage percentage")
    record_parser.add_argument("--total", type=int, required=True, help="Total lines")
    record_parser.add_argument("--covered", type=int, required=True, help="Covered lines")
    record_parser.add_argument("--missing", type=int, help="Missing lines (auto-calculated if not provided)")
    record_parser.add_argument("--branch-coverage", type=float, help="Branch coverage percentage")
    record_parser.add_argument("--test-suite", type=str, help="Test suite name")
    record_parser.add_argument("--commit-hash", type=str, help="Git commit hash")
    record_parser.add_argument("--branch-name", type=str, help="Git branch name")
    
    # Get latest command
    latest_parser = subparsers.add_parser("latest", help="Get latest coverage metrics")
    
    # Save Grafana dashboard
    dashboard_parser = subparsers.add_parser("save_dashboard", help="Save Grafana dashboard config")
    
    # Setup instructions
    instructions_parser = subparsers.add_parser("instructions", help="Print setup instructions")
    
    # Check alerts command
    alert_parser = subparsers.add_parser("check_alerts", help="Check coverage thresholds and send alerts")
    alert_parser.add_argument(
        "--threshold", type=float, default=80.0,
        help="Coverage threshold percentage (default: 80.0)"
    )
    alert_parser.add_argument(
        "--duration", type=int, default=5,
        help="Duration in minutes coverage must be below threshold (default: 5)"
    )
    alert_parser.add_argument(
        "--test-suite", type=str,
        help="Filter by test suite"
    )
    alert_parser.add_argument(
        "--branch-name", type=str,
        help="Filter by branch name"
    )
    
    # Create alert rules command
    rules_parser = subparsers.add_parser("create_alert_rules", help="Create Prometheus alert rules file")
    
    args = parser.parse_args()
    
    if args.command == "init_db":
        init_database(use_sqlite=args.sqlite, auto_fallback=not args.no_auto_fallback)
    elif args.command == "start_exporter":
        start_prometheus_exporter(port=args.port, update_interval=args.update_interval)
    elif args.command == "record_metric":
        record_metric(
            coverage=args.coverage,
            total=args.total,
            covered=args.covered,
            missing=args.missing,
            branch_coverage=args.branch_coverage,
            test_suite=args.test_suite,
            commit_hash=args.commit_hash,
            branch_name=args.branch_name,
        )
    elif args.command == "latest":
        latest = get_latest_coverage()
        if latest:
            import json
            print(json.dumps(latest, indent=2))
        else:
            print("No coverage metrics found")
    elif args.command == "save_dashboard":
        save_grafana_dashboard()
    elif args.command == "instructions":
        print_setup_instructions()
    elif args.command == "check_alerts":
        from monitoring.alerting import AlertConfig, CoverageAlertManager
        
        alert_config = AlertConfig(
            threshold=args.threshold,
            duration_minutes=args.duration,
            test_suite=getattr(args, "test_suite", None),
            branch_name=getattr(args, "branch_name", None),
        )
        
        manager = CoverageAlertManager(alert_config=alert_config)
        result = manager.check_and_alert()
        
        if result:
            print(f"[ALERT] Coverage below threshold!")
            print(f"  Current: {result['coverage']:.2f}%")
            print(f"  Threshold: {result['threshold']:.2f}%")
            print(f"  Notifications: {result['notifications']}")
        else:
            print("[OK] Coverage is above threshold")
    elif args.command == "create_alert_rules":
        from monitoring.alerting import create_prometheus_alert_rules
        create_prometheus_alert_rules("prometheus_alerts.yml")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

