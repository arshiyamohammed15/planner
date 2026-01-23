"""
Alerting system for test coverage thresholds.

This module provides alerting functionality to notify teams when test coverage
drops below configured thresholds. Supports multiple notification channels:
Slack, Email, SMS, and webhooks.
"""

from __future__ import annotations

import json
import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from monitoring.coverage_tracking import get_coverage_trends
from monitoring.coverage_metrics import CoverageMetricsModel


@dataclass
class AlertConfig:
    """Configuration for coverage alerts."""
    threshold: float = 80.0  # Coverage percentage threshold
    duration_minutes: int = 5  # Duration coverage must be below threshold
    test_suite: Optional[str] = None  # Filter by test suite
    branch_name: Optional[str] = None  # Filter by branch
    enabled: bool = True  # Enable/disable alerts


@dataclass
class NotificationConfig:
    """Configuration for notification channels."""
    slack_webhook_url: Optional[str] = None
    slack_channel: Optional[str] = None
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_from: Optional[str] = None
    email_to: list[str] = None
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    sms_api_key: Optional[str] = None
    sms_api_secret: Optional[str] = None
    sms_from: Optional[str] = None
    sms_to: list[str] = None
    webhook_url: Optional[str] = None


class CoverageAlertManager:
    """
    Manages coverage alerts and notifications.
    
    Checks coverage metrics against thresholds and sends notifications
    when coverage drops below configured levels.
    """

    def __init__(
        self,
        alert_config: Optional[AlertConfig] = None,
        notification_config: Optional[NotificationConfig] = None,
    ):
        """
        Initialize the alert manager.
        
        Args:
            alert_config: Alert configuration (uses defaults if not provided)
            notification_config: Notification configuration (uses defaults if not provided)
        """
        self.alert_config = alert_config or AlertConfig()
        self.notification_config = notification_config or NotificationConfig()
        
        # Load from environment variables if not provided
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        # Alert config
        if not self.alert_config.threshold:
            self.alert_config.threshold = float(
                os.environ.get("COVERAGE_THRESHOLD", "80.0")
            )
        
        # Slack config
        if not self.notification_config.slack_webhook_url:
            self.notification_config.slack_webhook_url = os.environ.get(
                "SLACK_WEBHOOK_URL"
            )
        if not self.notification_config.slack_channel:
            self.notification_config.slack_channel = os.environ.get(
                "SLACK_CHANNEL", "#alerts"
            )
        
        # Email config
        if not self.notification_config.email_smtp_server:
            self.notification_config.email_smtp_server = os.environ.get(
                "SMTP_SERVER"
            )
        if not self.notification_config.email_from:
            self.notification_config.email_from = os.environ.get("ALERT_EMAIL_FROM")
        if not self.notification_config.email_to:
            email_to = os.environ.get("ALERT_EMAIL_TO", "")
            self.notification_config.email_to = [
                e.strip() for e in email_to.split(",") if e.strip()
            ]
        
        # SMS config (using Twilio as example)
        if not self.notification_config.sms_api_key:
            self.notification_config.sms_api_key = os.environ.get("TWILIO_API_KEY")
        if not self.notification_config.sms_api_secret:
            self.notification_config.sms_api_secret = os.environ.get(
                "TWILIO_API_SECRET"
            )
        
        # Webhook config
        if not self.notification_config.webhook_url:
            self.notification_config.webhook_url = os.environ.get("ALERT_WEBHOOK_URL")

    def check_coverage_threshold(self) -> Optional[CoverageMetricsModel]:
        """
        Check if current coverage is below threshold.
        
        Returns:
            CoverageMetricsModel if below threshold, None otherwise
        """
        # Get latest coverage metrics
        trends = get_coverage_trends(
            days=1,
            test_suite=self.alert_config.test_suite,
            branch_name=self.alert_config.branch_name,
        )
        
        if not trends:
            return None
        
        latest = trends[-1]  # Most recent metric
        
        if latest.coverage_percentage < self.alert_config.threshold:
            # Check if it's been below threshold for the required duration
            cutoff_time = datetime.utcnow() - timedelta(
                minutes=self.alert_config.duration_minutes
            )
            
            # Check if all metrics in the duration window are below threshold
            recent_below_threshold = [
                m
                for m in trends
                if m.timestamp >= cutoff_time
                and m.coverage_percentage < self.alert_config.threshold
            ]
            
            if len(recent_below_threshold) >= 2:  # At least 2 data points
                return latest
        
        return None

    def send_slack_notification(
        self,
        coverage: float,
        threshold: float,
        metric: CoverageMetricsModel,
    ) -> bool:
        """
        Send alert notification to Slack.
        
        Args:
            coverage: Current coverage percentage
            threshold: Coverage threshold
            metric: Coverage metric that triggered the alert
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.notification_config.slack_webhook_url:
            return False
        
        message = {
            "text": f"⚠️ Test Coverage Alert",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "⚠️ Test Coverage Below Threshold"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Current Coverage:* {coverage:.2f}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Threshold:* {threshold:.2f}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Test Suite:* {metric.test_suite or 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Branch:* {metric.branch_name or 'N/A'}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Lines:* {metric.total_lines}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Missing Lines:* {metric.missing_lines}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Commit:* `{metric.commit_hash or 'N/A'}`\n*Timestamp:* {metric.timestamp.isoformat()}"
                    }
                }
            ]
        }
        
        if self.notification_config.slack_channel:
            message["channel"] = self.notification_config.slack_channel
        
        try:
            req = Request(
                self.notification_config.slack_webhook_url,
                data=json.dumps(message).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    def send_email_notification(
        self,
        coverage: float,
        threshold: float,
        metric: CoverageMetricsModel,
    ) -> bool:
        """
        Send alert notification via email.
        
        Args:
            coverage: Current coverage percentage
            threshold: Coverage threshold
            metric: Coverage metric that triggered the alert
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.notification_config.email_smtp_server:
            return False
        
        if not self.notification_config.email_to:
            return False
        
        subject = f"Test Coverage Alert: {coverage:.2f}% (Below {threshold}%)"
        
        body = f"""
Test Coverage Alert

Current coverage has dropped below the threshold:

Current Coverage: {coverage:.2f}%
Threshold: {threshold:.2f}%
Difference: {threshold - coverage:.2f}%

Details:
- Test Suite: {metric.test_suite or 'N/A'}
- Branch: {metric.branch_name or 'N/A'}
- Commit: {metric.commit_hash or 'N/A'}
- Total Lines: {metric.total_lines}
- Covered Lines: {metric.covered_lines}
- Missing Lines: {metric.missing_lines}
- Timestamp: {metric.timestamp.isoformat()}

Please review and improve test coverage.
"""
        
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.notification_config.email_from
            msg["To"] = ", ".join(self.notification_config.email_to)
            
            with smtplib.SMTP(
                self.notification_config.email_smtp_server,
                self.notification_config.email_smtp_port,
            ) as server:
                if self.notification_config.email_username:
                    server.starttls()
                    server.login(
                        self.notification_config.email_username,
                        self.notification_config.email_password or "",
                    )
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Failed to send email notification: {e}")
            return False

    def send_sms_notification(
        self,
        coverage: float,
        threshold: float,
        metric: CoverageMetricsModel,
    ) -> bool:
        """
        Send alert notification via SMS (using Twilio as example).
        
        Args:
            coverage: Current coverage percentage
            threshold: Coverage threshold
            metric: Coverage metric that triggered the alert
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.notification_config.sms_api_key:
            return False
        
        if not self.notification_config.sms_to:
            return False
        
        message = (
            f"Coverage Alert: {coverage:.1f}% (below {threshold}%). "
            f"Branch: {metric.branch_name or 'N/A'}. "
            f"Commit: {metric.commit_hash[:8] if metric.commit_hash else 'N/A'}"
        )
        
        # Example using Twilio API
        try:
            for phone_number in self.notification_config.sms_to:
                data = urlencode({
                    "From": self.notification_config.sms_from or "",
                    "To": phone_number,
                    "Body": message,
                }).encode()
                
                req = Request(
                    f"https://api.twilio.com/2010-04-01/Accounts/{self.notification_config.sms_api_key}/Messages.json",
                    data=data,
                    headers={
                        "Authorization": f"Basic {self.notification_config.sms_api_secret}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                urlopen(req, timeout=10)
            
            return True
        except Exception as e:
            print(f"Failed to send SMS notification: {e}")
            return False

    def send_webhook_notification(
        self,
        coverage: float,
        threshold: float,
        metric: CoverageMetricsModel,
    ) -> bool:
        """
        Send alert notification to a webhook URL.
        
        Args:
            coverage: Current coverage percentage
            threshold: Coverage threshold
            metric: Coverage metric that triggered the alert
        
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.notification_config.webhook_url:
            return False
        
        payload = {
            "alert_type": "coverage_threshold",
            "severity": "warning",
            "coverage": coverage,
            "threshold": threshold,
            "test_suite": metric.test_suite,
            "branch_name": metric.branch_name,
            "commit_hash": metric.commit_hash,
            "total_lines": metric.total_lines,
            "covered_lines": metric.covered_lines,
            "missing_lines": metric.missing_lines,
            "timestamp": metric.timestamp.isoformat(),
        }
        
        try:
            req = Request(
                self.notification_config.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urlopen(req, timeout=10)
            return True
        except Exception as e:
            print(f"Failed to send webhook notification: {e}")
            return False

    def send_all_notifications(
        self,
        coverage: float,
        threshold: float,
        metric: CoverageMetricsModel,
    ) -> dict[str, bool]:
        """
        Send notifications to all configured channels.
        
        Args:
            coverage: Current coverage percentage
            threshold: Coverage threshold
            metric: Coverage metric that triggered the alert
        
        Returns:
            Dictionary with notification channel names and success status
        """
        results = {}
        
        if self.notification_config.slack_webhook_url:
            results["slack"] = self.send_slack_notification(
                coverage, threshold, metric
            )
        
        if self.notification_config.email_smtp_server:
            results["email"] = self.send_email_notification(
                coverage, threshold, metric
            )
        
        if self.notification_config.sms_api_key:
            results["sms"] = self.send_sms_notification(coverage, threshold, metric)
        
        if self.notification_config.webhook_url:
            results["webhook"] = self.send_webhook_notification(
                coverage, threshold, metric
            )
        
        return results

    def check_and_alert(self) -> Optional[dict]:
        """
        Check coverage threshold and send alerts if needed.
        
        Returns:
            Dictionary with alert details if triggered, None otherwise
        """
        if not self.alert_config.enabled:
            return None
        
        metric = self.check_coverage_threshold()
        
        if metric:
            coverage = metric.coverage_percentage
            threshold = self.alert_config.threshold
            
            # Send notifications
            notification_results = self.send_all_notifications(
                coverage, threshold, metric
            )
            
            return {
                "triggered": True,
                "coverage": coverage,
                "threshold": threshold,
                "metric_id": metric.id,
                "timestamp": metric.timestamp.isoformat(),
                "notifications": notification_results,
            }
        
        return None


def create_prometheus_alert_rules(output_file: str = "prometheus_alerts.yml") -> None:
    """
    Create Prometheus Alertmanager alert rules file.
    
    Args:
        output_file: Path to output file
    """
    rules = {
        "groups": [
            {
                "name": "test-coverage-alerts",
                "interval": "1m",
                "rules": [
                    {
                        "alert": "LowTestCoverage",
                        "expr": "test_coverage_percentage < 80",
                        "for": "5m",
                        "labels": {
                            "severity": "warning",
                            "team": "engineering"
                        },
                        "annotations": {
                            "summary": "Test coverage has dropped below 80%",
                            "description": "Test coverage is currently {{ $value }}%, which is below the 80% threshold. Branch: {{ $labels.branch }}, Test Suite: {{ $labels.test_suite }}"
                        }
                    },
                    {
                        "alert": "CriticalTestCoverage",
                        "expr": "test_coverage_percentage < 70",
                        "for": "2m",
                        "labels": {
                            "severity": "critical",
                            "team": "engineering"
                        },
                        "annotations": {
                            "summary": "Test coverage has dropped below 70% (CRITICAL)",
                            "description": "Test coverage is critically low at {{ $value }}%. Immediate action required. Branch: {{ $labels.branch }}, Test Suite: {{ $labels.test_suite }}"
                        }
                    }
                ]
            }
        ]
    }
    
    import yaml
    
    with open(output_file, "w") as f:
        yaml.dump(rules, f, default_flow_style=False, sort_keys=False)
    
    print(f"[OK] Prometheus alert rules saved to: {output_file}")
    print("Add this file to your Prometheus Alertmanager configuration")


def create_grafana_alert_rules() -> dict:
    """
    Create Grafana alert rules configuration.
    
    Returns:
        Dictionary representing Grafana alert rules
    """
    return {
        "alert": {
            "name": "Low Test Coverage",
            "message": "Test coverage has dropped below threshold",
            "conditions": [
                {
                    "evaluator": {
                        "params": [80],
                        "type": "lt"
                    },
                    "operator": {
                        "type": "and"
                    },
                    "query": {
                        "params": ["A", "5m", "now"]
                    },
                    "reducer": {
                        "params": [],
                        "type": "last"
                    },
                    "type": "query"
                }
            ],
            "executionErrorState": "alerting",
            "for": "5m",
            "frequency": "10s",
            "handler": 1,
            "noDataState": "no_data",
            "notifications": []
        },
        "targets": [
            {
                "expr": "test_coverage_percentage",
                "refId": "A"
            }
        ]
    }


__all__ = [
    "CoverageAlertManager",
    "AlertConfig",
    "NotificationConfig",
    "create_prometheus_alert_rules",
    "create_grafana_alert_rules",
]

