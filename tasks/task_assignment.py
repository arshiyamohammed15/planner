from __future__ import annotations

from typing import Dict, Optional

from sqlalchemy.orm import Session

from database.data_access_layer import TestTaskDAL
from policies import get_policy_loader
from tasks.test_task_model import TestType


class TaskAssigner:
    """
    Assign tasks to team members based on test type.
    Uses policy-driven configuration from policies/assignment_policy.yaml.
    """

    def __init__(
        self,
        session: Session,
        role_map: Optional[Dict[TestType, str]] = None,
        policy_loader=None,
    ):
        """
        Initialize TaskAssigner.

        Args:
            session: Database session
            role_map: Optional override for role mapping (if None, uses policy)
            policy_loader: Optional policy loader (uses global if None)
        """
        self.session = session
        self.dal = TestTaskDAL(session)

        if role_map is not None:
            # Use provided role_map (backward compatibility)
            self.role_map: Dict[TestType, str] = role_map
            self._use_policy = False
        else:
            # Use policy-driven assignment
            if policy_loader is None:
                policy_loader = get_policy_loader()
            self.policy = policy_loader.get_config().assignment
            self._use_policy = True

    def assign_task(self, task_id: str) -> Optional[str]:
        """
        Assign the task to the mapped role based on its test type.
        Uses policy-driven assignment if configured, otherwise uses role_map.
        Returns the assignee string if assignment succeeded, otherwise None.
        """
        task = self.dal.get_task(task_id)
        if not task:
            return None

        if self._use_policy:
            # Use policy-driven assignment
            assignee = self.policy.get_role_for_test_type(task.test_type)
        else:
            # Use legacy role_map
            assignee = self.role_map.get(task.test_type)

        if assignee is None:
            return None

        # Only assign and notify if owner is changing
        if task.owner != assignee:
            task.owner = assignee
            self.session.commit()
            
            # Notify the assigned user
            try:
                from notifications.notify import NotificationService
                notification_service = NotificationService()
                notification_service.notify_task_assigned(
                    user=assignee,
                    task_id=task.id,
                    task_description=task.description,
                    assigned_by=None  # Auto-assigned by system
                )
            except Exception as e:
                # Log error but don't fail assignment if notification fails
                print(f"Warning: Failed to send assignment notification: {e}")
        
        return assignee


__all__ = ["TaskAssigner"]

