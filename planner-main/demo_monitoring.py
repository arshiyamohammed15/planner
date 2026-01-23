#!/usr/bin/env python3
"""
Python script to demonstrate Monitoring & Alerting features.
Usage: python demo_monitoring.py [--show-trends]
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta

from monitoring.alerting import AlertConfig, CoverageAlertManager
from monitoring.coverage_tracking import get_coverage_trends, store_coverage


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"[OK] {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"[WARNING] {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"[ERROR] {text}")


def demo_coverage_tracking() -> None:
    """Demonstrate coverage tracking."""
    print_header("Coverage Tracking Demonstration")
    
    # Record high coverage
    print("Recording high coverage (85.5%)...")
    try:
        metric1 = store_coverage(
            coverage_percentage=85.5,
            total_lines=1000,
            covered_lines=855,
            missing_lines=145,
            test_suite="unit-tests",
            branch_name="main",
        )
        print_success(f"Recorded: {metric1.coverage_percentage}% coverage")
    except Exception as e:
        print_error(f"Failed to record: {e}")
        return
    
    # Record medium coverage
    print("\nRecording medium coverage (75.0%)...")
    try:
        metric2 = store_coverage(
            coverage_percentage=75.0,
            total_lines=1000,
            covered_lines=750,
            missing_lines=250,
            test_suite="unit-tests",
            branch_name="main",
        )
        print_success(f"Recorded: {metric2.coverage_percentage}% coverage")
    except Exception as e:
        print_error(f"Failed to record: {e}")
        return
    
    # Record low coverage
    print("\nRecording low coverage (65.0%)...")
    try:
        metric3 = store_coverage(
            coverage_percentage=65.0,
            total_lines=1000,
            covered_lines=650,
            missing_lines=350,
            test_suite="unit-tests",
            branch_name="main",
        )
        print_success(f"Recorded: {metric3.coverage_percentage}% coverage")
    except Exception as e:
        print_error(f"Failed to record: {e}")
        return


def demo_alerting() -> None:
    """Demonstrate alerting system."""
    print_header("Alerting System Demonstration")
    
    # Test with 80% threshold
    print("Checking alerts with threshold 80%...")
    alert_config = AlertConfig(threshold=80.0, duration_minutes=0)  # 0 = check immediately
    manager = CoverageAlertManager(alert_config=alert_config)
    
    result = manager.check_and_alert()
    if result:
        print_warning(f"Alert triggered! Coverage: {result['coverage']}%")
        print(f"  Threshold: {result['threshold']}%")
        print(f"  Metric ID: {result['metric_id']}")
        print(f"  Timestamp: {result['timestamp']}")
    else:
        print_success("No alerts - coverage is above threshold")
    
    # Test with 70% threshold
    print("\nChecking alerts with threshold 70%...")
    alert_config = AlertConfig(threshold=70.0, duration_minutes=0)
    manager = CoverageAlertManager(alert_config=alert_config)
    
    result = manager.check_and_alert()
    if result:
        print_error(f"CRITICAL Alert triggered! Coverage: {result['coverage']}%")
        print(f"  Threshold: {result['threshold']}%")
        print(f"  Metric ID: {result['metric_id']}")
        print(f"  Timestamp: {result['timestamp']}")
    else:
        print_success("No alerts - coverage is above threshold")


def show_trends() -> None:
    """Show coverage trends."""
    print_header("Coverage Trends")
    
    try:
        trends = get_coverage_trends(days=30, test_suite="unit-tests")
        
        if not trends:
            print_warning("No coverage trends found")
            return
        
        print(f"Coverage Trends (Last 30 days): {len(trends)} metrics\n")
        
        for metric in trends[-10:]:  # Show last 10
            timestamp = metric.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            coverage = metric.coverage_percentage
            
            # Color code based on coverage
            if coverage >= 80:
                status = "✓"
            elif coverage >= 70:
                status = "⚠"
            else:
                status = "✗"
            
            print(f"  {status} {timestamp} - {coverage:.1f}% "
                  f"({metric.covered_lines}/{metric.total_lines} lines)")
        
        if len(trends) > 10:
            print(f"\n  ... and {len(trends) - 10} more metrics")
        
    except Exception as e:
        print_error(f"Failed to get trends: {e}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Demonstrate Monitoring & Alerting features"
    )
    parser.add_argument(
        "--show-trends",
        action="store_true",
        help="Show coverage trends instead of running full demo"
    )
    
    args = parser.parse_args()
    
    if args.show_trends:
        show_trends()
    else:
        print("Monitoring & Alerting Demonstration")
        print("=" * 60)
        
        try:
            demo_coverage_tracking()
            demo_alerting()
            
            print_header("Summary")
            print_success("Coverage tracking: Working")
            print_success("Alert system: Working")
            print("\nTo view trends, run: python demo_monitoring.py --show-trends")
            
        except Exception as e:
            print_error(f"Demonstration failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()

