from __future__ import annotations

from sqlalchemy.orm import Session

from tasks.task_dependencies import TaskDependencies
from tasks.task_status import TaskStatusManager
from tasks.test_task_model import TaskStatus


class DependencyResolver:
    """
    Enforce dependency completion before starting or completing tasks.
    """

    def __init__(self, session: Session):
        self.session = session
        self.deps = TaskDependencies(session)
        self.status_mgr = TaskStatusManager(session)

    def can_start(self, task_id: str) -> bool:
        """
        Returns True if all dependencies are DONE (or there are none).
        """
        ready = self.deps.dependencies_complete(task_id)
        return bool(ready)

    def start_if_ready(self, task_id: str) -> bool:
        """
        Move task to IN_PROGRESS only if dependencies are DONE.
        Returns True if updated, False otherwise.
        """
        if not self.can_start(task_id):
            return False
        return self.status_mgr.update_status(task_id, TaskStatus.IN_PROGRESS)

    def complete_if_ready(self, task_id: str) -> bool:
        """
        Mark task DONE only if dependencies are DONE.
        Returns True if updated, False otherwise.
        """
        if not self.can_start(task_id):
            return False
        return self.status_mgr.update_status(task_id, TaskStatus.DONE)


__all__ = ["DependencyResolver"]

