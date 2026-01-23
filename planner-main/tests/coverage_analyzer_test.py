from __future__ import annotations

from coverage.coverage_analyzer import CoverageAnalyzer
from tasks.test_task_model import CoverageStatus, TestTask, TestType


def test_find_missing_coverage_accepts_enum_and_string():
    tasks = [
        TestTask(
            id="t1",
            description="Unit covered",
            test_type=TestType.UNIT,
            coverage_status=CoverageStatus.COMPLETE,
        ),
        TestTask(
            id="t2",
            description="E2E missing",
            test_type=TestType.E2E,
            coverage_status=CoverageStatus.MISSING,
        ),
        TestTask(
            id="t3",
            description="Integration marked string",
            test_type=TestType.INTEGRATION,
            coverage_status="Not Covered",
        ),
    ]
    analyzer = CoverageAnalyzer()
    missing = analyzer.find_missing_coverage(tasks)
    ids = [t.id for t in missing]
    assert ids == ["t2", "t3"]


def test_prioritize_tests_orders_by_type_priority():
    tasks = [
        TestTask(
            id="unit-1",
            description="Unit missing",
            test_type=TestType.UNIT,
            coverage_status=CoverageStatus.MISSING,
        ),
        TestTask(
            id="e2e-1",
            description="E2E missing",
            test_type=TestType.E2E,
            coverage_status=CoverageStatus.MISSING,
        ),
        TestTask(
            id="integration-1",
            description="Integration missing",
            test_type=TestType.INTEGRATION,
            coverage_status=CoverageStatus.MISSING,
        ),
        TestTask(
            id="complete-1",
            description="Already covered",
            test_type=TestType.UNIT,
            coverage_status=CoverageStatus.COMPLETE,
        ),
    ]

    analyzer = CoverageAnalyzer()
    prioritized = analyzer.prioritize_tests(tasks)
    ids = [t.id for t in prioritized]
    # Expected order: E2E (highest), Integration, Unit
    assert ids == ["e2e-1", "integration-1", "unit-1"]


def test_prioritize_tests_ignores_non_missing():
    tasks = [
        TestTask(
            id="perf",
            description="Perf covered",
            test_type=TestType.PERFORMANCE,
            coverage_status=CoverageStatus.COMPLETE,
        ),
        TestTask(
            id="sec",
            description="Security missing",
            test_type=TestType.SECURITY,
            coverage_status=CoverageStatus.MISSING,
        ),
    ]
    analyzer = CoverageAnalyzer()
    prioritized = analyzer.prioritize_tests(tasks)
    assert len(prioritized) == 1
    assert prioritized[0].id == "sec"

