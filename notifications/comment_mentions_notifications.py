"""
Integrated notification system for comments and @mentions.

This module provides unified functionality to notify users when:
- They are @mentioned in comments
- Comments are added to tasks they are working on
- They are the task owner and a comment is added
"""

from __future__ import annotations

from typing import List, Optional, Set

from sqlalchemy.orm import Session

from database.data_access_layer import CommentDAL, TestTaskDAL
from database.postgresql_setup import get_sessionmaker
from notifications.notify import NotificationService
from tasks.task_mentions import parse_mentions


def extract_mentions(text: str) -> List[str]:
    """
    Extract @mentions from text.
    
    This is a convenience wrapper around parse_mentions from task_mentions.
    
    Args:
        text: Text to extract mentions from
    
    Returns:
        List of unique usernames (without @ symbol)
    
    Example:
        >>> extract_mentions("Hey @john.doe and @jane.smith, please review")
        ['john.doe', 'jane.smith']
    """
    return parse_mentions(text)


def notify_mentions_or_comments(
    task_id: str,
    comment: str,
    comment_author: str,
    session: Optional[Session] = None,
) -> dict:
    """
    Notify users when they are @mentioned or when a comment is added to their task.
    
    This function:
    1. Extracts @mentions from the comment
    2. Sends notifications to mentioned users
    3. Sends notifications to task owner (if not the comment author)
    4. Sends notifications to previous commenters (if not already notified)
    
    Args:
        task_id: ID of the task
        comment: Comment text (may contain @mentions)
        comment_author: Username who wrote the comment
        session: Optional database session
    
    Returns:
        Dictionary with notification results:
        {
            'mentions_found': List[str],
            'mentions_notified': List[str],
            'task_owner_notified': bool,
            'commenters_notified': List[str],
            'success': bool
        }
    
    Example:
        >>> result = notify_mentions_or_comments(
        ...     "task-123",
        ...     "Hey @john.doe, can you review this?",
        ...     "jane.smith"
        ... )
        >>> print(result['mentions_notified'])
        ['john.doe']
    """
    should_close = False
    if session is None:
        sessionmaker = get_sessionmaker()
        session = sessionmaker()
        should_close = True
    
    assert session is not None, "Session should not be None at this point"
    
    notification_service = NotificationService()
    result = {
        'mentions_found': [],
        'mentions_notified': [],
        'task_owner_notified': False,
        'commenters_notified': [],
        'success': True
    }
    
    try:
        # Get task information
        dal = TestTaskDAL(session)
        task = dal.get_task(task_id)
        if not task:
            result['success'] = False
            return result
        
        # Extract mentions from comment
        mentions = extract_mentions(comment)
        result['mentions_found'] = mentions
        
        # Collect all users to notify (avoid duplicates)
        users_to_notify: Set[str] = set()
        
        # Add mentioned users
        for mention in mentions:
            if mention != comment_author:
                users_to_notify.add(mention)
        
        # Add task owner (if not comment author and not already mentioned)
        if task.owner and task.owner != comment_author:
            users_to_notify.add(task.owner)
            result['task_owner_notified'] = True
        
        # Get previous commenters (excluding comment author)
        try:
            comment_dal = CommentDAL(session)
            previous_comments = comment_dal.list_by_task(task_id)
            for prev_comment in previous_comments:
                if (prev_comment.user != comment_author and 
                    prev_comment.user not in users_to_notify):
                    users_to_notify.add(prev_comment.user)
                    result['commenters_notified'].append(prev_comment.user)
        except Exception as e:
            print(f"Warning: Failed to get previous commenters: {e}")
        
        # Send notifications to all users
        for user in users_to_notify:
            try:
                # Determine notification type
                is_mentioned = user in mentions
                is_owner = user == task.owner
                
                if is_mentioned:
                    # Send mention notification
                    success = notification_service.notify_user_mentioned(
                        user=user,
                        task_id=task_id,
                        task_description=task.description,
                        mentioned_by=comment_author
                    )
                    if success:
                        result['mentions_notified'].append(user)
                else:
                    # Send comment notification (for task owner or previous commenters)
                    success = notification_service.notify_comment_added(
                        task_id=task_id,
                        task_description=task.description,
                        comment_author=comment_author,
                        comment_text=comment,
                        task_owner=task.owner if is_owner else None,
                        involved_users=[user] if not is_owner else None
                    )
                    if not success:
                        result['success'] = False
            except Exception as e:
                print(f"Warning: Failed to notify user {user}: {e}")
                result['success'] = False
        
        return result
    
    finally:
        if should_close and session:
            session.close()


def notify_comment_added(
    task_id: str,
    comment_text: str,
    comment_author: str,
    session: Optional[Session] = None,
) -> dict:
    """
    Notify users when a comment is added to a task.
    
    This is a convenience function that handles both mentions and comment notifications.
    
    Args:
        task_id: ID of the task
        comment_text: Text of the comment
        comment_author: Username who added the comment
        session: Optional database session
    
    Returns:
        Dictionary with notification results
    
    Example:
        >>> result = notify_comment_added(
        ...     "task-123",
        ...     "This looks good! @john.doe can you verify?",
        ...     "jane.smith"
        ... )
    """
    return notify_mentions_or_comments(
        task_id=task_id,
        comment=comment_text,
        comment_author=comment_author,
        session=session
    )


def send_notification(user: str, message: str, task_id: Optional[str] = None) -> bool:
    """
    Send a notification to a user.
    
    This is a convenience function for sending simple notifications.
    
    Args:
        user: Username to notify
        message: Notification message
        task_id: Optional task ID for context
    
    Returns:
        True if notification was sent successfully
    
    Example:
        >>> send_notification(
        ...     "john.doe",
        ...     "New comment on Task task-123: This needs review",
        ...     "task-123"
        ... )
        True
    """
    notification_service = NotificationService()
    
    # Format message with task context if provided
    if task_id:
        full_message = f"{message}\nView task: {notification_service._get_task_url(task_id)}"
    else:
        full_message = message
    
    # Log notification (always enabled)
    notification_service._log_notification(user, full_message)
    
    # Send via configured channels
    success = True
    if notification_service.email_enabled:
        success = success and notification_service._send_email(
            user,
            "Task Notification" if task_id else "Notification",
            full_message
        )
    
    if notification_service.slack_enabled:
        success = success and notification_service._send_slack(
            user,
            "Task Notification" if task_id else "Notification",
            full_message
        )
    
    if notification_service.webhook_enabled and notification_service.webhook_url:
        success = success and notification_service._send_webhook(
            user,
            "notification",
            full_message,
            {"task_id": task_id} if task_id else {}
        )
    
    return success


__all__ = [
    "extract_mentions",
    "notify_mentions_or_comments",
    "notify_comment_added",
    "send_notification",
]

