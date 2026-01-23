"""
Example script showing how to integrate coverage tracking in CI/CD pipelines.

This script demonstrates how to record coverage metrics after test runs.
"""

from __future__ import annotations

import os
import sys

from monitoring.coverage_tracking import (
    get_git_branch_name,
    get_git_commit_hash,
    store_coverage,
    track_coverage_from_file,
    track_coverage_from_pytest,
)


def example_manual_recording():
    """Example: Manually record coverage metrics."""
    print("Example: Manual coverage recording")
    
    metric = store_coverage(
        coverage_percentage=85.5,
        total_lines=1000,
        covered_lines=855,
        missing_lines=145,
        branch_coverage=82.0,
        test_suite="unit-tests",
    )
    
    print(f"Recorded metric ID: {metric.id}")
    print(f"Coverage: {metric.coverage_percentage}%")
    print(f"Timestamp: {metric.timestamp}")


def example_from_coverage_file():
    """Example: Record coverage from coverage.xml file."""
    print("\nExample: Recording from coverage.xml")
    
    if not os.path.exists("coverage.xml"):
        print("coverage.xml not found. Run pytest with --cov first.")
        return
    
    metric = track_coverage_from_file(
        "coverage.xml",
        test_suite="pytest",
    )
    
    print(f"Recorded metric ID: {metric.id}")
    print(f"Coverage: {metric.coverage_percentage}%")


def example_from_pytest():
    """Example: Run pytest and automatically track coverage."""
    print("\nExample: Running pytest and tracking coverage")
    
    try:
        metric = track_coverage_from_pytest(test_suite="pytest")
        print(f"Recorded metric ID: {metric.id}")
        print(f"Coverage: {metric.coverage_percentage}%")
        print(f"Total lines: {metric.total_lines}")
        print(f"Covered lines: {metric.covered_lines}")
    except Exception as e:
        print(f"Error: {e}")


def example_ci_cd_integration():
    """
    Example: CI/CD integration pattern.
    
    This shows how to integrate in GitHub Actions, GitLab CI, etc.
    """
    print("\nExample: CI/CD Integration Pattern")
    
    # In CI/CD, you would typically:
    # 1. Run tests with coverage
    # 2. Extract coverage metrics
    # 3. Record them
    
    # Get CI environment variables
    commit_hash = os.environ.get("GITHUB_SHA") or get_git_commit_hash()
    branch_name = os.environ.get("GITHUB_REF_NAME") or get_git_branch_name()
    
    print(f"Commit: {commit_hash}")
    print(f"Branch: {branch_name}")
    
    # Example: Record coverage after running tests
    # In real CI, you'd parse the coverage report
    metric = store_coverage(
        coverage_percentage=85.5,
        total_lines=1000,
        covered_lines=855,
        test_suite="ci-tests",
        commit_hash=commit_hash,
        branch_name=branch_name,
    )
    
    print(f"Recorded coverage for CI run: {metric.id}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "manual":
            example_manual_recording()
        elif command == "file":
            example_from_coverage_file()
        elif command == "pytest":
            example_from_pytest()
        elif command == "ci":
            example_ci_cd_integration()
        else:
            print(f"Unknown command: {command}")
            print("Usage: python example_ci_integration.py [manual|file|pytest|ci]")
    else:
        print("Coverage Tracking Examples")
        print("=" * 50)
        example_manual_recording()
        example_from_coverage_file()
        example_ci_cd_integration()

