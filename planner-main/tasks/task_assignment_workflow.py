from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy.orm import Session

from database.data_access_layer import TestTaskDAL
from tasks.task_assignment import TaskAssigner
from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


class TaskAssignmentWorkflow:
    """
    Orchestrate task creation and automatic assignment based on test type.
    """

    def __init__(self, session: Session):
        self.session = session
        self.dal = TestTaskDAL(session)
        self.assigner = TaskAssigner(session)

    def create_and_assign_task(
        self,
        *,
        id: str,
        description: str,
        test_type: TestType | str,
        owner: Optional[str] = None,
        dependencies: Optional[Iterable[str]] = None,
        status: TaskStatus | str = TaskStatus.PENDING,
        coverage_status: CoverageStatus | str = CoverageStatus.NOT_STARTED,
    ) -> Optional[TestTask]:
        """
        Create a task, optionally assign owner explicitly, otherwise auto-assign based on test_type.
        Returns the created task or None if creation failed.
        """
        # Create task
        task = self.dal.create_task(
            id=id,
            description=description,
            test_type=test_type,
            owner=owner,
            status=status,
            coverage_status=coverage_status,
            dependencies=dependencies or [],
        )
        self.session.commit()

        # Process @mentions in description first (takes precedence)
        try:
            from tasks.task_mentions import process_mentions_in_task_description
            mentions = process_mentions_in_task_description(
                task_id=task.id,
                description=description,
                session=self.session,
                notify=True
            )
            # If mentions were processed, task owner may have been set
            if mentions:
                self.session.commit()
        except Exception as e:
            # Log error but don't fail task creation if mention processing fails
            print(f"Warning: Failed to process mentions in task description: {e}")
        
        # Auto-assign if no owner provided (and no mentions set owner)
        if not task.owner:
            assigned = self.assigner.assign_task(task.id)
            if assigned:
                task.owner = assigned
                self.session.commit()

        return task


__all__ = ["TaskAssignmentWorkflow"]

