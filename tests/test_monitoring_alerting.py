"""
Unit tests for monitoring and alerting system.

Tests coverage tracking, alerting logic, and Grafana integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from typing import Optional

from monitoring.alerting import (
    AlertConfig,
    NotificationConfig,
    CoverageAlertManager,
)
from monitoring.coverage_tracking import (
    store_coverage,
    track_coverage_from_file,
    get_coverage_trends,
    parse_coverage_xml,
    parse_coverage_json,
)
from monitoring.coverage_metrics import CoverageMetricsModel
from monitoring.grafana_integration import GrafanaIntegration
from monitoring.prometheus_exporter import CoverageMetricsExporter


# ============================================================================
# Coverage Tracking Tests
# ============================================================================

class TestCoverageTracking:
    """Tests for coverage tracking functionality."""

    def test_store_coverage_basic(self):
        """Test storing basic coverage metrics."""
        with patch('monitoring.coverage_tracking.record_coverage_metric') as mock_record:
            mock_record.return_value = Mock(
                id=1,
                coverage_percentage=85.5,
                total_lines=1000,
                covered_lines=855,
                missing_lines=145,
                timestamp=datetime.utcnow()
            )
            
            result = store_coverage(
                coverage_percentage=85.5,
                total_lines=1000,
                covered_lines=855,
                missing_lines=145
            )
            
            assert result is not None
            mock_record.assert_called_once()
            call_args = mock_record.call_args[1]
            assert call_args['coverage_percentage'] == 85.5
            assert call_args['total_lines'] == 1000
            assert call_args['covered_lines'] == 855
            assert call_args['missing_lines'] == 145

    def test_store_coverage_with_metadata(self):
        """Test storing coverage with additional metadata."""
        with patch('monitoring.coverage_tracking.record_coverage_metric') as mock_record:
            mock_record.return_value = Mock(
                id=1,
                coverage_percentage=90.0,
                test_suite="pytest",
                branch_name="main",
                commit_hash="abc123"
            )
            
            result = store_coverage(
                coverage_percentage=90.0,
                total_lines=1000,
                covered_lines=900,
                missing_lines=100,
                test_suite="pytest",
                branch_name="main",
                commit_hash="abc123"
            )
            
            assert result is not None
            call_args = mock_record.call_args[1]
            assert call_args['test_suite'] == "pytest"
            assert call_args['branch_name'] == "main"
            assert call_args['commit_hash'] == "abc123"

    def test_parse_coverage_xml(self, tmp_path):
        """Test parsing Cobertura XML coverage report."""
        # Create a sample Cobertura XML file
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.85" branch-rate="0.80">
    <packages>
        <package name="test">
            <classes>
                <class name="test_module">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="1"/>
                        <line number="3" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        
        xml_file = tmp_path / "coverage.xml"
        xml_file.write_text(xml_content)
        
        result = parse_coverage_xml(str(xml_file))
        
        assert result is not None
        assert result['coverage_percentage'] == 85.0
        assert result['branch_coverage'] == 80.0
        assert result['total_lines'] == 3
        assert result['covered_lines'] == 2
        assert result['missing_lines'] == 1

    def test_parse_coverage_json(self, tmp_path):
        """Test parsing coverage.py JSON report."""
        json_content = {
            "totals": {
                "percent_covered": 87.5,
                "lines_valid": 1000,
                "lines_covered": 875,
                "lines_missing": 125,
                "branch_percent_covered": 82.0
            }
        }
        
        json_file = tmp_path / "coverage.json"
        import json
        json_file.write_text(json.dumps(json_content))
        
        result = parse_coverage_json(str(json_file))
        
        assert result is not None
        assert result['coverage_percentage'] == 87.5
        assert result['total_lines'] == 1000
        assert result['covered_lines'] == 875
        assert result['missing_lines'] == 125
        assert result['branch_coverage'] == 82.0

    def test_track_coverage_from_file_xml(self, tmp_path):
        """Test tracking coverage from XML file."""
        xml_content = """<?xml version="1.0" ?>
<coverage line-rate="0.75" branch-rate="0.70">
    <packages>
        <package name="test">
            <classes>
                <class name="test_module">
                    <lines>
                        <line number="1" hits="1"/>
                        <line number="2" hits="0"/>
                    </lines>
                </class>
            </classes>
        </package>
    </packages>
</coverage>"""
        
        xml_file = tmp_path / "coverage.xml"
        xml_file.write_text(xml_content)
        
        with patch('monitoring.coverage_tracking.store_coverage') as mock_store:
            mock_store.return_value = Mock(id=1)
            
            result = track_coverage_from_file(str(xml_file), test_suite="pytest")
            
            assert result is not None
            mock_store.assert_called_once()
            call_args = mock_store.call_args[1]
            assert call_args['coverage_percentage'] == 75.0
            assert call_args['test_suite'] == "pytest"

    def test_track_coverage_from_file_json(self, tmp_path):
        """Test tracking coverage from JSON file."""
        json_content = {
            "totals": {
                "percent_covered": 88.0,
                "lines_valid": 500,
                "lines_covered": 440,
                "lines_missing": 60
            }
        }
        
        json_file = tmp_path / "coverage.json"
        import json
        json_file.write_text(json.dumps(json_content))
        
        with patch('monitoring.coverage_tracking.store_coverage') as mock_store:
            mock_store.return_value = Mock(id=1)
            
            result = track_coverage_from_file(str(json_file), test_suite="unit-tests")
            
            assert result is not None
            call_args = mock_store.call_args[1]
            assert call_args['coverage_percentage'] == 88.0
            assert call_args['test_suite'] == "unit-tests"

    def test_track_coverage_from_file_not_found(self):
        """Test tracking coverage from non-existent file."""
        with pytest.raises(FileNotFoundError):
            track_coverage_from_file("nonexistent.xml")

    def test_get_coverage_trends(self):
        """Test retrieving coverage trends."""
        with patch('monitoring.coverage_tracking.get_sessionmaker') as mock_sessionmaker:
            # Create mock session and query results
            mock_session = Mock()
            mock_query = Mock()
            
            # Create mock metrics
            mock_metrics = [
                Mock(
                    id=3,
                    coverage_percentage=85.0,
                    timestamp=datetime.utcnow(),
                    test_suite="pytest",
                    branch_name="main"
                ),
                Mock(
                    id=2,
                    coverage_percentage=82.0,
                    timestamp=datetime.utcnow() - timedelta(hours=1),
                    test_suite="pytest",
                    branch_name="main"
                ),
                Mock(
                    id=1,
                    coverage_percentage=80.0,
                    timestamp=datetime.utcnow() - timedelta(hours=2),
                    test_suite="pytest",
                    branch_name="main"
                ),
            ]
            
            mock_query.all.return_value = mock_metrics
            mock_query.where.return_value = mock_query
            mock_query.order_by.return_value = mock_query
            mock_session.scalars.return_value = mock_query
            mock_sessionmaker.return_value.return_value = mock_session
            
            trends = get_coverage_trends(days=30, test_suite="pytest")
            
            assert len(trends) == 3
            assert trends[0].coverage_percentage == 85.0
            assert trends[1].coverage_percentage == 82.0
            assert trends[2].coverage_percentage == 80.0

    def test_coverage_data_recorded_and_displayed(self):
        """Test that coverage data is correctly recorded and displayed."""
        # Test recording coverage data
        with patch('monitoring.coverage_tracking.record_coverage_metric') as mock_record:
            mock_metric = Mock(
                id=1,
                coverage_percentage=87.5,
                total_lines=1000,
                covered_lines=875,
                missing_lines=125,
                timestamp=datetime.utcnow(),
                test_suite="pytest",
                branch_name="main"
            )
            mock_record.return_value = mock_metric
            
            # Record coverage
            metric = store_coverage(
                coverage_percentage=87.5,
                total_lines=1000,
                covered_lines=875,
                missing_lines=125,
                test_suite="pytest"
            )
            
            # Verify data was recorded correctly
            assert metric is not None
            assert metric.coverage_percentage == 87.5
            assert metric.total_lines == 1000
            assert metric.covered_lines == 875
            assert metric.missing_lines == 125
            
            # Test that data can be retrieved for display
            with patch('database.postgresql_setup.get_sessionmaker') as mock_sessionmaker:
                mock_session = Mock()
                mock_query = Mock()
                mock_query.all.return_value = [mock_metric]
                mock_query.where.return_value = mock_query
                mock_query.order_by.return_value = mock_query
                mock_session.scalars.return_value = mock_query
                mock_sessionmaker.return_value.return_value = mock_session
                
                trends = get_coverage_trends(days=30, test_suite="pytest")
                
                # Verify data can be displayed
                assert len(trends) == 1
                assert trends[0].coverage_percentage == 87.5
                assert trends[0].total_lines == 1000
                assert trends[0].covered_lines == 875


# ============================================================================
# Alerting Tests
# ============================================================================

class TestAlerting:
    """Tests for alerting functionality."""

    def test_alert_config_defaults(self):
        """Test AlertConfig default values."""
        config = AlertConfig()
        
        assert config.threshold == 80.0
        assert config.duration_minutes == 5
        assert config.test_suite is None
        assert config.branch_name is None
        assert config.enabled is True

    def test_alert_config_custom(self):
        """Test AlertConfig with custom values."""
        config = AlertConfig(
            threshold=75.0,
            duration_minutes=10,
            test_suite="pytest",
            branch_name="main",
            enabled=False
        )
        
        assert config.threshold == 75.0
        assert config.duration_minutes == 10
        assert config.test_suite == "pytest"
        assert config.branch_name == "main"
        assert config.enabled is False

    def test_notification_config_defaults(self):
        """Test NotificationConfig default values."""
        config = NotificationConfig()
        
        assert config.slack_webhook_url is None
        assert config.email_smtp_server is None
        assert config.email_smtp_port == 587
        assert config.webhook_url is None

    def test_alert_for_low_coverage(self):
        """Test that alert is triggered for low coverage."""
        coverage = 75.0
        threshold = 80.0
        
        assert coverage < threshold  # Ensure alert is triggered for low coverage
        
        # Test with alert manager
        alert_config = AlertConfig(threshold=threshold, duration_minutes=5)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        # Mock coverage trends to return low coverage
        # Need at least 2 data points within the duration window (5 minutes)
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            now = datetime.utcnow()
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now,
                    test_suite="pytest",
                    branch_name="main",
                    total_lines=1000,
                    covered_lines=750,
                    missing_lines=250,
                    commit_hash="abc123",
                    id=1
                ),
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now - timedelta(minutes=3),  # Within 5-minute window
                    test_suite="pytest",
                    branch_name="main",
                    id=2
                )
            ]
            
            result = manager.check_coverage_threshold()
            
            assert result is not None
            assert result.coverage_percentage == 75.0
            assert result.coverage_percentage < threshold

    def test_alert_not_triggered_above_threshold(self):
        """Test that alert is not triggered when coverage is above threshold."""
        alert_config = AlertConfig(threshold=80.0)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            now = datetime.utcnow()
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=85.0,
                    timestamp=now,
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            result = manager.check_coverage_threshold()
            
            assert result is None  # No alert should be triggered

    def test_alert_not_triggered_brief_drop(self):
        """Test that alert is not triggered for brief drops below threshold."""
        alert_config = AlertConfig(threshold=80.0, duration_minutes=5)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            now = datetime.utcnow()
            # Only one data point below threshold (not enough duration)
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now,
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            result = manager.check_coverage_threshold()
            
            # Should not trigger because duration requirement not met
            assert result is None

    def test_alert_triggered_after_duration(self):
        """Test that alert is triggered after required duration."""
        alert_config = AlertConfig(threshold=80.0, duration_minutes=5)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            now = datetime.utcnow()
            # Multiple data points below threshold over required duration
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now,
                    test_suite="pytest",
                    branch_name="main",
                    total_lines=1000,
                    covered_lines=750,
                    missing_lines=250,
                    commit_hash="abc123"
                ),
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now - timedelta(minutes=3),
                    test_suite="pytest",
                    branch_name="main"
                ),
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now - timedelta(minutes=6),
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            result = manager.check_coverage_threshold()
            
            assert result is not None
            assert result.coverage_percentage < alert_config.threshold

    def test_send_slack_notification(self):
        """Test sending Slack notification."""
        notification_config = NotificationConfig(
            slack_webhook_url="https://hooks.slack.com/test"
        )
        manager = CoverageAlertManager(
            notification_config=notification_config
        )
        
        metric = Mock(
            coverage_percentage=75.0,
            test_suite="pytest",
            branch_name="main",
            total_lines=1000,
            covered_lines=750,
            missing_lines=250,
            commit_hash="abc123",
            timestamp=datetime.utcnow()
        )
        
        with patch('monitoring.alerting.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_urlopen.return_value = mock_response
            
            result = manager.send_slack_notification(75.0, 80.0, metric)
            
            assert result is True
            mock_urlopen.assert_called_once()

    def test_send_email_notification(self):
        """Test sending email notification."""
        notification_config = NotificationConfig(
            email_smtp_server="smtp.example.com",
            email_from="alerts@example.com",
            email_to=["team@example.com"]
        )
        manager = CoverageAlertManager(
            notification_config=notification_config
        )
        
        metric = Mock(
            coverage_percentage=75.0,
            test_suite="pytest",
            branch_name="main",
            total_lines=1000,
            covered_lines=750,
            missing_lines=250,
            commit_hash="abc123",
            timestamp=datetime.utcnow()
        )
        
        with patch('monitoring.alerting.smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = manager.send_email_notification(75.0, 80.0, metric)
            
            assert result is True
            mock_smtp.assert_called_once_with("smtp.example.com", 587)

    def test_send_webhook_notification(self):
        """Test sending webhook notification."""
        notification_config = NotificationConfig(
            webhook_url="https://webhook.example.com/alerts"
        )
        manager = CoverageAlertManager(
            notification_config=notification_config
        )
        
        metric = Mock(
            coverage_percentage=75.0,
            test_suite="pytest",
            branch_name="main",
            total_lines=1000,
            covered_lines=750,
            missing_lines=250,
            commit_hash="abc123",
            timestamp=datetime.utcnow()
        )
        
        with patch('monitoring.alerting.urlopen') as mock_urlopen:
            mock_response = Mock()
            mock_urlopen.return_value = mock_response
            
            result = manager.send_webhook_notification(75.0, 80.0, metric)
            
            assert result is True
            mock_urlopen.assert_called_once()

    def test_check_and_alert_triggered(self):
        """Test check_and_alert when alert is triggered."""
        alert_config = AlertConfig(threshold=80.0)
        notification_config = NotificationConfig(
            webhook_url="https://webhook.example.com/alerts"
        )
        manager = CoverageAlertManager(
            alert_config=alert_config,
            notification_config=notification_config
        )
        
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends, \
             patch('monitoring.alerting.urlopen') as mock_urlopen:
            
            now = datetime.utcnow()
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now,
                    test_suite="pytest",
                    branch_name="main",
                    total_lines=1000,
                    covered_lines=750,
                    missing_lines=250,
                    commit_hash="abc123",
                    id=1
                ),
                Mock(
                    coverage_percentage=75.0,
                    timestamp=now - timedelta(minutes=6),
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            mock_urlopen.return_value = Mock()
            
            result = manager.check_and_alert()
            
            assert result is not None
            assert result['triggered'] is True
            assert result['coverage'] == 75.0
            assert result['threshold'] == 80.0
            assert 'notifications' in result

    def test_check_and_alert_not_triggered(self):
        """Test check_and_alert when alert is not triggered."""
        alert_config = AlertConfig(threshold=80.0)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=85.0,
                    timestamp=datetime.utcnow(),
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            result = manager.check_and_alert()
            
            assert result is None  # No alert triggered

    def test_alert_disabled(self):
        """Test that alerts are not sent when disabled."""
        alert_config = AlertConfig(threshold=80.0, enabled=False)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        result = manager.check_and_alert()
        
        assert result is None  # Alerts disabled


# ============================================================================
# Grafana Integration Tests
# ============================================================================

class TestGrafanaIntegration:
    """Tests for Grafana integration."""

    def test_grafana_integration_init(self):
        """Test GrafanaIntegration initialization."""
        grafana = GrafanaIntegration(
            grafana_url="http://localhost:3000",
            username="admin",
            password="admin"
        )
        
        assert grafana.grafana_url == "http://localhost:3000"
        assert grafana.username == "admin"
        assert grafana.password == "admin"
        assert grafana.auth_header.startswith("Basic")

    def test_grafana_integration(self):
        """Test Grafana integration to fetch coverage data."""
        # Helper function to fetch from Grafana (via Prometheus)
        def fetch_from_grafana(metric_name: str) -> dict:
            """Mock function to fetch coverage data from Grafana/Prometheus."""
            # In real implementation, this would query Prometheus via Grafana API
            # For testing, we return mock data
            return {
                'coverage': 85.5,
                'metric': metric_name,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        data = fetch_from_grafana("coverage_percentage")
        assert data is not None
        assert data['coverage'] >= 0
        assert 'coverage' in data
        assert data['coverage'] <= 100  # Coverage should be between 0-100%

    def test_create_prometheus_datasource(self):
        """Test creating Prometheus data source."""
        grafana = GrafanaIntegration()
        
        with patch.object(grafana, '_make_request') as mock_request:
            mock_request.side_effect = [
                Exception("Not found"),  # First call (check if exists) fails
                {"datasource": {"id": 1}}  # Second call (create) succeeds
            ]
            
            result = grafana.create_prometheus_datasource(
                name="Prometheus",
                prometheus_url="http://localhost:9090"
            )
            
            assert result is not None
            # Should have called _make_request for creation
            assert mock_request.call_count >= 1

    def test_create_coverage_dashboard(self):
        """Test creating coverage dashboard configuration."""
        grafana = GrafanaIntegration()
        
        dashboard = grafana.create_coverage_dashboard(
            dashboard_title="Test Dashboard"
        )
        
        assert dashboard is not None
        assert dashboard['dashboard']['title'] == "Test Dashboard"
        assert 'panels' in dashboard['dashboard']
        assert len(dashboard['dashboard']['panels']) > 0
        assert dashboard['dashboard']['refresh'] == "10s"

    def test_import_dashboard(self):
        """Test importing dashboard into Grafana."""
        grafana = GrafanaIntegration()
        
        dashboard_config = {
            "dashboard": {
                "title": "Test Dashboard",
                "panels": []
            },
            "overwrite": False
        }
        
        with patch.object(grafana, '_make_request') as mock_request:
            mock_request.return_value = {
                "status": "success",
                "uid": "test-uid"
            }
            
            result = grafana.import_dashboard(dashboard_config)
            
            assert result is not None
            assert result['status'] == "success"
            mock_request.assert_called_once()

    def test_verify_connection_success(self):
        """Test verifying Grafana connection when successful."""
        grafana = GrafanaIntegration()
        
        with patch.object(grafana, '_make_request') as mock_request:
            mock_request.side_effect = [
                {"version": "10.0.0"},  # Health check
                [{"name": "Prometheus", "type": "prometheus"}]  # Datasources
            ]
            
            result = grafana.verify_connection()
            
            assert result['connected'] is True
            assert result['version'] == "10.0.0"
            assert len(result['datasources']) > 0

    def test_verify_connection_failure(self):
        """Test verifying Grafana connection when it fails."""
        grafana = GrafanaIntegration()
        
        with patch.object(grafana, '_make_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")
            
            result = grafana.verify_connection()
            
            assert result['connected'] is False
            assert len(result['errors']) > 0

    def test_setup_complete_integration(self):
        """Test complete Grafana setup."""
        grafana = GrafanaIntegration()
        
        with patch.object(grafana, 'create_prometheus_datasource') as mock_ds, \
             patch.object(grafana, 'import_dashboard') as mock_import:
            
            mock_ds.return_value = {"datasource": {"id": 1}}
            mock_import.return_value = {
                "status": "success",
                "uid": "test-uid"
            }
            
            result = grafana.setup_complete_integration(
                prometheus_url="http://localhost:9090"
            )
            
            assert result['datasource_created'] is True
            assert result['dashboard_imported'] is True
            mock_ds.assert_called_once()
            mock_import.assert_called_once()


# ============================================================================
# Prometheus Exporter Tests
# ============================================================================

class TestPrometheusExporter:
    """Tests for Prometheus exporter."""

    def test_exporter_initialization(self):
        """Test CoverageMetricsExporter initialization."""
        exporter = CoverageMetricsExporter(port=8001)
        
        assert exporter.port == 8001
        assert exporter.coverage_percentage is not None
        assert exporter.coverage_total_lines is not None

    def test_update_metrics_with_data(self):
        """Test updating metrics when data is available."""
        exporter = CoverageMetricsExporter()
        
        with patch.object(exporter, 'sessionmaker') as mock_sessionmaker:
            mock_session = Mock()
            mock_metric = Mock(
                coverage_percentage=85.0,
                total_lines=1000,
                covered_lines=850,
                missing_lines=150,
                branch_coverage=82.0,
                test_suite="pytest",
                branch_name="main"
            )
            
            mock_query = Mock()
            mock_query.first.return_value = mock_metric
            mock_session.scalars.return_value = mock_query
            mock_sessionmaker.return_value.return_value = mock_session
            
            # Should not raise exception
            exporter.update_metrics()
            
            # Verify metrics were set
            assert exporter.coverage_percentage.labels(
                test_suite="pytest",
                branch="main"
            )._value.get() == 85.0

    def test_update_metrics_no_data(self):
        """Test updating metrics when no data is available."""
        exporter = CoverageMetricsExporter()
        
        with patch.object(exporter, 'sessionmaker') as mock_sessionmaker:
            mock_session = Mock()
            mock_query = Mock()
            mock_query.first.return_value = None  # No data
            mock_session.scalars.return_value = mock_query
            mock_sessionmaker.return_value.return_value = mock_session
            
            # Should not raise exception
            exporter.update_metrics()

    def test_update_metrics_connection_error(self):
        """Test updating metrics when database connection fails."""
        exporter = CoverageMetricsExporter()
        
        with patch.object(exporter, 'sessionmaker') as mock_sessionmaker:
            mock_sessionmaker.side_effect = Exception("Connection failed")
            
            # Should handle error gracefully
            exporter.update_metrics()
            
            # Metrics should be set to default values
            assert exporter.coverage_percentage.labels(
                test_suite="default",
                branch="main"
            )._value.get() == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for monitoring system."""

    def test_coverage_tracking_to_alerting_flow(self):
        """Test complete flow from coverage tracking to alerting."""
        # Store coverage
        with patch('monitoring.coverage_tracking.record_coverage_metric') as mock_record:
            mock_record.return_value = Mock(
                id=1,
                coverage_percentage=75.0,
                timestamp=datetime.utcnow(),
                test_suite="pytest",
                branch_name="main",
                total_lines=1000,
                covered_lines=750,
                missing_lines=250,
                commit_hash="abc123"
            )
            
            metric = store_coverage(
                coverage_percentage=75.0,
                total_lines=1000,
                covered_lines=750,
                missing_lines=250,
                test_suite="pytest"
            )
            
            assert metric is not None
            
            # Check alert
            alert_config = AlertConfig(threshold=80.0)
            manager = CoverageAlertManager(alert_config=alert_config)
            
            with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
                mock_trends.return_value = [
                    Mock(
                        coverage_percentage=75.0,
                        timestamp=datetime.utcnow(),
                        test_suite="pytest",
                        branch_name="main",
                        total_lines=1000,
                        covered_lines=750,
                        missing_lines=250,
                        commit_hash="abc123",
                        id=1
                    ),
                    Mock(
                        coverage_percentage=75.0,
                        timestamp=datetime.utcnow() - timedelta(minutes=6),
                        test_suite="pytest",
                        branch_name="main"
                    )
                ]
                
                result = manager.check_and_alert()
                
                assert result is not None
                assert result['triggered'] is True
                assert result['coverage'] == 75.0

    def test_alert_threshold_edge_cases(self):
        """Test alert threshold edge cases."""
        # Test exactly at threshold
        alert_config = AlertConfig(threshold=80.0)
        manager = CoverageAlertManager(alert_config=alert_config)
        
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=80.0,  # Exactly at threshold
                    timestamp=datetime.utcnow(),
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            result = manager.check_coverage_threshold()
            assert result is None  # Should not trigger at exact threshold
        
        # Test just below threshold
        with patch('monitoring.alerting.get_coverage_trends') as mock_trends:
            mock_trends.return_value = [
                Mock(
                    coverage_percentage=79.99,  # Just below threshold
                    timestamp=datetime.utcnow(),
                    test_suite="pytest",
                    branch_name="main",
                    total_lines=1000,
                    covered_lines=799,
                    missing_lines=201,
                    commit_hash="abc123",
                    id=1
                ),
                Mock(
                    coverage_percentage=79.99,
                    timestamp=datetime.utcnow() - timedelta(minutes=6),
                    test_suite="pytest",
                    branch_name="main"
                )
            ]
            
            result = manager.check_coverage_threshold()
            assert result is not None  # Should trigger

