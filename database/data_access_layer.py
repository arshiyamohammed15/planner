from __future__ import annotations

from typing import Iterable, List, Optional, Sequence

from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session

from database.models import CommentModel, CoverageModel, TestTaskModel
from tasks.task_sorter import TaskSorter
from tasks.test_task_model import CoverageStatus, TaskStatus, TestType


class TestTaskDAL:
    __test__ = False  # prevent pytest from collecting

    def __init__(self, session: Session):
        self.session = session

    # Create
    def create_task(
        self,
        *,
        id: str,
        description: str,
        test_type: TestType | str,
        status: TaskStatus | str = TaskStatus.PENDING,
        owner: Optional[str] = None,
        coverage_status: CoverageStatus | str = CoverageStatus.NOT_STARTED,
        dependencies: Optional[Iterable[str]] = None,
    ) -> TestTaskModel:
        task = TestTaskModel(
            id=id,
            description=description,
            test_type=TestType(test_type) if isinstance(test_type, str) else test_type,
            status=TaskStatus(status) if isinstance(status, str) else status,
            owner=owner,
            coverage_status=CoverageStatus(coverage_status)
            if isinstance(coverage_status, str)
            else coverage_status,
        )
        task.dependencies = list(dependencies or [])
        self.session.add(task)
        return task

    # Read
    def get_task(self, task_id: str) -> Optional[TestTaskModel]:
        stmt = select(TestTaskModel).where(TestTaskModel.id == task_id)
        return self.session.scalars(stmt).first()

    def list_tasks(self) -> List[TestTaskModel]:
        # #region agent log
        import json
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"data_access_layer.py:list_tasks","message":"About to execute list_tasks query","data":{"session_type":type(self.session).__name__},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
        # #endregion
        
        try:
            stmt = select(TestTaskModel)
            result = list(self.session.scalars(stmt).all())
            
            # #region agent log
            try:
                with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"data_access_layer.py:list_tasks","message":"list_tasks query successful","data":{"task_count":len(result)},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
            except: pass
            # #endregion
            
            return result
        except Exception as e:
            # #region agent log
            try:
                with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    error_str = str(e)
                    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"G","location":"data_access_layer.py:list_tasks","message":"list_tasks query failed","data":{"error_type":type(e).__name__,"error":error_str[:500],"has_password_auth":'password authentication' in error_str.lower(),"has_psycopg2":'psycopg2' in error_str,"has_operational":'OperationalError' in error_str},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
            except: pass
            # #endregion
            raise

    def plan_tasks(self) -> List[TestTaskModel]:
        """
        Return tasks ordered topologically by dependencies (and stable otherwise).
        """
        sorter = TaskSorter()
        return sorter.sort(self.list_tasks())

    # Update
    def update_task(
        self,
        task_id: str,
        *,
        description: Optional[str] = None,
        test_type: TestType | str | None = None,
        status: TaskStatus | str | None = None,
        owner: Optional[str] = None,
        coverage_status: CoverageStatus | str | None = None,
        dependencies: Optional[Iterable[str]] = None,
    ) -> Optional[TestTaskModel]:
        task = self.get_task(task_id)
        if not task:
            return None

        if description is not None:
            task.description = description
            # Process @mentions in updated description
            try:
                from tasks.task_mentions import process_mentions_in_task_description
                process_mentions_in_task_description(
                    task_id=task_id,
                    description=description,
                    session=self.session,
                    notify=True
                )
            except Exception as e:
                # Log error but don't fail update if mention processing fails
                print(f"Warning: Failed to process mentions in task description: {e}")
        if test_type is not None:
            task.test_type = TestType(test_type) if isinstance(test_type, str) else test_type
        if status is not None:
            old_status = task.status
            task.status = TaskStatus(status) if isinstance(status, str) else status
            # Notify if status changed
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
                        changed_by=None
                    )
                except Exception as e:
                    print(f"Warning: Failed to send status change notification: {e}")
        if owner is not None:
            old_owner = task.owner
            task.owner = owner
            # Notify new owner if owner changed
            if old_owner != owner and owner:
                try:
                    from notifications.notify import NotificationService
                    notification_service = NotificationService()
                    notification_service.notify_task_assigned(
                        user=owner,
                        task_id=task_id,
                        task_description=task.description,
                        assigned_by=None
                    )
                except Exception as e:
                    print(f"Warning: Failed to send assignment notification: {e}")
        if coverage_status is not None:
            task.coverage_status = (
                CoverageStatus(coverage_status)
                if isinstance(coverage_status, str)
                else coverage_status
            )
        if dependencies is not None:
            task.dependencies = list(dependencies)

        return task

    # Delete
    def delete_task(self, task_id: str) -> int:
        stmt = delete(TestTaskModel).where(TestTaskModel.id == task_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0


class CoverageDAL:
    __test__ = False  # prevent pytest from collecting

    def __init__(self, session: Session):
        self.session = session

    def add_coverage(
        self,
        *,
        task_id: str,
        coverage_status: CoverageStatus | str,
    ) -> CoverageModel:
        cov = CoverageModel(
            task_id=task_id,
            coverage_status=CoverageStatus(coverage_status)
            if isinstance(coverage_status, str)
            else coverage_status,
        )
        self.session.add(cov)
        return cov

    def list_by_task(self, task_id: str) -> List[CoverageModel]:
        stmt = select(CoverageModel).where(CoverageModel.task_id == task_id)
        return list(self.session.scalars(stmt).all())

    def update_coverage(
        self, coverage_id: int, *, coverage_status: CoverageStatus | str
    ) -> Optional[CoverageModel]:
        stmt = select(CoverageModel).where(CoverageModel.id == coverage_id)
        cov = self.session.scalars(stmt).first()
        if not cov:
            return None
        cov.coverage_status = (
            CoverageStatus(coverage_status)
            if isinstance(coverage_status, str)
            else coverage_status
        )
        return cov

    def delete_coverage(self, coverage_id: int) -> int:
        stmt = delete(CoverageModel).where(CoverageModel.id == coverage_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0


class CommentDAL:
    """Data Access Layer for task comments."""
    __test__ = False  # prevent pytest from collecting

    def __init__(self, session: Session):
        self.session = session

    def add_comment(
        self,
        *,
        task_id: str,
        user: str,
        comment_text: str,
    ) -> CommentModel:
        """
        Add a comment to a task.
        
        Args:
            task_id: The ID of the task
            user: The username/author of the comment
            comment_text: The text content of the comment
        
        Returns:
            CommentModel instance
        """
        from datetime import datetime
        
        comment = CommentModel(
            task_id=task_id,
            user=user,
            comment_text=comment_text,
            timestamp=datetime.utcnow(),
        )
        self.session.add(comment)
        return comment

    def get_comment(self, comment_id: int) -> Optional[CommentModel]:
        """Get a comment by ID."""
        stmt = select(CommentModel).where(CommentModel.id == comment_id)
        return self.session.scalars(stmt).first()

    def list_by_task(self, task_id: str) -> List[CommentModel]:
        """
        List all comments for a task, ordered by timestamp (oldest first).
        
        Args:
            task_id: The ID of the task
        
        Returns:
            List of CommentModel instances
        """
        stmt = (
            select(CommentModel)
            .where(CommentModel.task_id == task_id)
            .order_by(CommentModel.timestamp.asc())
        )
        return list(self.session.scalars(stmt).all())

    def delete_comment(self, comment_id: int) -> int:
        """Delete a comment by ID."""
        stmt = delete(CommentModel).where(CommentModel.id == comment_id)
        result = self.session.execute(stmt)
        return result.rowcount or 0


__all__ = ["TestTaskDAL", "CoverageDAL", "CommentDAL"]

