"""
Policy loader for reading and managing policy configurations from YAML files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml

from policies.policy_models import (
    AssignmentPolicy,
    PolicyConfig,
    PriorityPolicy,
    TemplatePolicy,
    ValidationPolicy,
)


class PolicyLoader:
    """Loads and manages policy configurations from YAML files."""

    def __init__(self, policy_dir: Optional[Path] = None):
        """
        Initialize the policy loader.

        Args:
            policy_dir: Directory containing policy files. Defaults to ./policies directory.
        """
        if policy_dir is None:
            # Default to ./policies directory relative to this file
            policy_dir = Path(__file__).parent

        self.policy_dir = Path(policy_dir)
        self._config: Optional[PolicyConfig] = None

    def load(self) -> PolicyConfig:
        """
        Load all policies from YAML files.

        Returns:
            PolicyConfig with all loaded policies

        Raises:
            FileNotFoundError: If policy files are missing
            yaml.YAMLError: If YAML files are malformed
        """
        # Load assignment policy
        assignment = self._load_assignment_policy()

        # Load priority policy
        priority = self._load_priority_policy()

        # Load template policy
        template = self._load_template_policy()

        # Load validation policy
        validation = self._load_validation_policy()

        self._config = PolicyConfig(
            assignment=assignment,
            priority=priority,
            template=template,
            validation=validation,
        )

        return self._config

    def reload(self) -> PolicyConfig:
        """Reload all policies from files."""
        self._config = None
        return self.load()

    def get_config(self) -> PolicyConfig:
        """
        Get the current policy configuration, loading if necessary.

        Returns:
            PolicyConfig instance
        """
        if self._config is None:
            return self.load()
        return self._config

    def _load_assignment_policy(self) -> AssignmentPolicy:
        """Load assignment policy from YAML file."""
        policy_file = self.policy_dir / "assignment_policy.yaml"
        if not policy_file.exists():
            # Return default policy
            return AssignmentPolicy(
                role_map={
                    "unit": "developer",
                    "integration": "developer",
                    "e2e": "tester",
                    "exploratory": "tester",
                    "performance": "performance",
                    "security": "security",
                }
            )

        with open(policy_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        role_map = data.get("role_map", {})
        default_role = data.get("default_role")

        return AssignmentPolicy(role_map=role_map, default_role=default_role)

    def _load_priority_policy(self) -> PriorityPolicy:
        """Load priority policy from YAML file."""
        policy_file = self.policy_dir / "priority_policy.yaml"
        if not policy_file.exists():
            # Return default policy
            return PriorityPolicy(
                priorities={
                    "e2e": 5,
                    "integration": 4,
                    "security": 4,
                    "performance": 3,
                    "exploratory": 2,
                    "unit": 1,
                },
                default_priority=0,
            )

        with open(policy_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        priorities = data.get("priorities", {})
        default_priority = data.get("default_priority", 0)

        return PriorityPolicy(priorities=priorities, default_priority=default_priority)

    def _load_template_policy(self) -> TemplatePolicy:
        """Load template policy from YAML file."""
        policy_file = self.policy_dir / "template_policy.yaml"
        if not policy_file.exists():
            # Return default policy
            return TemplatePolicy(default_template="basic")

        with open(policy_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        default_template = data.get("default_template", "basic")
        selection_rules = data.get("template_selection_rules", {})

        return TemplatePolicy(
            default_template=default_template,
            template_selection_rules=selection_rules,
        )

    def _load_validation_policy(self) -> ValidationPolicy:
        """Load validation policy from YAML file."""
        policy_file = self.policy_dir / "validation_policy.yaml"
        if not policy_file.exists():
            # Return default policy
            return ValidationPolicy(
                min_goal_length=1,
                min_feature_length=1,
                required_fields=["goal", "feature"],
            )

        with open(policy_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        min_goal_length = data.get("min_goal_length", 1)
        min_feature_length = data.get("min_feature_length", 1)
        required_fields = data.get("required_fields", ["goal", "feature"])
        max_constraints = data.get("max_constraints")

        return ValidationPolicy(
            min_goal_length=min_goal_length,
            min_feature_length=min_feature_length,
            required_fields=required_fields,
            max_constraints=max_constraints,
        )


# Global policy loader instance
_global_loader: Optional[PolicyLoader] = None


def get_policy_loader(policy_dir: Optional[Path] = None) -> PolicyLoader:
    """
    Get or create the global policy loader instance.

    Args:
        policy_dir: Directory containing policy files (only used on first call)

    Returns:
        PolicyLoader instance
    """
    global _global_loader
    if _global_loader is None:
        _global_loader = PolicyLoader(policy_dir)
    return _global_loader

