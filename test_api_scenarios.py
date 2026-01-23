#!/usr/bin/env python3
"""
Python script for automated API testing.
Usage: python test_api_scenarios.py [--base-url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Optional

import requests


class APITester:
    """API test runner for Planner Agent API."""

    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.verbose = verbose
        self.token: Optional[str] = None
        self.test_results: List[Dict[str, Any]] = []
        self.test_plan_id: Optional[str] = None
        self.test_task_id: Optional[str] = None

    def log_result(
        self,
        test_id: str,
        test_name: str,
        status: str,
        message: str = "",
    ) -> None:
        """Log test result."""
        status_symbol = {"PASS": "✓", "FAIL": "✗", "SKIP": "⊘"}.get(status, "?")
        color_code = {"PASS": "\033[92m", "FAIL": "\033[91m", "SKIP": "\033[93m"}.get(
            status, "\033[0m"
        )
        reset = "\033[0m"

        print(f"{color_code}[{status_symbol}] {test_id} - {test_name}{reset}")
        if message:
            print(f"  {message}")

        self.test_results.append(
            {
                "test_id": test_id,
                "test_name": test_name,
                "status": status,
                "message": message,
            }
        )

    def get_auth_token(self, subject: str = "test-user") -> Optional[str]:
        """Generate authentication token."""
        try:
            response = requests.post(
                f"{self.base_url}/token",
                params={"subject": subject, "expires_minutes": 60},
                timeout=5,
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if token:
                self.token = token
                return token
            return None
        except Exception as e:
            self.log_result(
                "TC-AUTH-001", "Generate Token", "FAIL", f"Failed: {str(e)}"
            )
            return None

    def test_authentication(self) -> bool:
        """Test authentication endpoints."""
        print("\n=== Authentication Tests ===")

        # TC-AUTH-001: Generate Token
        token = self.get_auth_token()
        if token:
            self.log_result("TC-AUTH-001", "Generate Token Successfully", "PASS")

        # TC-AUTH-002: Generate Token with Custom Subject
        try:
            response = requests.post(
                f"{self.base_url}/token",
                params={"subject": "developer", "expires_minutes": 30},
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("subject") == "developer":
                self.log_result(
                    "TC-AUTH-002", "Generate Token with Custom Subject", "PASS"
                )
            else:
                self.log_result(
                    "TC-AUTH-002",
                    "Generate Token with Custom Subject",
                    "FAIL",
                    "Subject mismatch",
                )
        except Exception as e:
            self.log_result(
                "TC-AUTH-002", "Generate Token with Custom Subject", "FAIL", str(e)
            )

        # TC-AUTH-003: Access Protected Endpoint Without Token
        try:
            response = requests.post(
                f"{self.base_url}/plan",
                json={"goal": "test", "feature": "test"},
                timeout=5,
            )
            if response.status_code == 401:
                self.log_result(
                    "TC-AUTH-003", "Access Protected Endpoint Without Token", "PASS"
                )
            else:
                self.log_result(
                    "TC-AUTH-003",
                    "Access Protected Endpoint Without Token",
                    "FAIL",
                    f"Expected 401, got {response.status_code}",
                )
        except Exception as e:
            self.log_result(
                "TC-AUTH-003", "Access Protected Endpoint Without Token", "FAIL", str(e)
            )

        # TC-AUTH-006: Access Public Endpoints
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            self.log_result("TC-AUTH-006", "Access Public Endpoints", "PASS")
        except Exception as e:
            self.log_result("TC-AUTH-006", "Access Public Endpoints", "FAIL", str(e))

        return token is not None

    def test_templates(self) -> None:
        """Test template management endpoints."""
        print("\n=== Template Management Tests ===")

        if not self.token:
            self.log_result("TC-TEMPLATE-001", "List Available Templates", "SKIP")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # TC-TEMPLATE-001: List Available Templates
        try:
            response = requests.get(
                f"{self.base_url}/templates", headers=headers, timeout=5
            )
            response.raise_for_status()
            templates = response.json()
            if isinstance(templates, list) and len(templates) >= 4:
                self.log_result(
                    "TC-TEMPLATE-001",
                    "List Available Templates",
                    "PASS",
                    f"Found {len(templates)} templates",
                )
            else:
                self.log_result(
                    "TC-TEMPLATE-001",
                    "List Available Templates",
                    "FAIL",
                    f"Expected at least 4 templates, got {len(templates) if isinstance(templates, list) else 'non-array'}",
                )
        except Exception as e:
            self.log_result(
                "TC-TEMPLATE-001", "List Available Templates", "FAIL", str(e)
            )

    def test_plan_generation(self) -> None:
        """Test plan generation endpoints."""
        print("\n=== Plan Generation Tests ===")

        if not self.token:
            self.log_result("TC-PLAN-001", "Generate Plan with Basic Template", "SKIP")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # TC-PLAN-001: Generate Plan with Basic Template
        try:
            payload = {
                "goal": "Ensure secure authentication",
                "feature": "User Authentication",
                "template_name": "basic",
                "save_to_database": True,
            }
            response = requests.post(
                f"{self.base_url}/plan",
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if len(data.get("tasks", [])) == 3:
                self.log_result(
                    "TC-PLAN-001",
                    "Generate Plan with Basic Template",
                    "PASS",
                    "Plan created with 3 tasks",
                )
                self.test_plan_id = data.get("plan_id")
                if data.get("tasks"):
                    self.test_task_id = data["tasks"][0].get("id")
            else:
                self.log_result(
                    "TC-PLAN-001",
                    "Generate Plan with Basic Template",
                    "FAIL",
                    f"Expected 3 tasks, got {len(data.get('tasks', []))}",
                )
        except Exception as e:
            self.log_result(
                "TC-PLAN-001", "Generate Plan with Basic Template", "FAIL", str(e)
            )

        # TC-PLAN-002: Generate Plan with Complex Template
        try:
            payload = {
                "goal": "Verify payment processing",
                "feature": "Payment Processing",
                "template_name": "complex",
                "save_to_database": True,
            }
            response = requests.post(
                f"{self.base_url}/plan",
                json=payload,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if len(data.get("tasks", [])) == 6:
                self.log_result(
                    "TC-PLAN-002",
                    "Generate Plan with Complex Template",
                    "PASS",
                    "Plan created with 6 tasks",
                )
            else:
                self.log_result(
                    "TC-PLAN-002",
                    "Generate Plan with Complex Template",
                    "FAIL",
                    f"Expected 6 tasks, got {len(data.get('tasks', []))}",
                )
        except Exception as e:
            self.log_result(
                "TC-PLAN-002", "Generate Plan with Complex Template", "FAIL", str(e)
            )

        # TC-PLAN-009: Generate Plan with Missing Goal
        try:
            payload = {"feature": "User Authentication", "template_name": "basic"}
            response = requests.post(
                f"{self.base_url}/plan",
                json=payload,
                headers=headers,
                timeout=5,
            )
            if response.status_code == 422:
                self.log_result(
                    "TC-PLAN-009", "Generate Plan with Missing Goal", "PASS"
                )
            else:
                self.log_result(
                    "TC-PLAN-009",
                    "Generate Plan with Missing Goal",
                    "FAIL",
                    f"Expected 422, got {response.status_code}",
                )
        except Exception as e:
            if "422" in str(e) or "required" in str(e).lower():
                self.log_result("TC-PLAN-009", "Generate Plan with Missing Goal", "PASS")
            else:
                self.log_result(
                    "TC-PLAN-009", "Generate Plan with Missing Goal", "FAIL", str(e)
                )

        # TC-PLAN-011: Generate Plan with Blank Goal
        try:
            payload = {
                "goal": "",
                "feature": "User Authentication",
                "template_name": "basic",
            }
            response = requests.post(
                f"{self.base_url}/plan",
                json=payload,
                headers=headers,
                timeout=5,
            )
            if response.status_code == 422:
                self.log_result("TC-PLAN-011", "Generate Plan with Blank Goal", "PASS")
            else:
                self.log_result(
                    "TC-PLAN-011",
                    "Generate Plan with Blank Goal",
                    "FAIL",
                    f"Expected 422, got {response.status_code}",
                )
        except Exception as e:
            if "422" in str(e) or "empty" in str(e).lower():
                self.log_result("TC-PLAN-011", "Generate Plan with Blank Goal", "PASS")
            else:
                self.log_result(
                    "TC-PLAN-011", "Generate Plan with Blank Goal", "FAIL", str(e)
                )

        # TC-PLAN-013: Generate Plan with Invalid Template
        try:
            payload = {
                "goal": "Test invalid template",
                "feature": "Test Feature",
                "template_name": "invalid_template",
                "save_to_database": True,
            }
            response = requests.post(
                f"{self.base_url}/plan",
                json=payload,
                headers=headers,
                timeout=5,
            )
            if response.status_code == 400:
                self.log_result(
                    "TC-PLAN-013", "Generate Plan with Invalid Template", "PASS"
                )
            else:
                self.log_result(
                    "TC-PLAN-013",
                    "Generate Plan with Invalid Template",
                    "FAIL",
                    f"Expected 400, got {response.status_code}",
                )
        except Exception as e:
            if "400" in str(e):
                self.log_result(
                    "TC-PLAN-013", "Generate Plan with Invalid Template", "PASS"
                )
            else:
                self.log_result(
                    "TC-PLAN-013",
                    "Generate Plan with Invalid Template",
                    "FAIL",
                    str(e),
                )

    def test_task_retrieval(self) -> None:
        """Test task retrieval endpoints."""
        print("\n=== Task Retrieval Tests ===")

        if not self.token:
            self.log_result("TC-TASK-001", "Get Task Details", "SKIP")
            return

        if not self.test_task_id:
            self.log_result("TC-TASK-001", "Get Task Details", "SKIP", "No task ID")
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # TC-TASK-001: Get Task Details
        try:
            response = requests.get(
                f"{self.base_url}/tasks/{self.test_task_id}",
                headers=headers,
                timeout=5,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("id") and data.get("description"):
                self.log_result("TC-TASK-001", "Get Task Details Successfully", "PASS")
            else:
                self.log_result(
                    "TC-TASK-001", "Get Task Details Successfully", "FAIL", "Missing fields"
                )
        except Exception as e:
            self.log_result("TC-TASK-001", "Get Task Details Successfully", "FAIL", str(e))

        # TC-TASK-002: Get Non-Existent Task
        try:
            response = requests.get(
                f"{self.base_url}/tasks/non-existent-task-id",
                headers=headers,
                timeout=5,
            )
            if response.status_code == 404:
                self.log_result("TC-TASK-002", "Get Non-Existent Task", "PASS")
            else:
                self.log_result(
                    "TC-TASK-002",
                    "Get Non-Existent Task",
                    "FAIL",
                    f"Expected 404, got {response.status_code}",
                )
        except Exception as e:
            if "404" in str(e):
                self.log_result("TC-TASK-002", "Get Non-Existent Task", "PASS")
            else:
                self.log_result("TC-TASK-002", "Get Non-Existent Task", "FAIL", str(e))

        # TC-TASK-003: List All Tasks
        try:
            response = requests.get(f"{self.base_url}/tasks", headers=headers, timeout=5)
            response.raise_for_status()
            tasks = response.json()
            if isinstance(tasks, list):
                self.log_result(
                    "TC-TASK-003", "List All Tasks", "PASS", f"Retrieved {len(tasks)} tasks"
                )
            else:
                self.log_result("TC-TASK-003", "List All Tasks", "FAIL", "Expected array")
        except Exception as e:
            self.log_result("TC-TASK-003", "List All Tasks", "FAIL", str(e))

    def show_summary(self) -> None:
        """Display test summary."""
        print("\n=== Test Summary ===")
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIP")

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")

        if total > 0:
            pass_rate = round((passed / total) * 100, 2)
            color = "\033[92m" if pass_rate >= 80 else "\033[91m"
            print(f"{color}Pass Rate: {pass_rate}%\033[0m")

        if failed > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test_id']}: {result['test_name']}")
                    if result["message"]:
                        print(f"    {result['message']}")

    def run_all_tests(self) -> None:
        """Run all test suites."""
        print("=== Planner Agent API Test Suite ===")
        print(f"Base URL: {self.base_url}\n")

        # Check if API is running
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            print("[OK] API is running\n")
        except Exception as e:
            print(f"[ERROR] API is not accessible at {self.base_url}")
            print("Please start the API server: .\\start_api.ps1")
            sys.exit(1)

        # Run tests
        if self.test_authentication():
            self.test_templates()
            self.test_plan_generation()
            self.test_task_retrieval()

        self.show_summary()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Planner Agent API Test Suite")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    tester = APITester(base_url=args.base_url, verbose=args.verbose)
    tester.run_all_tests()


if __name__ == "__main__":
    main()

