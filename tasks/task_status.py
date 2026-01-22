from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from database.data_access_layer import TestTaskDAL
from tasks.test_task_model import TaskStatus


class TaskStatusManager:
    """
    Manage task status transitions and persistence.
    """

    def __init__(self, session: Session):
        self.session = session
        self.dal = TestTaskDAL(session)

    def update_status(self, task_id: str, new_status: TaskStatus | str, changed_by: Optional[str] = None) -> bool:
        """
        Update task status and persist. Returns True if updated, False if task missing.
        
        Args:
            task_id: ID of the task
            new_status: New status to set
            changed_by: Username who changed the status (optional, for notifications)
        """
        task = self.dal.get_task(task_id)
        if not task:
            return False

        old_status = task.status
        task.status = TaskStatus(new_status) if isinstance(new_status, str) else new_status
        self.session.commit()
        
        # Notify task owner of status change
        if old_status != task.status:
            try:
                from notifications.notify import NotificationService
                notification_service = NotificationService()
                notification_service.notify_task_status_changed(
                    task_id=task_id,
                    task_description=task.description,
                    old_status=old_status,
                    new_status=task.status,
                    task_owner=task.owner,
                    changed_by=changed_by
                )
            except Exception as e:
                # Log error but don't fail status update if notification fails
                print(f"Warning: Failed to send status change notification: {e}")
        
        return True


__all__ = ["TaskStatusManager"]

