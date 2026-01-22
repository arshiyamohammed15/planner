from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional

from policies import get_policy_loader
from tasks.test_task_model import TestTask, TestType
from database.data_access_layer import TestTaskDAL


def _priority(task: TestTask, policy_loader=None) -> int:
    """
    Get priority for a task based on its test type.
    Higher value means higher priority in planning.
    Uses policy-driven configuration if available.
    """
    if policy_loader is None:
        policy_loader = get_policy_loader()
    policy = policy_loader.get_config().priority
    return policy.get_priority_for_test_type(task.test_type)


class TestPlanGenerator:
    """
    Generate an ordered test plan respecting dependencies and test-type priority.
    Uses policy-driven priority configuration.
    """

    __test__ = False  # prevent pytest from collecting

    def __init__(self, policy_loader=None):
        """
        Initialize TestPlanGenerator.

        Args:
            policy_loader: Optional policy loader (uses global if None)
        """
        if policy_loader is None:
            policy_loader = get_policy_loader()
        self.policy_loader = policy_loader

    def generate_plan(self, tasks: Iterable[TestTask]) -> List[TestTask]:
        tasks_by_id: Dict[str, TestTask] = {t.id: t for t in tasks}
        indegree: Dict[str, int] = {task_id: 0 for task_id in tasks_by_id}
        graph: Dict[str, List[str]] = defaultdict(list)

        # Build dependency graph (only consider dependencies present in the task set)
        for task in tasks_by_id.values():
            for dep_id in task.dependencies:
                if dep_id not in tasks_by_id:
                    # Missing dependency; skip so it doesn't block the plan
                    continue
                graph[dep_id].append(task.id)
                indegree[task.id] += 1

        # Initialize ready queue with zero-indegree tasks, sorted by priority (desc)
        def get_priority(task: TestTask) -> int:
            return _priority(task, self.policy_loader)

        ready = deque(
            sorted(
                (task for task_id, task in tasks_by_id.items() if indegree[task_id] == 0),
                key=get_priority,
                reverse=True,
            )
        )

        plan: List[TestTask] = []
        while ready:
            current = ready.popleft()
            plan.append(current)

            for neighbor_id in graph.get(current.id, []):
                indegree[neighbor_id] -= 1
                if indegree[neighbor_id] == 0:
                    ready.append(tasks_by_id[neighbor_id])

            # Keep ready queue ordered by priority
            if ready:
                ready = deque(sorted(ready, key=get_priority, reverse=True))

        if len(plan) != len(tasks_by_id):
            missing = set(tasks_by_id) - {t.id for t in plan}
            raise ValueError(
                f"Could not generate full plan due to dependency cycle or unresolved deps: {missing}"
            )

        return plan

    def generate_plan_from_db(self, dal: TestTaskDAL) -> List[TestTask]:
        """
        Fetch tasks from the database via DAL and generate an ordered plan.
        """
        tasks = dal.list_tasks()
        return self.generate_plan(tasks)


__all__ = ["TestPlanGenerator"]

