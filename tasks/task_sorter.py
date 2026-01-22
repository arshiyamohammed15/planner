from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, Iterable, List, Protocol, TypeVar

from tasks.test_task_model import TestTask


class TaskLike(Protocol):
    """Protocol for objects that can be sorted by TaskSorter."""
    id: str
    dependencies: List[str]


T = TypeVar('T', bound=TaskLike)


class TaskSorter:
    """
    Sort tasks topologically by dependencies.
    """

    __test__ = False  # prevent pytest collection

    def sort(self, tasks: Iterable[T]) -> List[T]:
        tasks_by_id: Dict[str, TestTask] = {t.id: t for t in tasks}
        indegree: Dict[str, int] = {tid: 0 for tid in tasks_by_id}
        graph: Dict[str, List[str]] = defaultdict(list)

        for task in tasks_by_id.values():
            for dep_id in task.dependencies:
                if dep_id not in tasks_by_id:
                    # Ignore missing dependencies to avoid blocking
                    continue
                graph[dep_id].append(task.id)
                indegree[task.id] += 1

        ready = deque([tasks_by_id[tid] for tid, deg in indegree.items() if deg == 0])
        ordered: List[TestTask] = []

        while ready:
            current = ready.popleft()
            ordered.append(current)
            for neighbor_id in graph.get(current.id, []):
                indegree[neighbor_id] -= 1
                if indegree[neighbor_id] == 0:
                    ready.append(tasks_by_id[neighbor_id])

        if len(ordered) != len(tasks_by_id):
            missing = set(tasks_by_id) - {t.id for t in ordered}
            raise ValueError(
                f"Cycle or unresolved dependencies prevented full ordering: {missing}"
            )

        return ordered


__all__ = ["TaskSorter"]

