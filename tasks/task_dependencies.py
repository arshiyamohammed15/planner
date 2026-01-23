from __future__ import annotations

from typing import Iterable, List, Optional

from sqlalchemy.orm import Session

from database.data_access_layer import TestTaskDAL
from tasks.test_task_model import TaskStatus


class TaskDependencies:
    """
    Manage task dependencies and enforce readiness before progress/completion.
    """

    def __init__(self, session: Session):
        self.session = session
        self.dal = TestTaskDAL(session)

    def set_dependencies(self, task_id: str, dependencies: Iterable[str]) -> bool:
        task = self.dal.get_task(task_id)
        if not task:
            return False
        task.dependencies = list(dependencies)
        self.session.commit()
        return True

    def get_dependencies(self, task_id: str) -> Optional[List[str]]:
        task = self.dal.get_task(task_id)
        if not task:
            return None
        return task.dependencies

    def dependencies_complete(self, task_id: str) -> Optional[bool]:
        task = self.dal.get_task(task_id)
        if not task:
            return None
        deps = task.dependencies
        if not deps:
            return True

        for dep_id in deps:
            dep = self.dal.get_task(dep_id)
            if not dep or dep.status != TaskStatus.DONE:
                return False
        return True

    def mark_in_progress_if_ready(self, task_id: str) -> bool:
        """
        Move task to IN_PROGRESS only if all dependencies are DONE.
        Returns True if status updated, False otherwise.
        """
        task = self.dal.get_task(task_id)
        if not task:
            return False
        ready = self.dependencies_complete(task_id)
        if not ready:
            return False
        task.status = TaskStatus.IN_PROGRESS
        self.session.commit()
        return True

    def complete_task(self, task_id: str) -> bool:
        """
        Mark task DONE only if dependencies are DONE.
        Returns True if status updated, False otherwise.
        """
        task = self.dal.get_task(task_id)
        if not task:
            return False
        ready = self.dependencies_complete(task_id)
        if not ready:
            return False
        task.status = TaskStatus.DONE
        self.session.commit()
        return True


__all__ = ["TaskDependencies"]

