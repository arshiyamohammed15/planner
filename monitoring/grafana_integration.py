"""
Grafana integration for test coverage dashboard visualization.

This module provides tools to set up Grafana data sources, create dashboards,
and manage Grafana integration for displaying test coverage trends.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import urllib.request
import urllib.parse
import base64


class GrafanaIntegration:
    """
    Grafana integration for coverage metrics visualization.
    
    Provides functionality to configure Grafana data sources,
    create and import dashboards, and manage dashboard updates.
    """

    def __init__(
        self,
        grafana_url: str = "http://localhost:3000",
        username: str = "admin",
        password: str = "admin",
    ):
        """
        Initialize Grafana integration.
        
        Args:
            grafana_url: Grafana server URL
            username: Grafana admin username
            password: Grafana admin password
        """
        self.grafana_url = grafana_url.rstrip("/")
        self.username = username
        self.password = password
        self.auth_header = self._create_auth_header()

    def _create_auth_header(self) -> str:
        """Create basic auth header for Grafana API."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Grafana API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., '/api/datasources')
            data: Request body data (optional)
        
        Returns:
            Response JSON as dictionary
        """
        url = f"{self.grafana_url}{endpoint}"
        headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
        }

        req_data = None
        if data:
            req_data = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read().decode("utf-8")
                if response_data:
                    return json.loads(response_data)
                return {}
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise Exception(f"Grafana API error: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"Failed to connect to Grafana: {e}")

    def create_prometheus_datasource(
        self,
        name: str = "Prometheus",
        prometheus_url: str = "http://localhost:9090",
        is_default: bool = True,
    ) -> Dict[str, Any]:
        """
        Create or update Prometheus data source in Grafana.
        
        Args:
            name: Data source name
            prometheus_url: Prometheus server URL
            is_default: Set as default data source
        
        Returns:
            Data source configuration
        """
        datasource_config = {
            "name": name,
            "type": "prometheus",
            "url": prometheus_url,
            "access": "proxy",
            "isDefault": is_default,
            "jsonData": {
                "timeInterval": "15s",
                "httpMethod": "POST",
            },
            "secureJsonData": {},
        }

        # Check if datasource already exists
        try:
            existing = self._make_request("GET", f"/api/datasources/name/{name}")
            datasource_id = existing.get("id")
            
            # Update existing datasource
            endpoint = f"/api/datasources/{datasource_id}"
            result = self._make_request("PUT", endpoint, datasource_config)
            print(f"[OK] Updated Prometheus data source: {name} (ID: {datasource_id})")
        except Exception:
            # Create new datasource
            result = self._make_request("POST", "/api/datasources", datasource_config)
            print(f"[OK] Created Prometheus data source: {name} (ID: {result.get('datasource', {}).get('id', 'N/A')})")
        
        return result

    def create_coverage_dashboard(
        self,
        dashboard_title: str = "Test Coverage Dashboard",
        folder_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a comprehensive Grafana dashboard for test coverage.
        
        Args:
            dashboard_title: Dashboard title
            folder_id: Folder ID to place dashboard in (optional)
        
        Returns:
            Dashboard configuration dictionary
        """
        dashboard = {
            "dashboard": {
                "title": dashboard_title,
                "tags": ["coverage", "testing", "metrics"],
                "timezone": "browser",
                "schemaVersion": 27,
                "version": 0,
                "refresh": "10s",
                "time": {
                    "from": "now-6h",
                    "to": "now"
                },
                "panels": [
                    # Panel 1: Coverage Percentage Gauge
                    {
                        "id": 1,
                        "gridPos": {"x": 0, "y": 0, "w": 6, "h": 4},
                        "type": "gauge",
                        "title": "Current Coverage Percentage",
                        "targets": [
                            {
                                "expr": "test_coverage_percentage",
                                "refId": "A",
                                "legendFormat": "{{test_suite}} - {{branch}}"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "min": 0,
                                "max": 100,
                                "unit": "percent",
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "red"},
                                        {"value": 70, "color": "yellow"},
                                        {"value": 80, "color": "green"}
                                    ]
                                }
                            }
                        },
                        "options": {
                            "orientation": "auto",
                            "reduceOptions": {
                                "values": False,
                                "calcs": ["lastNotNull"],
                                "fields": ""
                            },
                            "showThresholdLabels": False,
                            "showThresholdMarkers": True
                        }
                    },
                    # Panel 2: Coverage Trend Over Time (Line Graph)
                    {
                        "id": 2,
                        "gridPos": {"x": 6, "y": 0, "w": 12, "h": 4},
                        "type": "timeseries",
                        "title": "Coverage Trend Over Time",
                        "targets": [
                            {
                                "expr": "test_coverage_percentage",
                                "refId": "A",
                                "legendFormat": "{{test_suite}} - {{branch}}"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "min": 0,
                                "max": 100,
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "red"},
                                        {"value": 70, "color": "yellow"},
                                        {"value": 80, "color": "green"}
                                    ]
                                }
                            }
                        },
                        "options": {
                            "tooltip": {"mode": "multi"},
                            "legend": {"displayMode": "table", "placement": "bottom"}
                        }
                    },
                    # Panel 3: Covered vs Missing Lines (Bar Chart)
                    {
                        "id": 3,
                        "gridPos": {"x": 18, "y": 0, "w": 6, "h": 4},
                        "type": "barchart",
                        "title": "Covered vs Missing Lines",
                        "targets": [
                            {
                                "expr": "test_coverage_covered_lines",
                                "refId": "A",
                                "legendFormat": "Covered"
                            },
                            {
                                "expr": "test_coverage_missing_lines",
                                "refId": "B",
                                "legendFormat": "Missing"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "custom": {
                                    "displayMode": "gradient",
                                    "orientation": "horizontal"
                                }
                            }
                        }
                    },
                    # Panel 4: Total Lines Stat
                    {
                        "id": 4,
                        "gridPos": {"x": 0, "y": 4, "w": 6, "h": 3},
                        "type": "stat",
                        "title": "Total Lines of Code",
                        "targets": [
                            {
                                "expr": "test_coverage_total_lines",
                                "refId": "A"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "short",
                                "color": {"mode": "palette-classic"}
                            }
                        },
                        "options": {
                            "graphMode": "none",
                            "colorMode": "value"
                        }
                    },
                    # Panel 5: Branch Coverage
                    {
                        "id": 5,
                        "gridPos": {"x": 6, "y": 4, "w": 6, "h": 3},
                        "type": "gauge",
                        "title": "Branch Coverage",
                        "targets": [
                            {
                                "expr": "test_coverage_branch_coverage",
                                "refId": "A",
                                "legendFormat": "{{test_suite}} - {{branch}}"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "min": 0,
                                "max": 100,
                                "unit": "percent",
                                "thresholds": {
                                    "mode": "absolute",
                                    "steps": [
                                        {"value": 0, "color": "red"},
                                        {"value": 70, "color": "yellow"},
                                        {"value": 80, "color": "green"}
                                    ]
                                }
                            }
                        }
                    },
                    # Panel 6: Coverage Trend Indicator
                    {
                        "id": 6,
                        "gridPos": {"x": 12, "y": 4, "w": 6, "h": 3},
                        "type": "stat",
                        "title": "Coverage Trend",
                        "targets": [
                            {
                                "expr": "test_coverage_trend",
                                "refId": "A"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "mappings": [
                                    {
                                        "type": "value",
                                        "options": {
                                            "0": {"text": "Stable", "color": "blue"},
                                            "1": {"text": "Increasing", "color": "green"},
                                            "-1": {"text": "Decreasing", "color": "red"}
                                        }
                                    }
                                ]
                            }
                        },
                        "options": {
                            "graphMode": "none",
                            "colorMode": "value"
                        }
                    },
                    # Panel 7: Coverage by Test Suite (Table)
                    {
                        "id": 7,
                        "gridPos": {"x": 18, "y": 4, "w": 6, "h": 3},
                        "type": "table",
                        "title": "Coverage by Test Suite",
                        "targets": [
                            {
                                "expr": "test_coverage_percentage",
                                "refId": "A",
                                "format": "table",
                                "instant": True
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "custom": {
                                    "displayMode": "color-background"
                                }
                            }
                        }
                    },
                    # Panel 8: Coverage Change (Delta)
                    {
                        "id": 8,
                        "gridPos": {"x": 0, "y": 7, "w": 12, "h": 4},
                        "type": "timeseries",
                        "title": "Coverage Change Over Time",
                        "targets": [
                            {
                                "expr": "test_coverage_percentage - test_coverage_percentage offset 1h",
                                "refId": "A",
                                "legendFormat": "Change (1h)"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "percent",
                                "color": {"mode": "palette-classic"}
                            }
                        }
                    },
                    # Panel 9: Last Updated Timestamp
                    {
                        "id": 9,
                        "gridPos": {"x": 12, "y": 7, "w": 12, "h": 4},
                        "type": "stat",
                        "title": "Last Updated",
                        "targets": [
                            {
                                "expr": "test_coverage_last_updated_timestamp",
                                "refId": "A",
                                "format": "time_series"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "unit": "dateTimeFromNow"
                            }
                        },
                        "options": {
                            "graphMode": "none"
                        }
                    }
                ]
            },
            "overwrite": False,
            "folderId": folder_id,
        }
        
        return dashboard

    def import_dashboard(self, dashboard_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Import a dashboard into Grafana.
        
        Args:
            dashboard_config: Dashboard configuration dictionary
        
        Returns:
            Import result
        """
        result = self._make_request("POST", "/api/dashboards/db", dashboard_config)
        return result

    def get_dashboard_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get dashboard by UID.
        
        Args:
            uid: Dashboard UID
        
        Returns:
            Dashboard configuration or None
        """
        try:
            return self._make_request("GET", f"/api/dashboards/uid/{uid}")
        except Exception:
            return None

    def list_dashboards(self) -> List[Dict[str, Any]]:
        """
        List all dashboards.
        
        Returns:
            List of dashboard summaries
        """
        try:
            result = self._make_request("GET", "/api/search?type=dash-db")
            return result
        except Exception:
            return []

    def verify_connection(self) -> Dict[str, Any]:
        """
        Verify connection to Grafana.
        
        Returns:
            Verification results
        """
        results = {
            "connected": False,
            "version": None,
            "datasources": [],
            "errors": [],
        }
        
        try:
            # Test connection with health check
            health = self._make_request("GET", "/api/health")
            results["connected"] = True
            
            # Get Grafana version
            try:
                version_info = self._make_request("GET", "/api/health")
                results["version"] = version_info.get("version", "unknown")
            except Exception:
                pass
            
            # List data sources
            try:
                datasources = self._make_request("GET", "/api/datasources")
                results["datasources"] = [
                    {"name": ds.get("name"), "type": ds.get("type")}
                    for ds in datasources
                ]
            except Exception as e:
                results["errors"].append(f"Failed to list datasources: {e}")
        
        except Exception as e:
            results["errors"].append(str(e))
        
        return results

    def setup_complete_integration(
        self,
        prometheus_url: str = "http://localhost:9090",
        dashboard_title: str = "Test Coverage Dashboard",
    ) -> Dict[str, Any]:
        """
        Complete setup: create datasource and import dashboard.
        
        Args:
            prometheus_url: Prometheus server URL
            dashboard_title: Dashboard title
        
        Returns:
            Setup results
        """
        results = {
            "datasource_created": False,
            "dashboard_imported": False,
            "dashboard_url": None,
            "errors": [],
        }
        
        try:
            # Create Prometheus data source
            datasource_result = self.create_prometheus_datasource(
                prometheus_url=prometheus_url
            )
            results["datasource_created"] = True
            
            # Create and import dashboard
            dashboard_config = self.create_coverage_dashboard(
                dashboard_title=dashboard_title
            )
            import_result = self.import_dashboard(dashboard_config)
            
            if import_result.get("status") == "success":
                results["dashboard_imported"] = True
                dashboard_uid = import_result.get("uid")
                results["dashboard_url"] = f"{self.grafana_url}/d/{dashboard_uid}"
        
        except Exception as e:
            results["errors"].append(str(e))
        
        return results


def save_dashboard_json(
    dashboard_config: Dict[str, Any],
    output_file: str = "monitoring/grafana_coverage_dashboard.json",
) -> None:
    """
    Save dashboard configuration to JSON file.
    
    Args:
        dashboard_config: Dashboard configuration
        output_file: Output file path
    """
    with open(output_file, "w") as f:
        json.dump(dashboard_config, f, indent=2)
    
    print(f"[OK] Dashboard JSON saved to: {output_file}")


def load_dashboard_json(file_path: str) -> Dict[str, Any]:
    """
    Load dashboard configuration from JSON file.
    
    Args:
        file_path: JSON file path
    
    Returns:
        Dashboard configuration
    """
    with open(file_path, "r") as f:
        return json.load(f)


def main() -> None:
    """CLI entry point for Grafana integration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Grafana Integration for Coverage Dashboard")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Complete Grafana setup")
    setup_parser.add_argument(
        "--grafana-url", type=str, default="http://localhost:3000",
        help="Grafana URL (default: http://localhost:3000)"
    )
    setup_parser.add_argument(
        "--username", type=str, default="admin",
        help="Grafana username (default: admin)"
    )
    setup_parser.add_argument(
        "--password", type=str, default="admin",
        help="Grafana password (default: admin)"
    )
    setup_parser.add_argument(
        "--prometheus-url", type=str, default="http://localhost:9090",
        help="Prometheus URL (default: http://localhost:9090)"
    )
    
    # Create datasource command
    datasource_parser = subparsers.add_parser("create-datasource", help="Create Prometheus datasource")
    datasource_parser.add_argument("--name", type=str, default="Prometheus")
    datasource_parser.add_argument("--prometheus-url", type=str, default="http://localhost:9090")
    
    # Import dashboard command
    import_parser = subparsers.add_parser("import-dashboard", help="Import dashboard")
    import_parser.add_argument("--file", type=str, help="Dashboard JSON file")
    import_parser.add_argument("--title", type=str, default="Test Coverage Dashboard")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify Grafana connection")
    verify_parser.add_argument("--grafana-url", type=str, default="http://localhost:3000")
    verify_parser.add_argument("--username", type=str, default="admin")
    verify_parser.add_argument("--password", type=str, default="admin")
    
    # Save dashboard command
    save_parser = subparsers.add_parser("save-dashboard", help="Save dashboard JSON")
    save_parser.add_argument("--output", type=str, default="monitoring/grafana_coverage_dashboard.json")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        grafana = GrafanaIntegration(
            grafana_url=args.grafana_url,
            username=args.username,
            password=args.password,
        )
        results = grafana.setup_complete_integration(
            prometheus_url=args.prometheus_url
        )
        
        if results["datasource_created"]:
            print("[OK] Prometheus data source created")
        if results["dashboard_imported"]:
            print(f"[OK] Dashboard imported: {results['dashboard_url']}")
        if results["errors"]:
            print(f"[ERROR] {results['errors']}")
    
    elif args.command == "create-datasource":
        grafana = GrafanaIntegration()
        grafana.create_prometheus_datasource(
            name=args.name,
            prometheus_url=args.prometheus_url
        )
    
    elif args.command == "import-dashboard":
        grafana = GrafanaIntegration()
        if args.file:
            dashboard_config = load_dashboard_json(args.file)
        else:
            dashboard_config = grafana.create_coverage_dashboard(
                dashboard_title=args.title
            )
        result = grafana.import_dashboard(dashboard_config)
        if result.get("status") == "success":
            print(f"[OK] Dashboard imported: {result.get('url', 'N/A')}")
    
    elif args.command == "verify":
        grafana = GrafanaIntegration(
            grafana_url=args.grafana_url,
            username=args.username,
            password=args.password,
        )
        results = grafana.verify_connection()
        
        if results["connected"]:
            print("[OK] Connected to Grafana")
            if results["version"]:
                print(f"  Version: {results['version']}")
            if results["datasources"]:
                print(f"  Data sources: {len(results['datasources'])}")
                for ds in results["datasources"]:
                    print(f"    - {ds['name']} ({ds['type']})")
        else:
            print("[FAILED] Could not connect to Grafana")
            if results["errors"]:
                for error in results["errors"]:
                    print(f"  Error: {error}")
    
    elif args.command == "save-dashboard":
        grafana = GrafanaIntegration()
        dashboard = grafana.create_coverage_dashboard()
        save_dashboard_json(dashboard, args.output)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


__all__ = [
    "GrafanaIntegration",
    "save_dashboard_json",
    "load_dashboard_json",
    "create_coverage_dashboard",
]

