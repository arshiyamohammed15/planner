"""
Unit tests for template-based test plan creation.
"""

from __future__ import annotations

import pytest

from templates.test_plan_templates import (
    BASIC_TEMPLATE,
    COMPLEX_TEMPLATE,
    MINIMAL_TEMPLATE,
    add_task_to_plan,
    customize_plan,
    generate_from_template,
    get_template,
    list_templates,
    remove_task_from_plan,
)
from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


def test_list_templates():
    """Test listing all available templates."""
    templates = list_templates()
    
    assert len(templates) >= 4  # At least basic, complex, minimal, full_coverage
    template_names = [t['name'] for t in templates]
    assert 'basic' in template_names
    assert 'complex' in template_names
    assert 'minimal' in template_names
    
    # Check structure
    for template in templates:
        assert 'name' in template
        assert 'description' in template
        assert 'task_count' in template


def test_get_template():
    """Test getting a template by name."""
    template = get_template('basic')
    assert template is not None
    assert template.name == 'basic'
    assert len(template.tasks) > 0
    
    # Test case-insensitive
    template2 = get_template('BASIC')
    assert template2 is not None
    assert template2.name == 'basic'
    
    # Test non-existent template
    template3 = get_template('nonexistent')
    assert template3 is None


def test_generate_from_template_basic():
    """Test generating a test plan from the basic template."""
    tasks = generate_from_template(
        template_name='basic',
        feature='Checkout',
        goal='Ensure reliable payment processing'
    )
    
    assert len(tasks) == 3
    assert tasks[0].id == 'task-1'
    assert tasks[0].test_type == TestType.UNIT
    assert 'Checkout' in tasks[0].description
    assert tasks[0].dependencies == []
    
    assert tasks[1].id == 'task-2'
    assert tasks[1].test_type == TestType.INTEGRATION
    assert tasks[1].dependencies == ['task-1']
    
    assert tasks[2].id == 'task-3'
    assert tasks[2].test_type == TestType.E2E
    assert 'Ensure reliable payment processing' in tasks[2].description
    assert tasks[2].dependencies == ['task-2']


def test_generate_from_template_complex():
    """Test generating a test plan from the complex template."""
    tasks = generate_from_template(
        template_name='complex',
        feature='Authentication',
        goal='Secure user login'
    )
    
    assert len(tasks) >= 6
    test_types = [task.test_type for task in tasks]
    assert TestType.UNIT in test_types
    assert TestType.INTEGRATION in test_types
    assert TestType.E2E in test_types
    assert TestType.EXPLORATORY in test_types
    assert TestType.SECURITY in test_types
    assert TestType.PERFORMANCE in test_types


def test_generate_from_template_minimal():
    """Test generating a test plan from the minimal template."""
    tasks = generate_from_template(
        template_name='minimal',
        feature='API',
        goal='Test endpoints'
    )
    
    assert len(tasks) == 2
    assert tasks[0].test_type == TestType.UNIT
    assert tasks[1].test_type == TestType.INTEGRATION


def test_generate_from_template_with_owner():
    """Test generating a test plan with default owner."""
    tasks = generate_from_template(
        template_name='basic',
        feature='Checkout',
        goal='Test payment',
        owner='john.doe'
    )
    
    assert all(task.owner == 'john.doe' for task in tasks)


def test_generate_from_template_with_constraints():
    """Test generating a test plan with constraints."""
    tasks = generate_from_template(
        template_name='basic',
        feature='Checkout',
        goal='Test payment',
        constraints=['PCI compliance', 'limited staging data']
    )
    
    # Check that constraints are appended to descriptions
    assert any('PCI compliance' in task.description for task in tasks)
    assert any('limited staging data' in task.description for task in tasks)


def test_generate_from_template_custom_prefix():
    """Test generating a test plan with custom task ID prefix."""
    tasks = generate_from_template(
        template_name='basic',
        feature='Checkout',
        goal='Test payment',
        task_id_prefix='checkout'
    )
    
    assert tasks[0].id == 'checkout-1'
    assert tasks[1].id == 'checkout-2'
    assert tasks[2].id == 'checkout-3'
    
    # Check dependencies are updated
    assert tasks[1].dependencies == ['checkout-1']
    assert tasks[2].dependencies == ['checkout-2']


def test_generate_from_template_nonexistent():
    """Test generating from a non-existent template."""
    with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
        generate_from_template(
            template_name='nonexistent',
            feature='Test',
            goal='Test goal'
        )


def test_add_task_to_plan():
    """Test adding a task to an existing plan."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    original_count = len(plan)
    
    new_task = add_task_to_plan(
        plan,
        description='Security testing for Checkout',
        test_type=TestType.SECURITY,
        dependencies=[plan[0].id],
        owner='security.team'
    )
    
    assert len(plan) == original_count + 1
    assert new_task.id == f'task-{original_count + 1}'
    assert new_task.description == 'Security testing for Checkout'
    assert new_task.test_type == TestType.SECURITY
    assert new_task.dependencies == [plan[0].id]
    assert new_task.owner == 'security.team'


def test_add_task_to_plan_custom_id():
    """Test adding a task with a custom ID."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    
    new_task = add_task_to_plan(
        plan,
        description='Custom task',
        test_type=TestType.UNIT,
        task_id='custom-task-1'
    )
    
    assert new_task.id == 'custom-task-1'
    assert len(plan) == 4


def test_remove_task_from_plan():
    """Test removing a task from a plan."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    original_count = len(plan)
    task_to_remove_id = plan[1].id
    
    # Verify task has dependencies
    assert task_to_remove_id in plan[2].dependencies
    
    removed = remove_task_from_plan(plan, task_to_remove_id)
    
    assert removed is True
    assert len(plan) == original_count - 1
    assert not any(task.id == task_to_remove_id for task in plan)
    
    # Verify dependencies were updated
    assert task_to_remove_id not in plan[1].dependencies  # Was plan[2], now plan[1]


def test_remove_task_from_plan_nonexistent():
    """Test removing a non-existent task."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    original_count = len(plan)
    
    removed = remove_task_from_plan(plan, 'nonexistent-task')
    
    assert removed is False
    assert len(plan) == original_count


def test_customize_plan_add_tasks():
    """Test customizing a plan by adding tasks."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    
    customized = customize_plan(
        plan,
        add_tasks=[
            {
                'description': 'Security tests',
                'test_type': TestType.SECURITY,
                'dependencies': [plan[0].id],
            },
            {
                'description': 'Performance tests',
                'test_type': TestType.PERFORMANCE,
            },
        ]
    )
    
    assert len(customized) == len(plan) + 2
    assert any(task.test_type == TestType.SECURITY for task in customized)
    assert any(task.test_type == TestType.PERFORMANCE for task in customized)


def test_customize_plan_remove_tasks():
    """Test customizing a plan by removing tasks."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    
    customized = customize_plan(
        plan,
        remove_task_ids=['task-2']
    )
    
    assert len(customized) == len(plan) - 1
    assert not any(task.id == 'task-2' for task in customized)
    
    # Verify dependencies were updated
    remaining_task = next((t for t in customized if t.id == 'task-3'), None)
    if remaining_task:
        assert 'task-2' not in remaining_task.dependencies


def test_customize_plan_update_tasks():
    """Test customizing a plan by updating tasks."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    
    customized = customize_plan(
        plan,
        update_tasks={
            'task-1': {
                'description': 'Updated unit tests',
                'owner': 'john.doe',
            },
            'task-2': {
                'status': 'in_progress',
                'coverage_status': 'in_progress',
            },
        }
    )
    
    # Find updated tasks
    task1 = next((t for t in customized if t.id == 'task-1'), None)
    task2 = next((t for t in customized if t.id == 'task-2'), None)
    
    assert task1 is not None
    assert task1.description == 'Updated unit tests'
    assert task1.owner == 'john.doe'
    
    assert task2 is not None
    assert task2.status == TaskStatus.IN_PROGRESS
    assert task2.coverage_status == CoverageStatus.IN_PROGRESS


def test_customize_plan_combined():
    """Test customizing a plan with add, remove, and update operations."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    
    customized = customize_plan(
        plan,
        add_tasks=[
            {
                'description': 'Security tests',
                'test_type': TestType.SECURITY,
            },
        ],
        remove_task_ids=['task-3'],
        update_tasks={
            'task-1': {
                'owner': 'john.doe',
            },
        }
    )
    
    # Should have: original 3 - 1 removed + 1 added = 3 tasks
    assert len(customized) == 3
    
    # Verify the original task-3 (E2E test) was removed
    # Note: A new task might get ID task-3, but it should be the Security task, not the original E2E task
    original_task3_description = next((t.description for t in plan if t.id == 'task-3'), None)
    if original_task3_description:
        # Check that the original task-3 description is not in customized
        assert not any(
            task.description == original_task3_description and task.test_type == TestType.E2E
            for task in customized
        )
    
    # Verify task-1 was updated
    task1 = next((t for t in customized if t.id == 'task-1'), None)
    assert task1 is not None
    assert task1.owner == 'john.doe'
    
    # Verify new task was added
    assert any(task.test_type == TestType.SECURITY for task in customized)


def test_generate_from_template_placeholders():
    """Test that template placeholders are correctly substituted."""
    tasks = generate_from_template(
        template_name='basic',
        feature='User Authentication',
        goal='Ensure secure login'
    )
    
    # Check that feature and goal are in descriptions
    assert any('User Authentication' in task.description for task in tasks)
    assert any('Ensure secure login' in task.description for task in tasks)


def test_template_dependencies_resolution():
    """Test that template dependencies are correctly resolved."""
    tasks = generate_from_template(
        template_name='basic',
        feature='Checkout',
        goal='Test payment',
        task_id_prefix='checkout'
    )
    
    # Verify dependencies are resolved to actual task IDs
    assert tasks[1].dependencies == ['checkout-1']
    assert tasks[2].dependencies == ['checkout-2']


def test_customize_plan_preserves_original():
    """Test that customize_plan doesn't modify the original plan."""
    plan = generate_from_template('basic', 'Checkout', 'Test payment')
    original_length = len(plan)
    original_task_ids = [task.id for task in plan]
    
    customized = customize_plan(
        plan,
        add_tasks=[{'description': 'New task', 'test_type': TestType.UNIT}],
        remove_task_ids=['task-1'],
    )
    
    # Original plan should be unchanged
    assert len(plan) == original_length
    assert [task.id for task in plan] == original_task_ids
    
    # Customized plan should be different
    assert len(customized) == original_length  # -1 removed +1 added = same length
    assert not any(task.id == 'task-1' for task in customized)
    assert any(task.description == 'New task' for task in customized)

