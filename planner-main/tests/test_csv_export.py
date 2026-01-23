"""
Unit tests for CSV export functionality.
"""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

import pytest

from export.csv_export import export_to_csv, export_to_csv_simple
from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


def test_export_to_csv_simple():
    """Test simple CSV export with minimal columns."""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_csv_simple(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check headers
            assert rows[0] == ['Task ID', 'Description', 'Owner', 'Coverage Status']
            
            # Check data rows
            assert rows[1] == ['task-1', 'Write unit tests', 'john.doe', 'not_started']
            assert rows[2] == ['task-2', 'Integration tests', 'jane.smith', 'in_progress']
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_csv_with_testtask_objects():
    """Test CSV export with TestTask objects."""
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
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_csv(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check headers
            assert rows[0] == [
                'Task ID',
                'Description',
                'Owner',
                'Coverage Status',
                'Status',
                'Test Type',
                'Dependencies',
            ]
            
            # Check first data row
            assert rows[1][0] == 'task-1'
            assert rows[1][1] == 'Write unit tests'
            assert rows[1][2] == 'john.doe'
            assert rows[1][3] == 'not_started'
            assert rows[1][4] == 'pending'
            assert rows[1][5] == 'unit'
            assert rows[1][6] == ''
            
            # Check second data row
            assert rows[2][0] == 'task-2'
            assert rows[2][1] == 'Integration tests'
            assert rows[2][2] == 'jane.smith'
            assert rows[2][3] == 'in_progress'
            assert rows[2][4] == 'in_progress'
            assert rows[2][5] == 'integration'
            assert rows[2][6] == 'task-1'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_csv_with_dicts():
    """Test CSV export with dictionary objects."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
            'status': 'pending',
            'test_type': 'unit',
            'dependencies': '',
        },
        {
            'id': 'task-2',
            'description': 'Integration tests',
            'owner': 'jane.smith',
            'coverage_status': 'in_progress',
            'status': 'in_progress',
            'test_type': 'integration',
            'dependencies': 'task-1',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_csv(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check headers
            assert len(rows) == 3  # Header + 2 data rows
            assert rows[0][0] == 'Task ID'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_csv_custom_columns():
    """Test CSV export with custom column selection."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
            'status': 'pending',
            'test_type': 'unit',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        custom_columns = ['Task ID', 'Description', 'Owner']
        export_to_csv(test_plan, output_path, columns=custom_columns)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Check headers
            assert rows[0] == custom_columns
            
            # Check data row has only 3 columns
            assert len(rows[1]) == 3
            assert rows[1][0] == 'task-1'
            assert rows[1][1] == 'Write unit tests'
            assert rows[1][2] == 'john.doe'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_csv_no_headers():
    """Test CSV export without headers."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': 'john.doe',
            'coverage_status': 'not_started',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_csv(test_plan, output_path, include_headers=False)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should only have data rows, no headers
            assert len(rows) == 1
            assert rows[0][0] == 'task-1'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_csv_empty_plan():
    """Test CSV export with empty test plan."""
    test_plan = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_csv(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # Should only have headers
            assert len(rows) == 1
            assert rows[0][0] == 'Task ID'
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()


def test_export_to_csv_none_values():
    """Test CSV export handles None values correctly."""
    test_plan = [
        {
            'id': 'task-1',
            'description': 'Write unit tests',
            'owner': None,  # None owner
            'coverage_status': 'not_started',
            'status': 'pending',
            'test_type': 'unit',
            'dependencies': '',
        },
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        output_path = Path(tmp.name)
    
    try:
        export_to_csv(test_plan, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Read and verify CSV content
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            # None should be converted to empty string
            assert rows[1][2] == ''  # Owner column
    finally:
        # Cleanup
        if output_path.exists():
            output_path.unlink()

