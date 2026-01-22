"""
Template-based test plan creation system.

This module provides predefined test plan templates and functionality to
generate and customize test plans based on these templates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


@dataclass
class TaskTemplate:
    """
    Template definition for a single task.
    
    Attributes:
        description_template: Template string for task description (supports {feature}, {goal} placeholders)
        test_type: Type of test
        dependencies: List of dependency task IDs (can reference other template tasks)
        owner: Default owner (optional)
    """
    description_template: str
    test_type: TestType
    dependencies: List[str] = field(default_factory=list)
    owner: Optional[str] = None


@dataclass
class TestPlanTemplate:
    """
    Template definition for a complete test plan.
    
    Attributes:
        name: Template name
        description: Template description
        tasks: List of task templates
    """
    name: str
    description: str
    tasks: List[TaskTemplate]


# ============================================================================
# Predefined Templates
# ============================================================================

BASIC_TEMPLATE = TestPlanTemplate(
    name="basic",
    description="Basic test plan with essential test types (unit, integration, e2e)",
    tasks=[
        TaskTemplate(
            description_template="Write unit tests for {feature} core logic",
            test_type=TestType.UNIT,
            dependencies=[],
        ),
        TaskTemplate(
            description_template="Cover service and API flows for {feature}",
            test_type=TestType.INTEGRATION,
            dependencies=["task-1"],
        ),
        TaskTemplate(
            description_template="Validate user journeys for {feature}: {goal}",
            test_type=TestType.E2E,
            dependencies=["task-2"],
        ),
    ],
)

COMPLEX_TEMPLATE = TestPlanTemplate(
    name="complex",
    description="Complex test plan with comprehensive coverage including security and performance",
    tasks=[
        TaskTemplate(
            description_template="Write unit tests for {feature} core logic",
            test_type=TestType.UNIT,
            dependencies=[],
        ),
        TaskTemplate(
            description_template="Cover service and API flows for {feature}",
            test_type=TestType.INTEGRATION,
            dependencies=["task-1"],
        ),
        TaskTemplate(
            description_template="Validate user journeys for {feature}: {goal}",
            test_type=TestType.E2E,
            dependencies=["task-2"],
        ),
        TaskTemplate(
            description_template="Explore edge cases and negative paths for {feature}",
            test_type=TestType.EXPLORATORY,
            dependencies=["task-1"],
        ),
        TaskTemplate(
            description_template="Security testing for {feature}",
            test_type=TestType.SECURITY,
            dependencies=["task-2"],
        ),
        TaskTemplate(
            description_template="Performance testing for {feature}",
            test_type=TestType.PERFORMANCE,
            dependencies=["task-2"],
        ),
    ],
)

MINIMAL_TEMPLATE = TestPlanTemplate(
    name="minimal",
    description="Minimal test plan with just unit and integration tests",
    tasks=[
        TaskTemplate(
            description_template="Write unit tests for {feature}",
            test_type=TestType.UNIT,
            dependencies=[],
        ),
        TaskTemplate(
            description_template="Integration tests for {feature}",
            test_type=TestType.INTEGRATION,
            dependencies=["task-1"],
        ),
    ],
)

FULL_COVERAGE_TEMPLATE = TestPlanTemplate(
    name="full_coverage",
    description="Full coverage test plan with all test types",
    tasks=[
        TaskTemplate(
            description_template="Unit tests for {feature} core functionality",
            test_type=TestType.UNIT,
            dependencies=[],
        ),
        TaskTemplate(
            description_template="Integration tests for {feature} service layer",
            test_type=TestType.INTEGRATION,
            dependencies=["task-1"],
        ),
        TaskTemplate(
            description_template="End-to-end tests for {feature} user flows: {goal}",
            test_type=TestType.E2E,
            dependencies=["task-2"],
        ),
        TaskTemplate(
            description_template="Exploratory testing for {feature} edge cases",
            test_type=TestType.EXPLORATORY,
            dependencies=["task-1"],
        ),
        TaskTemplate(
            description_template="Security testing for {feature} vulnerabilities",
            test_type=TestType.SECURITY,
            dependencies=["task-2"],
        ),
        TaskTemplate(
            description_template="Performance testing for {feature} load and stress",
            test_type=TestType.PERFORMANCE,
            dependencies=["task-2"],
        ),
    ],
)

# Template registry
TEMPLATE_REGISTRY: Dict[str, TestPlanTemplate] = {
    "basic": BASIC_TEMPLATE,
    "complex": COMPLEX_TEMPLATE,
    "minimal": MINIMAL_TEMPLATE,
    "full_coverage": FULL_COVERAGE_TEMPLATE,
}


# ============================================================================
# Template Functions
# ============================================================================

def list_templates() -> List[Dict[str, str]]:
    """
    List all available test plan templates.
    Includes both YAML-loaded and hardcoded templates.
    
    Returns:
        List of dictionaries with template information:
        [
            {'name': 'basic', 'description': '...'},
            ...
        ]
        
    Example:
        >>> templates = list_templates()
        >>> for template in templates:
        ...     print(template['name'], template['description'])
    """
    # Try template loader first (YAML templates)
    try:
        from templates.template_loader import get_template_loader
        template_loader = get_template_loader()
        yaml_templates = template_loader.list_templates()
        if yaml_templates:
            # Merge with hardcoded templates (YAML takes precedence)
            template_dict = {t['name']: t for t in yaml_templates}
            for template in TEMPLATE_REGISTRY.values():
                if template.name not in template_dict:
                    template_dict[template.name] = {
                        'name': template.name,
                        'description': template.description,
                        'task_count': len(template.tasks),
                    }
            return list(template_dict.values())
    except Exception:
        pass  # Fall back to hardcoded templates

    # Fall back to hardcoded registry
    return [
        {
            'name': template.name,
            'description': template.description,
            'task_count': len(template.tasks),
        }
        for template in TEMPLATE_REGISTRY.values()
    ]


def get_template(template_name: str) -> Optional[TestPlanTemplate]:
    """
    Get a template by name.
    First checks YAML-loaded templates, then falls back to hardcoded registry.
    
    Args:
        template_name: Name of the template
        
    Returns:
        TestPlanTemplate if found, None otherwise
        
    Example:
        >>> template = get_template('basic')
        >>> print(template.name)
        basic
    """
    # Try template loader first (YAML templates)
    try:
        from templates.template_loader import get_template_loader
        template_loader = get_template_loader()
        template = template_loader.get_template(template_name)
        if template:
            return template
    except Exception:
        pass  # Fall back to hardcoded templates

    # Fall back to hardcoded registry
    return TEMPLATE_REGISTRY.get(template_name.lower())


def generate_from_template(
    template_name: str,
    feature: str,
    goal: str,
    task_id_prefix: str = "task",
    owner: Optional[str] = None,
    constraints: Optional[List[str]] = None,
) -> List[TestTask]:
    """
    Generate a test plan from a template.
    
    Args:
        template_name: Name of the template to use
        feature: Feature name to substitute in descriptions
        goal: Goal to substitute in descriptions
        task_id_prefix: Prefix for task IDs (default: "task")
        owner: Default owner for all tasks (optional)
        constraints: Optional list of constraints to append to descriptions
        
    Returns:
        List of TestTask objects
        
    Raises:
        ValueError: If template not found
        
    Example:
        >>> tasks = generate_from_template(
        ...     'basic',
        ...     feature='Checkout',
        ...     goal='Ensure reliable payment processing'
        ... )
        >>> print(f"Generated {len(tasks)} tasks")
    """
    template = get_template(template_name)
    if not template:
        available = ', '.join(TEMPLATE_REGISTRY.keys())
        raise ValueError(
            f"Template '{template_name}' not found. Available templates: {available}"
        )
    
    # Prepare substitution context
    context = {
        'feature': feature,
        'goal': goal,
    }
    
    # Build constraints suffix if provided
    constraints_suffix = ""
    if constraints:
        constraints_suffix = f" (constraints: {', '.join(constraints)})"
    
    tasks = []
    task_id_map: Dict[str, str] = {}  # Map template task IDs to actual task IDs
    
    # First pass: create task IDs
    for idx, task_template in enumerate(template.tasks, start=1):
        actual_id = f"{task_id_prefix}-{idx}"
        # Map template dependencies (e.g., "task-1") to actual IDs
        template_id = f"{task_id_prefix}-{idx}"
        task_id_map[f"task-{idx}"] = actual_id
    
    # Second pass: create tasks with resolved dependencies
    for idx, task_template in enumerate(template.tasks, start=1):
        actual_id = f"{task_id_prefix}-{idx}"
        
        # Format description
        description = task_template.description_template.format(**context)
        if constraints_suffix:
            description += constraints_suffix
        
        # Resolve dependencies
        resolved_dependencies = []
        for dep in task_template.dependencies:
            if dep in task_id_map:
                resolved_dependencies.append(task_id_map[dep])
            else:
                # Try direct mapping if it's already in the format we use
                resolved_dependencies.append(dep)
        
        # Create task
        task = TestTask(
            id=actual_id,
            description=description,
            test_type=task_template.test_type,
            dependencies=resolved_dependencies,
            status=TaskStatus.PENDING,
            owner=owner or task_template.owner,
            coverage_status=CoverageStatus.NOT_STARTED,
        )
        tasks.append(task)
    
    return tasks


def add_task_to_plan(
    plan: List[TestTask],
    description: str,
    test_type: TestType,
    dependencies: Optional[List[str]] = None,
    owner: Optional[str] = None,
    task_id: Optional[str] = None,
) -> TestTask:
    """
    Add a new task to an existing test plan.
    
    Args:
        plan: Existing list of TestTask objects
        description: Description of the new task
        test_type: Type of test
        dependencies: List of task IDs this task depends on
        owner: Owner of the task (optional)
        task_id: Custom task ID (auto-generated if not provided)
        
    Returns:
        The newly created TestTask
        
    Example:
        >>> plan = generate_from_template('basic', 'Checkout', 'Test payment')
        >>> new_task = add_task_to_plan(
        ...     plan,
        ...     description='Additional security tests',
        ...     test_type=TestType.SECURITY,
        ...     dependencies=[plan[0].id]
        ... )
    """
    # Generate task ID if not provided
    if not task_id:
        existing_ids = {task.id for task in plan}
        counter = len(plan) + 1
        task_id = f"task-{counter}"
        while task_id in existing_ids:
            counter += 1
            task_id = f"task-{counter}"
    
    # Create new task
    new_task = TestTask(
        id=task_id,
        description=description,
        test_type=test_type,
        dependencies=dependencies or [],
        status=TaskStatus.PENDING,
        owner=owner,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    
    plan.append(new_task)
    return new_task


def remove_task_from_plan(plan: List[TestTask], task_id: str) -> bool:
    """
    Remove a task from a test plan.
    
    Also removes the task from other tasks' dependencies.
    
    Args:
        plan: List of TestTask objects
        task_id: ID of the task to remove
        
    Returns:
        True if task was removed, False if not found
        
    Example:
        >>> plan = generate_from_template('basic', 'Checkout', 'Test payment')
        >>> removed = remove_task_from_plan(plan, 'task-1')
        >>> print(f"Task removed: {removed}")
    """
    # Find the task index
    task_index = None
    for idx, task in enumerate(plan):
        if task.id == task_id:
            task_index = idx
            break
    
    if task_index is None:
        return False
    
    # Remove from plan by index
    plan.pop(task_index)
    
    # Remove from other tasks' dependencies
    for task in plan:
        if task_id in task.dependencies:
            task.dependencies.remove(task_id)
    
    return True


def customize_plan(
    plan: List[TestTask],
    add_tasks: Optional[List[Dict[str, Any]]] = None,
    remove_task_ids: Optional[List[str]] = None,
    update_tasks: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[TestTask]:
    """
    Customize a test plan by adding, removing, or updating tasks.
    
    Args:
        plan: List of TestTask objects to customize
        add_tasks: List of task dictionaries to add:
            [{'description': '...', 'test_type': TestType.UNIT, ...}, ...]
        remove_task_ids: List of task IDs to remove
        update_tasks: Dictionary mapping task IDs to updates:
            {'task-1': {'description': 'Updated description', 'owner': 'new_owner'}, ...}
        
    Returns:
        Updated list of TestTask objects
        
    Example:
        >>> plan = generate_from_template('basic', 'Checkout', 'Test payment')
        >>> customized = customize_plan(
        ...     plan,
        ...     add_tasks=[{
        ...         'description': 'Security tests',
        ...         'test_type': TestType.SECURITY
        ...     }],
        ...     remove_task_ids=['task-3'],
        ...     update_tasks={'task-1': {'owner': 'john.doe'}}
        ... )
    """
    # Create a copy of the plan to avoid modifying the original
    customized_plan = [TestTask(
        id=task.id,
        description=task.description,
        test_type=task.test_type,
        dependencies=list(task.dependencies),
        status=task.status,
        owner=task.owner,
        coverage_status=task.coverage_status,
    ) for task in plan]
    
    # Remove tasks
    if remove_task_ids:
        for task_id in remove_task_ids:
            remove_task_from_plan(customized_plan, task_id)
    
    # Update tasks
    if update_tasks:
        for task_id, updates in update_tasks.items():
            task = next((t for t in customized_plan if t.id == task_id), None)
            if task:
                if 'description' in updates:
                    task.description = updates['description']
                if 'test_type' in updates:
                    task.test_type = TestType(updates['test_type']) if isinstance(updates['test_type'], str) else updates['test_type']
                if 'owner' in updates:
                    task.owner = updates['owner']
                if 'status' in updates:
                    task.status = TaskStatus(updates['status']) if isinstance(updates['status'], str) else updates['status']
                if 'coverage_status' in updates:
                    task.coverage_status = CoverageStatus(updates['coverage_status']) if isinstance(updates['coverage_status'], str) else updates['coverage_status']
                if 'dependencies' in updates:
                    task.dependencies = updates['dependencies']
    
    # Add tasks
    if add_tasks:
        for task_data in add_tasks:
            add_task_to_plan(
                customized_plan,
                description=task_data.get('description', ''),
                test_type=TestType(task_data['test_type']) if isinstance(task_data.get('test_type'), str) else task_data.get('test_type', TestType.UNIT),
                dependencies=task_data.get('dependencies', []),
                owner=task_data.get('owner'),
                task_id=task_data.get('id'),
            )
    
    return customized_plan


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

