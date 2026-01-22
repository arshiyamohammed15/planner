"""
Example usage of the coverage alerting system.
"""

from __future__ import annotations

from monitoring.alerting import (
    AlertConfig,
    CoverageAlertManager,
    NotificationConfig,
    create_prometheus_alert_rules,
)


def example_basic_alert():
    """Example: Basic alert configuration."""
    print("Example: Basic Alert Configuration")
    
    # Configure alerts
    alert_config = AlertConfig(
        threshold=80.0,  # Alert if coverage drops below 80%
        duration_minutes=5,  # Must be below threshold for 5 minutes
        test_suite="pytest",
    )
    
    # Configure notifications (using environment variables)
    notification_config = NotificationConfig()
    
    # Create alert manager
    manager = CoverageAlertManager(
        alert_config=alert_config,
        notification_config=notification_config,
    )
    
    # Check and send alerts
    result = manager.check_and_alert()
    
    if result:
        print(f"Alert triggered! Coverage: {result['coverage']}%")
        print(f"Notifications sent: {result['notifications']}")
    else:
        print("No alerts triggered - coverage is above threshold")


def example_slack_alerts():
    """Example: Slack notification configuration."""
    print("\nExample: Slack Alert Configuration")
    
    alert_config = AlertConfig(threshold=80.0)
    
    notification_config = NotificationConfig(
        slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        slack_channel="#alerts",
    )
    
    manager = CoverageAlertManager(
        alert_config=alert_config,
        notification_config=notification_config,
    )
    
    result = manager.check_and_alert()
    if result:
        print("Slack notification sent!")


def example_email_alerts():
    """Example: Email notification configuration."""
    print("\nExample: Email Alert Configuration")
    
    alert_config = AlertConfig(threshold=80.0)
    
    notification_config = NotificationConfig(
        email_smtp_server="smtp.gmail.com",
        email_smtp_port=587,
        email_from="alerts@example.com",
        email_to=["team@example.com", "manager@example.com"],
        email_username="alerts@example.com",
        email_password="your-password",
    )
    
    manager = CoverageAlertManager(
        alert_config=alert_config,
        notification_config=notification_config,
    )
    
    result = manager.check_and_alert()
    if result:
        print("Email notification sent!")


def example_multiple_channels():
    """Example: Multiple notification channels."""
    print("\nExample: Multiple Notification Channels")
    
    alert_config = AlertConfig(threshold=80.0)
    
    notification_config = NotificationConfig(
        slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        email_smtp_server="smtp.gmail.com",
        email_to=["team@example.com"],
        webhook_url="https://your-webhook-url.com/alerts",
    )
    
    manager = CoverageAlertManager(
        alert_config=alert_config,
        notification_config=notification_config,
    )
    
    result = manager.check_and_alert()
    if result:
        print(f"Notifications sent to: {list(result['notifications'].keys())}")


def example_create_alert_rules():
    """Example: Create Prometheus alert rules."""
    print("\nExample: Creating Prometheus Alert Rules")
    
    create_prometheus_alert_rules("prometheus_alerts.yml")
    print("Prometheus alert rules file created!")


if __name__ == "__main__":
    print("Coverage Alerting Examples")
    print("=" * 50)
    
    example_basic_alert()
    example_create_alert_rules()
    
    print("\nNote: Configure notification channels via environment variables:")
    print("  SLACK_WEBHOOK_URL")
    print("  SMTP_SERVER, ALERT_EMAIL_FROM, ALERT_EMAIL_TO")
    print("  ALERT_WEBHOOK_URL")

