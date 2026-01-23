from __future__ import annotations

import pytest

from tasks.test_plan_generator import TestPlanGenerator
from tasks.test_plan_display import format_plan, render_plan_text
from tasks.test_task_model import TestTask, TestType, TaskStatus, CoverageStatus


def sample_tasks():
    return [
        TestTask(
            id="unit-1",
            description="Unit Test for Login",
            test_type=TestType.UNIT,
            owner="Developer",
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=[],
        ),
        TestTask(
            id="integration-1",
            description="Integration Test for Login + DB",
            test_type=TestType.INTEGRATION,
            owner="Developer",
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=["unit-1"],
        ),
        TestTask(
            id="e2e-1",
            description="E2E Test for Login Flow",
            test_type=TestType.E2E,
            owner="Tester",
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=["integration-1"],
        ),
    ]


def test_generate_test_plan_ordered():
    generator = TestPlanGenerator()
    plan = generator.generate_plan(sample_tasks())
    ids = [t.id for t in plan]
    assert ids == ["unit-1", "integration-1", "e2e-1"]


def test_format_plan_includes_fields():
    generator = TestPlanGenerator()
    plan = generator.generate_plan(sample_tasks())
    formatted = format_plan(plan)
    assert formatted[0]["description"] == "Unit Test for Login"
    assert formatted[0]["owner"] == "Developer"
    assert formatted[1]["dependencies"] == ["unit-1"]


def test_render_plan_text():
    generator = TestPlanGenerator()
    plan = generator.generate_plan(sample_tasks())
    text = render_plan_text(plan)
    assert "Test Plan:" in text
    assert "Unit Test for Login" in text
    assert "E2E Test for Login Flow" in text

