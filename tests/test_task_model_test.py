from __future__ import annotations

import pytest

from tasks.test_task_model import (
    CoverageStatus,
    TaskStatus,
    TestTask,
    TestType,
)


def test_defaults_and_ready_flag():
    task = TestTask(
        id="t1",
        description="Write unit tests for auth",
        test_type=TestType.UNIT,
    )
    assert task.status == TaskStatus.PENDING
    assert task.coverage_status == CoverageStatus.NOT_STARTED
    assert task.dependencies == []
    assert task.is_ready() is True


def test_dependencies_not_ready():
    task = TestTask(
        id="t2",
        description="Integration tests",
        test_type=TestType.INTEGRATION,
        dependencies=["t1"],
    )
    assert task.is_ready() is False
    # dependencies normalized to strings
    assert task.dependencies == ["t1"]


def test_test_type_string_coerces_to_enum():
    task = TestTask(
        id="t3",
        description="E2E checkout flow",
        test_type="e2e",
    )
    assert task.test_type == TestType.E2E


def test_invalid_test_type_raises():
    with pytest.raises(ValueError):
        TestTask(
            id="t4",
            description="Bad test type",
            test_type="not-a-valid-type",
        )


def test_update_status_and_owner():
    task = TestTask(
        id="t5",
        description="Security tests",
        test_type=TestType.SECURITY,
    )
    task.status = TaskStatus.IN_PROGRESS
    task.owner = "qa-lead"
    task.coverage_status = CoverageStatus.MISSING

    assert task.status == TaskStatus.IN_PROGRESS
    assert task.owner == "qa-lead"
    assert task.coverage_status == CoverageStatus.MISSING

