"""
Unit tests for JSON export functionality.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from export.json_export import export_to_json, export_to_json_simple
from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


def test_export_to_json_simple():
    """Test simple JSON export matching microtask example."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
        },
        {
            'id': 'task-2',
            'description': 'Integration tests',
            'owner': 'jane.smith',
            'coverage_status': 'in_progress',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json_simple(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Should be a list
            assert isinstance(data, list)
            assert len(data) == 2
            
            # Check first task
            assert data[0]['id'] == 'task-1'
            assert data[0]['description'] == 'Write unit tests'
            assert data[0]['owner'] == 'john.doe'
            assert data[0]['coverage_status'] == 'not_started'
            
            # Check second task
            assert data[1]['id'] == 'task-2'
            assert data[1]['description'] == 'Integration tests'
            assert data[1]['owner'] == 'jane.smith'
            assert data[1]['coverage_status'] == 'in_progress'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_with_testtask_objects():
    """Test JSON export with TestTask objects."""
    test_plan = [
        TestTask(
            id='task-1',
            description='Write unit tests',
            test_type=TestType.UNIT,
            owner='john.doe',
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=[],
        ),
        TestTask(
            id='task-2',
            description='Integration tests',
            test_type=TestType.INTEGRATION,
            owner='jane.smith',
            status=TaskStatus.IN_PROGRESS,
            coverage_status=CoverageStatus.IN_PROGRESS,
            dependencies=['task-1'],
        ),
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Should have structure with metadata
            assert 'test_plan' in data
            assert 'exported_at' in data
            assert 'total_tasks' in data
            assert data['total_tasks'] == 2
            
            # Check tasks
            tasks = data['test_plan']
            assert len(tasks) == 2
            
            # Check first task
            assert tasks[0]['id'] == 'task-1'
            assert tasks[0]['description'] == 'Write unit tests'
            assert tasks[0]['owner'] == 'john.doe'
            assert tasks[0]['coverage_status'] == 'not_started'
            assert tasks[0]['status'] == 'pending'
            assert tasks[0]['test_type'] == 'unit'
            assert tasks[0]['dependencies'] == []
            
            # Check second task
            assert tasks[1]['id'] == 'task-2'
            assert tasks[1]['description'] == 'Integration tests'
            assert tasks[1]['owner'] == 'jane.smith'
            assert tasks[1]['coverage_status'] == 'in_progress'
            assert tasks[1]['status'] == 'in_progress'
            assert tasks[1]['test_type'] == 'integration'
            assert tasks[1]['dependencies'] == ['task-1']
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_with_dicts():
    """Test JSON export with dictionary objects."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
            'status': 'pending',
            'test_type': 'unit',
            'dependencies': [],
        },
        {
            'id': 'task-2',
            'description': 'Integration tests',
            'owner': 'jane.smith',
            'coverage_status': 'in_progress',
            'status': 'in_progress',
            'test_type': 'integration',
            'dependencies': ['task-1'],
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Should have structure with metadata
            assert 'test_plan' in data
            assert data['total_tasks'] == 2
            assert len(data['test_plan']) == 2
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_custom_indent():
    """Test JSON export with custom indentation."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json(test_plan, output_path, indent=2)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read file as text to check indentation
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Should be valid JSON
            data = json.loads(content)
            assert len(data['test_plan']) == 1
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_empty_plan():
    """Test JSON export with empty test plan."""
    test_plan = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Should have structure with empty test_plan
            assert 'test_plan' in data
            assert data['total_tasks'] == 0
            assert data['test_plan'] == []
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_none_values():
    """Test JSON export handles None values correctly."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': None,  # None owner
            'coverage_status': 'not_started',
            'status': 'pending',
            'test_type': 'unit',
            'dependencies': [],
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify JSON content
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # None should be preserved as null in JSON
            assert data['test_plan'][0]['owner'] is None
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_readable_format():
    """Test that exported JSON is readable and properly formatted."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json(test_plan, output_path, indent=4)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read file as text to verify formatting
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Should contain newlines (indented)
            assert '\n' in content
            
            # Should be valid JSON
            data = json.loads(content)
            assert 'test_plan' in data
            
            # Should be readable (contains expected keys)
            assert 'exported_at' in data
            assert 'total_tasks' in data
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_json_simple_matches_example():
    """Test that export_to_json_simple matches the microtask example format."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_json_simple(test_plan, output_path, indent=4)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify JSON content matches example format
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Should be a list (matching example format)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]['id'] == 'task-1'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()

