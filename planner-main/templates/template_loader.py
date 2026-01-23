"""
Template loader for loading test plan templates from YAML files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml

from tasks.test_task_model import TestType
from templates.test_plan_templates import (
    TEMPLATE_REGISTRY,
    TaskTemplate,
    TestPlanTemplate,
)


class TemplateLoader:
    """Loads test plan templates from YAML files."""

    def __init__(self, template_dir: Optional[Path] = None):
        """
        Initialize the template loader.

        Args:
            template_dir: Directory containing template YAML files.
                         Defaults to ./templates/templates directory.
        """
        if template_dir is None:
            # Default to ./templates/templates directory
            template_dir = Path(__file__).parent / "templates"
            template_dir.mkdir(exist_ok=True)

        self.template_dir = Path(template_dir)
        self._loaded_templates: Dict[str, TestPlanTemplate] = {}

    def load_all(self) -> Dict[str, TestPlanTemplate]:
        """
        Load all templates from YAML files in the template directory.

        Returns:
            Dictionary mapping template names to TestPlanTemplate objects
        """
        # Start with hardcoded templates as fallback
        self._loaded_templates = TEMPLATE_REGISTRY.copy()

        # Load YAML templates
        if self.template_dir.exists():
            for yaml_file in self.template_dir.glob("*.yaml"):
                try:
                    template = self._load_template_from_file(yaml_file)
                    if template:
                        self._loaded_templates[template.name.lower()] = template
                except Exception as e:
                    print(f"Warning: Failed to load template from {yaml_file}: {e}")

        return self._loaded_templates

    def _load_template_from_file(self, file_path: Path) -> Optional[TestPlanTemplate]:
        """Load a single template from a YAML file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "name" not in data:
            return None

        name = data["name"]
        description = data.get("description", "")
        tasks_data = data.get("tasks", [])

        tasks = []
        for task_data in tasks_data:
            description_template = task_data.get("description_template", "")
            test_type_str = task_data.get("test_type", "").upper()
            dependencies = task_data.get("dependencies", [])
            owner = task_data.get("owner")

            try:
                test_type = TestType[test_type_str]
            except KeyError:
                print(f"Warning: Invalid test type '{test_type_str}' in template '{name}'")
                continue

            task_template = TaskTemplate(
                description_template=description_template,
                test_type=test_type,
                dependencies=dependencies,
                owner=owner,
            )
            tasks.append(task_template)

        return TestPlanTemplate(name=name, description=description, tasks=tasks)

    def get_template(self, template_name: str) -> Optional[TestPlanTemplate]:
        """Get a template by name."""
        if not self._loaded_templates:
            self.load_all()
        return self._loaded_templates.get(template_name.lower())

    def list_templates(self) -> List[Dict[str, str]]:
        """List all available templates."""
        if not self._loaded_templates:
            self.load_all()
        return [
            {
                "name": template.name,
                "description": template.description,
                "task_count": len(template.tasks),
            }
            for template in self._loaded_templates.values()
        ]


# Global template loader instance
_global_template_loader: Optional[TemplateLoader] = None


def get_template_loader(template_dir: Optional[Path] = None) -> TemplateLoader:
    """Get or create the global template loader instance."""
    global _global_template_loader
    if _global_template_loader is None:
        _global_template_loader = TemplateLoader(template_dir)
    return _global_template_loader

