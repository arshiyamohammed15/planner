"""
Notification service for task assignments, @mentions, status changes, and comments.

This module provides functionality to send notifications to users when:
- They are mentioned in tasks or comments
- Tasks are assigned to them
- Task status changes
- Comments are added to tasks they are involved in

Supports multiple notification channels: Slack, Email, and Webhooks.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from database.data_access_layer import TestTaskDAL
from database.postgresql_setup import get_sessionmaker
from tasks.test_task_model import TaskStatus


class NotificationService:
    """
    Service for sending notifications to users.
    
    Supports multiple notification channels:
    - Console logging (always enabled)
    - Email (if configured)
    - Webhook (if configured)
    - In-app notifications (future)
    """
    
    def __init__(self):
        """Initialize the notification service."""
        self.email_enabled = os.environ.get("NOTIFICATION_EMAIL_ENABLED", "false").lower() == "true"
        self.webhook_enabled = os.environ.get("NOTIFICATION_WEBHOOK_ENABLED", "false").lower() == "true"
        self.webhook_url = os.environ.get("NOTIFICATION_WEBHOOK_URL")
        
        # Slack configuration
        self.slack_enabled = os.environ.get("NOTIFICATION_SLACK_ENABLED", "false").lower() == "true"
        self.slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
        # Support per-user Slack webhooks (format: SLACK_WEBHOOK_<USERNAME>)
        self.slack_webhook_base = os.environ.get("SLACK_WEBHOOK_BASE_URL", "https://hooks.slack.com/services")
    
    def notify_user_mentioned(
        self,
        user: str,
        task_id: str,
        task_description: str,
        mentioned_by: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that they were @mentioned in a task or comment.
        
        Args:
            user: Username of the mentioned user
            task_id: ID of the task
            task_description: Description of the task
            mentioned_by: Username who mentioned them (optional)
        
        Returns:
            True if notification was sent successfully
        
        Example:
            >>> service = NotificationService()
            >>> service.notify_user_mentioned(
            ...     user="john.doe",
            ...     task_id="task-123",
            ...     task_description="Review API endpoints",
            ...     mentioned_by="jane.smith"
            ... )
            True
        """
        message = self._format_mention_notification(
            user=user,
            task_id=task_id,
            task_description=task_description,
            mentioned_by=mentioned_by
        )
        
        # Always log to console
        self._log_notification(user, message)
        
        # Send via configured channels
        success = True
        if self.email_enabled:
            success = success and self._send_email(user, "You were mentioned in a task", message)
        
        if self.slack_enabled:
            success = success and self._send_slack(user, "You were mentioned in a task", message)
        
        if self.webhook_enabled and self.webhook_url:
            success = success and self._send_webhook(user, "mention", message, {
                "task_id": task_id,
                "task_description": task_description,
                "mentioned_by": mentioned_by
            })
        
        return success
    
    def notify_task_assigned(
        self,
        user: str,
        task_id: str,
        task_description: str,
        assigned_by: Optional[str] = None,
    ) -> bool:
        """
        Notify a user that a task has been assigned to them.
        
        Args:
            user: Username of the assigned user
            task_id: ID of the task
            task_description: Description of the task
            assigned_by: Username who assigned the task (optional)
        
        Returns:
            True if notification was sent successfully
        
        Example:
            >>> service = NotificationService()
            >>> service.notify_task_assigned(
            ...     user="john.doe",
            ...     task_id="task-123",
            ...     task_description="Review API endpoints"
            ... )
            True
        """
        message = self._format_assignment_notification(
            user=user,
            task_id=task_id,
            task_description=task_description,
            assigned_by=assigned_by
        )
        
        # Always log to console
        self._log_notification(user, message)
        
        # Send via configured channels
        success = True
        if self.email_enabled:
            success = success and self._send_email(user, "Task assigned to you", message)
        
        if self.slack_enabled:
            success = success and self._send_slack(user, "Task assigned to you", message)
        
        if self.webhook_enabled and self.webhook_url:
            success = success and self._send_webhook(user, "assignment", message, {
                "task_id": task_id,
                "task_description": task_description,
                "assigned_by": assigned_by
            })
        
        return success
    
    def notify_task_status_changed(
        self,
        task_id: str,
        task_description: str,
        old_status: TaskStatus | str,
        new_status: TaskStatus | str,
        task_owner: Optional[str] = None,
        changed_by: Optional[str] = None,
    ) -> bool:
        """
        Notify relevant users when a task status changes.
        
        Args:
            task_id: ID of the task
            task_description: Description of the task
            old_status: Previous status
            new_status: New status
            task_owner: Owner of the task (will be notified)
            changed_by: Username who changed the status (optional)
        
        Returns:
            True if notification was sent successfully
        
        Example:
            >>> service = NotificationService()
            >>> service.notify_task_status_changed(
            ...     task_id="task-123",
            ...     task_description="Review API endpoints",
            ...     old_status="pending",
            ...     new_status="in_progress",
            ...     task_owner="john.doe"
            ... )
            True
        """
        # Only notify if status actually changed
        old_status_str = str(old_status)
        new_status_str = str(new_status)
        if old_status_str == new_status_str:
            return True
        
        message = self._format_status_change_notification(
            task_id=task_id,
            task_description=task_description,
            old_status=old_status_str,
            new_status=new_status_str,
            changed_by=changed_by
        )
        
        # Notify task owner if they exist
        success = True
        if task_owner:
            self._log_notification(task_owner, message)
            
            if self.email_enabled:
                success = success and self._send_email(
                    task_owner,
                    f"Task {task_id} status changed",
                    message
                )
            
            if self.slack_enabled:
                success = success and self._send_slack(
                    task_owner,
                    f"Task {task_id} status changed",
                    message
                )
            
            if self.webhook_enabled and self.webhook_url:
                success = success and self._send_webhook(
                    task_owner,
                    "status_change",
                    message,
                    {
                        "task_id": task_id,
                        "task_description": task_description,
                        "old_status": old_status_str,
                        "new_status": new_status_str,
                        "changed_by": changed_by
                    }
                )
        
        return success
    
    def notify_comment_added(
        self,
        task_id: str,
        task_description: str,
        comment_author: str,
        comment_text: str,
        task_owner: Optional[str] = None,
        involved_users: Optional[List[str]] = None,
    ) -> bool:
        """
        Notify involved users when a comment is added to a task.
        
        Involved users include:
        - Task owner
        - Users who have previously commented on the task
        - Users mentioned in the comment (handled separately)
        
        Args:
            task_id: ID of the task
            task_description: Description of the task
            comment_author: Username who added the comment
            comment_text: Text of the comment
            task_owner: Owner of the task
            involved_users: List of additional users to notify (e.g., previous commenters)
        
        Returns:
            True if notifications were sent successfully
        
        Example:
            >>> service = NotificationService()
            >>> service.notify_comment_added(
            ...     task_id="task-123",
            ...     task_description="Review API endpoints",
            ...     comment_author="jane.smith",
            ...     comment_text="Looks good to me",
            ...     task_owner="john.doe"
            ... )
            True
        """
        # Collect all users to notify (excluding comment author)
        users_to_notify: List[str] = []
        
        if task_owner and task_owner != comment_author:
            users_to_notify.append(task_owner)
        
        if involved_users:
            for user in involved_users:
                if user != comment_author and user not in users_to_notify:
                    users_to_notify.append(user)
        
        if not users_to_notify:
            return True  # No one to notify
        
        message = self._format_comment_notification(
            task_id=task_id,
            task_description=task_description,
            comment_author=comment_author,
            comment_text=comment_text
        )
        
        # Send notifications to all involved users
        success = True
        for user in users_to_notify:
            self._log_notification(user, message)
            
            if self.email_enabled:
                success = success and self._send_email(
                    user,
                    f"New comment on task {task_id}",
                    message
                )
            
            if self.slack_enabled:
                success = success and self._send_slack(
                    user,
                    f"New comment on task {task_id}",
                    message
                )
            
            if self.webhook_enabled and self.webhook_url:
                success = success and self._send_webhook(
                    user,
                    "comment_added",
                    message,
                    {
                        "task_id": task_id,
                        "task_description": task_description,
                        "comment_author": comment_author,
                        "comment_text": comment_text
                    }
                )
        
        return success
    
    def _format_mention_notification(
        self,
        user: str,
        task_id: str,
        task_description: str,
        mentioned_by: Optional[str] = None,
    ) -> str:
        """Format a mention notification message."""
        mentioned_by_text = f" by {mentioned_by}" if mentioned_by else ""
        return (
            f"You were mentioned{mentioned_by_text} in task {task_id}.\n"
            f"Task: {task_description}\n"
            f"View task: {self._get_task_url(task_id)}"
        )
    
    def _format_assignment_notification(
        self,
        user: str,
        task_id: str,
        task_description: str,
        assigned_by: Optional[str] = None,
    ) -> str:
        """Format a task assignment notification message."""
        assigned_by_text = f" by {assigned_by}" if assigned_by else ""
        return (
            f"Task {task_id} has been assigned to you{assigned_by_text}.\n"
            f"Task: {task_description}\n"
            f"View task: {self._get_task_url(task_id)}"
        )
    
    def _format_status_change_notification(
        self,
        task_id: str,
        task_description: str,
        old_status: str,
        new_status: str,
        changed_by: Optional[str] = None,
    ) -> str:
        """Format a task status change notification message."""
        changed_by_text = f" by {changed_by}" if changed_by else ""
        return (
            f"Task {task_id} status changed{changed_by_text}.\n"
            f"Status: {old_status} → {new_status}\n"
            f"Task: {task_description}\n"
            f"View task: {self._get_task_url(task_id)}"
        )
    
    def _format_comment_notification(
        self,
        task_id: str,
        task_description: str,
        comment_author: str,
        comment_text: str,
    ) -> str:
        """Format a comment notification message."""
        # Truncate long comments
        comment_preview = comment_text[:200] + "..." if len(comment_text) > 200 else comment_text
        return (
            f"New comment on task {task_id} by {comment_author}.\n"
            f"Task: {task_description}\n"
            f"Comment: {comment_preview}\n"
            f"View task: {self._get_task_url(task_id)}"
        )
    
    def _get_task_url(self, task_id: str) -> str:
        """Get URL for viewing a task (can be customized via environment variable)."""
        base_url = os.environ.get("TASK_BASE_URL", "http://localhost:8000")
        return f"{base_url}/tasks/{task_id}"
    
    def _log_notification(self, user: str, message: str) -> None:
        """Log notification to console."""
        print(f"[NOTIFICATION] To: {user}")
        print(f"[NOTIFICATION] Message: {message}")
    
    def _send_email(self, user: str, subject: str, message: str) -> bool:
        """
        Send email notification.
        
        This is a placeholder implementation. In production, integrate with
        an email service (SMTP, SendGrid, SES, etc.).
        
        Args:
            user: Recipient username/email
            subject: Email subject
            message: Email body
        
        Returns:
            True if email was sent successfully
        """
        # Placeholder: In production, implement actual email sending
        # Example: Use smtplib, SendGrid API, AWS SES, etc.
        email_address = os.environ.get(f"EMAIL_{user.upper().replace('.', '_')}") or f"{user}@example.com"
        print(f"[EMAIL] Would send to {email_address}: {subject}")
        print(f"[EMAIL] {message}")
        return True
    
    def _send_webhook(self, user: str, event_type: str, message: str, metadata: dict) -> bool:
        """
        Send webhook notification.
        
        Args:
            user: Username
            event_type: Type of event (mention, assignment, etc.)
            message: Notification message
            metadata: Additional metadata
        
        Returns:
            True if webhook was sent successfully
        """
        import json
        import urllib.request
        import urllib.parse
        
        if not self.webhook_url:
            return False
        
        payload = {
            "user": user,
            "event_type": event_type,
            "message": message,
            **metadata
        }
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                self.webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            print(f"[WEBHOOK] Failed to send notification: {e}")
            return False
    
    def _send_slack(self, user: str, title: str, message: str) -> bool:
        """
        Send Slack notification via webhook.
        
        Supports both global webhook URL and per-user webhooks.
        Per-user webhook format: SLACK_WEBHOOK_<USERNAME> environment variable.
        
        Args:
            user: Username
            title: Notification title
            message: Notification message
        
        Returns:
            True if Slack notification was sent successfully
        
        Example:
            >>> service = NotificationService()
            >>> service._send_slack("john.doe", "Task assigned", "Task 123 assigned to you")
            True
        """
        # Try per-user webhook first, then fall back to global
        webhook_url = os.environ.get(f"SLACK_WEBHOOK_{user.upper().replace('.', '_').replace('-', '_')}")
        if not webhook_url:
            webhook_url = self.slack_webhook_url
        
        if not webhook_url:
            return False
        
        # Use requests if available, otherwise fall back to urllib
        if REQUESTS_AVAILABLE:
            return self._send_slack_requests(webhook_url, user, title, message)
        else:
            return self._send_slack_urllib(webhook_url, user, title, message)
    
    def _send_slack_requests(self, webhook_url: str, user: str, title: str, message: str) -> bool:
        """Send Slack notification using requests library."""
        try:
            payload = {
                "text": title,
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{title}*\n{message}"
                        }
                    }
                ]
            }
            
            response = requests.post(webhook_url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[SLACK] Failed to send notification to {user}: {e}")
            return False
    
    def _send_slack_urllib(self, webhook_url: str, user: str, title: str, message: str) -> bool:
        """Send Slack notification using urllib (fallback when requests not available)."""
        import urllib.request
        
        try:
            payload = {
                "text": f"{title}\n{message}"
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                webhook_url,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            print(f"[SLACK] Failed to send notification to {user}: {e}")
            return False


__all__ = ["NotificationService"]

