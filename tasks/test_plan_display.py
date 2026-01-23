from __future__ import annotations

from typing import Iterable, List, Dict, Any

from tasks.test_task_model import TestTask


DISPLAY_FIELDS = [
    "id",
    "description",
    "owner",
    "coverage_status",
    "dependencies",
    "test_type",
    "status",
]


def format_task(task: TestTask) -> Dict[str, Any]:
    """Return a serializable dict of key task details."""
    return {
        "id": task.id,
        "description": task.description,
        "owner": task.owner,
        "coverage_status": getattr(task.coverage_status, "value", task.coverage_status),
        "status": getattr(task.status, "value", task.status),
        "test_type": getattr(task.test_type, "value", task.test_type),
        "dependencies": list(task.dependencies),
    }


def format_plan(tasks: Iterable[TestTask]) -> List[Dict[str, Any]]:
    """Format a list of tasks for display."""
    return [format_task(t) for t in tasks]


def render_plan_text(tasks: Iterable[TestTask]) -> str:
    """
    Render a human-readable text representation of the test plan.
    """
    lines: List[str] = []
    lines.append("Test Plan:")
    lines.append("---------------------------------------")
    for task in tasks:
        deps = ", ".join(task.dependencies) if task.dependencies else "None"
        lines.append(f"Task {task.id}: {task.description}")
        lines.append(f"- Owner: {task.owner or 'Unassigned'}")
        lines.append(f"- Coverage Status: {getattr(task.coverage_status, 'value', task.coverage_status)}")
        lines.append(f"- Status: {getattr(task.status, 'value', task.status)}")
        lines.append(f"- Test Type: {getattr(task.test_type, 'value', task.test_type)}")
        lines.append(f"- Dependencies: {deps}")
        lines.append("")  # blank line between tasks
    return "\n".join(lines)


__all__ = ["format_task", "format_plan", "DISPLAY_FIELDS"]

