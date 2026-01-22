"""
Templates package for test plan creation.

Provides predefined test plan templates and functionality to generate
and customize test plans based on these templates.
"""

from templates.test_plan_templates import (
    BASIC_TEMPLATE,
    COMPLEX_TEMPLATE,
    FULL_COVERAGE_TEMPLATE,
    MINIMAL_TEMPLATE,
    TEMPLATE_REGISTRY,
    TaskTemplate,
    TestPlanTemplate,
    add_task_to_plan,
    customize_plan,
    generate_from_template,
    get_template,
    list_templates,
    remove_task_from_plan,
)

__all__ = [
    'TaskTemplate',
    'TestPlanTemplate',
    'BASIC_TEMPLATE',
    'COMPLEX_TEMPLATE',
    'MINIMAL_TEMPLATE',
    'FULL_COVERAGE_TEMPLATE',
    'TEMPLATE_REGISTRY',
    'list_templates',
    'get_template',
    'generate_from_template',
    'add_task_to_plan',
    'remove_task_from_plan',
    'customize_plan',
]

