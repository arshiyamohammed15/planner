"""Prometheus exporter for test coverage metrics."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from prometheus_client import Gauge, start_http_server
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database.postgresql_setup import get_engine, get_sessionmaker
from monitoring.coverage_metrics import CoverageMetricsModel


class CoverageMetricsExporter:
    """
    Prometheus exporter for test coverage metrics.
    
    Exposes coverage metrics as Prometheus gauges that can be scraped
    and visualized in Grafana.
    """

    def __init__(self, port: int = 8001):
        """
        Initialize the Prometheus exporter.
        
        Args:
            port: Port to expose metrics on (default: 8001)
        """
        self.port = port
        self.sessionmaker = get_sessionmaker()
        
        # Prometheus metrics
        self.coverage_percentage = Gauge(
            "test_coverage_percentage",
            "Test coverage percentage",
            ["test_suite", "branch"]
        )
        self.coverage_total_lines = Gauge(
            "test_coverage_total_lines",
            "Total lines of code",
            ["test_suite", "branch"]
        )
        self.coverage_covered_lines = Gauge(
            "test_coverage_covered_lines",
            "Covered lines of code",
            ["test_suite", "branch"]
        )
        self.coverage_missing_lines = Gauge(
            "test_coverage_missing_lines",
            "Missing lines of code",
            ["test_suite", "branch"]
        )
        self.coverage_branch_coverage = Gauge(
            "test_coverage_branch_coverage",
            "Branch coverage percentage",
            ["test_suite", "branch"]
        )

    def update_metrics(self) -> None:
        """
        Update Prometheus metrics from the latest coverage data in database.
        
        Handles database connection errors gracefully by setting default values.
        """
        try:
            session = self.sessionmaker()
            try:
                # Get the latest coverage metrics for each test suite/branch
                stmt = (
                    select(CoverageMetricsModel)
                    .order_by(CoverageMetricsModel.timestamp.desc())
                )
                latest_metrics = session.scalars(stmt).first()
                
                if latest_metrics:
                    test_suite = latest_metrics.test_suite or "default"
                    branch = latest_metrics.branch_name or "main"
                    
                    # Update Prometheus metrics
                    self.coverage_percentage.labels(
                        test_suite=test_suite, branch=branch
                    ).set(latest_metrics.coverage_percentage)
                    
                    self.coverage_total_lines.labels(
                        test_suite=test_suite, branch=branch
                    ).set(latest_metrics.total_lines)
                    
                    self.coverage_covered_lines.labels(
                        test_suite=test_suite, branch=branch
                    ).set(latest_metrics.covered_lines)
                    
                    self.coverage_missing_lines.labels(
                        test_suite=test_suite, branch=branch
                    ).set(latest_metrics.missing_lines)
                    
                    if latest_metrics.branch_coverage is not None:
                        self.coverage_branch_coverage.labels(
                            test_suite=test_suite, branch=branch
                        ).set(latest_metrics.branch_coverage)
            finally:
                session.close()
        except Exception as e:
            # If database connection fails, set default/zero values
            # This ensures Prometheus can still scrape metrics even without DB
            test_suite = "default"
            branch = "main"
            
            self.coverage_percentage.labels(
                test_suite=test_suite, branch=branch
            ).set(0)
            
            self.coverage_total_lines.labels(
                test_suite=test_suite, branch=branch
            ).set(0)
            
            self.coverage_covered_lines.labels(
                test_suite=test_suite, branch=branch
            ).set(0)
            
            self.coverage_missing_lines.labels(
                test_suite=test_suite, branch=branch
            ).set(0)
            
            # Re-raise only if it's not a connection error
            # This allows the metrics server to keep running
            if "connection" not in str(e).lower() and "authentication" not in str(e).lower():
                raise

    def start_server(self) -> None:
        """Start the Prometheus metrics HTTP server."""
        start_http_server(self.port)
        print(f"Prometheus metrics server started on port {self.port}")
        print(f"Metrics available at: http://localhost:{self.port}/metrics")

    def run(self, update_interval: int = 60) -> None:
        """
        Run the exporter, updating metrics periodically.
        
        Args:
            update_interval: Seconds between metric updates (default: 60)
        """
        import time
        
        self.start_server()
        
        while True:
            try:
                self.update_metrics()
                time.sleep(update_interval)
            except KeyboardInterrupt:
                print("\nStopping Prometheus exporter...")
                break
            except Exception as e:
                print(f"Error updating metrics: {e}")
                time.sleep(update_interval)


def record_coverage_metric(
    coverage_percentage: float,
    total_lines: int,
    covered_lines: int,
    missing_lines: int,
    branch_coverage: Optional[float] = None,
    test_suite: Optional[str] = None,
    commit_hash: Optional[str] = None,
    branch_name: Optional[str] = None,
    session: Optional[Session] = None,
) -> CoverageMetricsModel:
    """
    Record a coverage metric in the database.
    
    Args:
        coverage_percentage: Overall coverage percentage
        total_lines: Total lines of code
        covered_lines: Lines covered by tests
        missing_lines: Lines not covered by tests
        branch_coverage: Branch coverage percentage (optional)
        test_suite: Name of test suite (optional)
        commit_hash: Git commit hash (optional)
        branch_name: Git branch name (optional)
        session: Database session (optional, creates new if not provided)
    
    Returns:
        CoverageMetricsModel instance
    """
    should_close = False
    if session is None:
        sessionmaker = get_sessionmaker()
        session = sessionmaker()
        should_close = True
    
    try:
        metric = CoverageMetricsModel(
            timestamp=datetime.utcnow(),
            coverage_percentage=coverage_percentage,
            total_lines=total_lines,
            covered_lines=covered_lines,
            missing_lines=missing_lines,
            branch_coverage=branch_coverage,
            test_suite=test_suite,
            commit_hash=commit_hash,
            branch_name=branch_name,
        )
        if session:
            session.add(metric)
            session.commit()
        return metric
    finally:
        if should_close and session:
            session.close()


__all__ = ["CoverageMetricsExporter", "record_coverage_metric"]

