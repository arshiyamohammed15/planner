"""
Policy data models for the Planner Agent.

Defines the structure of policy configurations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tasks.test_task_model import TestType


@dataclass
class AssignmentPolicy:
    """Policy for task assignment based on test type."""

    role_map: Dict[str, str] = field(default_factory=dict)
    """Mapping of test type names to role names.
    
    Example:
        unit: developer
        integration: developer
        e2e: tester
    """

    default_role: Optional[str] = None
    """Default role to assign if test type not found in role_map."""

    def get_role_for_test_type(self, test_type: TestType) -> Optional[str]:
        """Get the role for a given test type."""
        test_type_name = test_type.value.lower()
        return self.role_map.get(test_type_name, self.default_role)


@dataclass
class PriorityPolicy:
    """Policy for test type priorities in plan generation."""

    priorities: Dict[str, int] = field(default_factory=dict)
    """Mapping of test type names to priority values (higher = higher priority).
    
    Example:
        e2e: 5
        integration: 4
        unit: 1
    """

    default_priority: int = 0
    """Default priority if test type not found."""

    def get_priority_for_test_type(self, test_type: TestType) -> int:
        """Get the priority for a given test type."""
        test_type_name = test_type.value.lower()
        return self.priorities.get(test_type_name, self.default_priority)


@dataclass
class TemplatePolicy:
    """Policy for template selection and configuration."""

    default_template: str = "basic"
    """Default template to use if none specified."""

    template_selection_rules: Dict[str, str] = field(default_factory=dict)
    """Rules for selecting templates based on conditions.
    
    Example:
        high_risk: full_coverage
        quick_test: minimal
    """

    def get_template(self, template_name: Optional[str] = None) -> str:
        """Get template name, applying selection rules if needed."""
        if template_name:
            return template_name
        return self.default_template


@dataclass
class ValidationPolicy:
    """Policy for input validation."""

    min_goal_length: int = 1
    """Minimum length for goal field."""

    min_feature_length: int = 1
    """Minimum length for feature field."""

    required_fields: List[str] = field(default_factory=lambda: ["goal", "feature"])
    """List of required field names."""

    max_constraints: Optional[int] = None
    """Maximum number of constraints allowed (None = unlimited)."""


@dataclass
class PolicyConfig:
    """Complete policy configuration for the Planner Agent."""

    assignment: AssignmentPolicy = field(default_factory=AssignmentPolicy)
    priority: PriorityPolicy = field(default_factory=PriorityPolicy)
    template: TemplatePolicy = field(default_factory=TemplatePolicy)
    validation: ValidationPolicy = field(default_factory=ValidationPolicy)

    def reload(self) -> None:
        """Reload policies from files (to be implemented by PolicyLoader)."""
        pass

