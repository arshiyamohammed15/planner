"""
Commenting functionality for test tasks.

This module provides functions to add comments to test tasks and retrieve
existing comments, enabling team collaboration and communication.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from database.data_access_layer import CommentDAL
from database.models import CommentModel
from database.postgresql_setup import get_sessionmaker


def add_comment(task_id: str, user: str, comment_text: str, session: Optional[Session] = None) -> CommentModel:
    """
    Add a comment to a test task.
    
    Args:
        task_id: The ID of the task to comment on
        user: The username/author of the comment
        comment_text: The text content of the comment
        session: Optional database session (creates new if not provided)
    
    Returns:
        CommentModel instance representing the created comment
    
    Raises:
        ValueError: If task_id, user, or comment_text is empty
        RuntimeError: If the task does not exist
    
    Example:
        >>> comment = add_comment("task-123", "john.doe", "This test needs more edge cases")
        >>> print(comment.id)
        1
    """
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")
    if not user or not user.strip():
        raise ValueError("user cannot be empty")
    if not comment_text or not comment_text.strip():
        raise ValueError("comment_text cannot be empty")
    
    should_close = False
    if session is None:
        sessionmaker = get_sessionmaker()
        session = sessionmaker()
        should_close = True
    
    # Type assertion: session is guaranteed to be non-None here
    assert session is not None, "Session should not be None at this point"
    
    try:
        # Verify task exists
        from database.data_access_layer import TestTaskDAL
        task_dal = TestTaskDAL(session)
        task = task_dal.get_task(task_id)
        if not task:
            raise RuntimeError(f"Task with id '{task_id}' does not exist")
        
        # Create and store comment
        comment_dal = CommentDAL(session)
        comment = comment_dal.add_comment(
            task_id=task_id,
            user=user.strip(),
            comment_text=comment_text.strip()
        )
        
        session.commit()
        
        # Get involved users (task owner and previous commenters)
        involved_users: List[str] = []
        if task.owner and task.owner != user:
            involved_users.append(task.owner)
        
        # Get previous commenters (excluding current comment author)
        try:
            previous_comments = comment_dal.list_by_task(task_id)
            for prev_comment in previous_comments:
                if prev_comment.user != user and prev_comment.user not in involved_users:
                    involved_users.append(prev_comment.user)
        except Exception as e:
            print(f"Warning: Failed to get previous commenters: {e}")
        
        # Use integrated notification system for comments and mentions
        try:
            from notifications.comment_mentions_notifications import notify_mentions_or_comments
            notify_mentions_or_comments(
                task_id=task_id,
                comment=comment_text,
                comment_author=user,
                session=session
            )
        except Exception as e:
            # Log error but don't fail comment creation if notification fails
            print(f"Warning: Failed to send comment/mention notifications: {e}")
        
        # Also process mentions for task assignment (if first mention)
        try:
            from tasks.task_mentions import process_mentions_in_comment
            process_mentions_in_comment(
                task_id=task_id,
                comment_text=comment_text,
                comment_author=user,
                session=session,
                notify=False  # Already notified via notify_mentions_or_comments
            )
        except Exception as e:
            # Log error but don't fail comment creation if mention processing fails
            print(f"Warning: Failed to process mentions for task assignment: {e}")
        
        return comment
    finally:
        if should_close:
            session.close()


def get_comments(task_id: str, session: Optional[Session] = None) -> List[CommentModel]:
    """
    Get all comments for a test task, ordered by timestamp (oldest first).
    
    Args:
        task_id: The ID of the task to get comments for
        session: Optional database session (creates new if not provided)
    
    Returns:
        List of CommentModel instances, ordered by timestamp ascending
    
    Example:
        >>> comments = get_comments("task-123")
        >>> for comment in comments:
        ...     print(f"{comment.user}: {comment.comment_text}")
    """
    should_close = False
    if session is None:
        sessionmaker = get_sessionmaker()
        session = sessionmaker()
        should_close = True
    
    # Type assertion: session is guaranteed to be non-None here
    assert session is not None, "Session should not be None at this point"
    
    try:
        comment_dal = CommentDAL(session)
        return comment_dal.list_by_task(task_id)
    finally:
        if should_close and session:
            session.close()


def store_comment_in_db(comment: dict, session: Optional[Session] = None) -> CommentModel:
    """
    Store a comment in the database.
    
    This is a lower-level function that accepts a dictionary with comment data.
    Prefer using add_comment() for most use cases.
    
    Args:
        comment: Dictionary with keys: task_id, user, comment_text, timestamp (optional)
        session: Optional database session (creates new if not provided)
    
    Returns:
        CommentModel instance representing the stored comment
    
    Example:
        >>> comment_data = {
        ...     'task_id': 'task-123',
        ...     'user': 'john.doe',
        ...     'comment': 'This needs review',
        ...     'timestamp': datetime.now()
        ... }
        >>> comment = store_comment_in_db(comment_data)
    """
    task_id = comment.get('task_id')
    user = comment.get('user')
    comment_text = comment.get('comment') or comment.get('comment_text')
    timestamp = comment.get('timestamp', datetime.utcnow())
    
    if not task_id:
        raise ValueError("comment dictionary must contain 'task_id'")
    if not user:
        raise ValueError("comment dictionary must contain 'user'")
    if not comment_text:
        raise ValueError("comment dictionary must contain 'comment' or 'comment_text'")
    
    return add_comment(task_id, user, comment_text, session=session)


__all__ = ["add_comment", "get_comments", "store_comment_in_db"]

