"""
@Mention functionality for task assignment and notifications.

This module parses @mentions from task descriptions and comments,
automatically assigns tasks to mentioned users, and sends notifications.
"""

from __future__ import annotations

import re
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from database.data_access_layer import TestTaskDAL
from database.postgresql_setup import get_sessionmaker
from notifications.notify import NotificationService


def parse_mentions(text: str) -> List[str]:
    """
    Parse @mentions from text and return a list of unique usernames.
    
    Supports formats:
    - @username
    - @user.name
    - @user_name
    - @user-name
    
    Args:
        text: Text to parse for @mentions
    
    Returns:
        List of unique usernames (without @ symbol)
    
    Example:
        >>> parse_mentions("Hey @john.doe, can you review this? Also @jane_smith")
        ['john.doe', 'jane_smith']
        >>> parse_mentions("No mentions here")
        []
    """
    if not text:
        return []
    
    # Pattern matches @ followed by alphanumeric, dots, underscores, or hyphens
    # Username must start with alphanumeric and can contain dots, underscores, hyphens
    # Minimum length of 1 character after @
    mention_pattern = r'@([a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?)'
    
    matches = re.findall(mention_pattern, text)
    
    # Return unique mentions, preserving order
    seen: Set[str] = set()
    unique_mentions: List[str] = []
    for mention in matches:
        mention_lower = mention.lower()
        if mention_lower not in seen:
            seen.add(mention_lower)
            unique_mentions.append(mention)
    
    return unique_mentions


def process_mentions_in_text(
    text: str,
    task_id: str,
    session: Optional[Session] = None,
    notify: bool = True
) -> List[str]:
    """
    Process @mentions in text, assign task to first mentioned user, and send notifications.
    
    Args:
        text: Text containing @mentions (e.g., task description or comment)
        task_id: ID of the task to assign
        session: Optional database session
        notify: Whether to send notifications (default: True)
    
    Returns:
        List of usernames that were mentioned and processed
    
    Raises:
        RuntimeError: If task does not exist
        ValueError: If no mentions found or task_id is invalid
    
    Example:
        >>> mentions = process_mentions_in_text(
        ...     "Please review @john.doe and @jane.smith",
        ...     "task-123"
        ... )
        >>> print(mentions)
        ['john.doe', 'jane.smith']
    """
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")
    
    mentions = parse_mentions(text)
    if not mentions:
        return []
    
    should_close = False
    if session is None:
        sessionmaker = get_sessionmaker()
        session = sessionmaker()
        should_close = True
    
    # Type assertion: session is guaranteed to be non-None here
    assert session is not None, "Session should not be None at this point"
    
    try:
        # Verify task exists
        dal = TestTaskDAL(session)
        task = dal.get_task(task_id)
        if not task:
            raise RuntimeError(f"Task with id '{task_id}' does not exist")
        
        # Assign task to first mentioned user
        first_mention = mentions[0]
        if not task.owner or task.owner != first_mention:
            task.owner = first_mention
            if session:
                session.commit()
        
        # Send notifications to all mentioned users
        if notify:
            notification_service = NotificationService()
            for mentioned_user in mentions:
                notification_service.notify_user_mentioned(
                    user=mentioned_user,
                    task_id=task_id,
                    task_description=task.description,
                    mentioned_by=first_mention if len(mentions) > 1 else None
                )
        
        return mentions
    finally:
        if should_close and session:
            session.close()


def process_mentions_in_comment(
    task_id: str,
    comment_text: str,
    comment_author: str,
    session: Optional[Session] = None,
    notify: bool = True
) -> List[str]:
    """
    Process @mentions in a comment, assign task if needed, and send notifications.
    
    This is a convenience function that processes mentions when a comment is added.
    
    Args:
        task_id: ID of the task the comment belongs to
        comment_text: Text of the comment (may contain @mentions)
        comment_author: Author of the comment
        session: Optional database session
        notify: Whether to send notifications (default: True)
    
    Returns:
        List of usernames that were mentioned and processed
    
    Example:
        >>> mentions = process_mentions_in_comment(
        ...     "task-123",
        ...     "Hey @john.doe, can you take a look?",
        ...     "jane.smith"
        ... )
    """
    return process_mentions_in_text(comment_text, task_id, session=session, notify=notify)


def process_mentions_in_task_description(
    task_id: str,
    description: str,
    session: Optional[Session] = None,
    notify: bool = True
) -> List[str]:
    """
    Process @mentions in a task description, assign task, and send notifications.
    
    This is a convenience function for processing mentions when a task is created or updated.
    
    Args:
        task_id: ID of the task
        description: Task description (may contain @mentions)
        session: Optional database session
        notify: Whether to send notifications (default: True)
    
    Returns:
        List of usernames that were mentioned and processed
    
    Example:
        >>> mentions = process_mentions_in_task_description(
        ...     "task-123",
        ...     "Review API endpoints. @john.doe please handle this."
        ... )
    """
    return process_mentions_in_text(description, task_id, session=session, notify=notify)


__all__ = [
    "parse_mentions",
    "process_mentions_in_text",
    "process_mentions_in_comment",
    "process_mentions_in_task_description",
]

