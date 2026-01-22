"""
Import functionality for test plans from external sources.

This module provides functions to import test plan data from various formats
(CSV, JSON) and external tools (TestRail, Jira), allowing for smooth integration
with other systems.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


class ImportValidationError(Exception):
    """Raised when imported data fails validation."""
    pass


def _validate_task_data(task_dict: Dict[str, Any]) -> None:
    """
    Validate imported task data.
    
    Args:
        task_dict: Dictionary containing task data
        
    Raises:
        ImportValidationError: If validation fails
    """
    # Required fields
    if 'id' not in task_dict or not task_dict['id']:
        raise ImportValidationError("Task 'id' is required and cannot be empty")
    
    if 'description' not in task_dict or not task_dict['description']:
        raise ImportValidationError("Task 'description' is required and cannot be empty")
    
    # Validate test_type if provided
    if 'test_type' in task_dict and task_dict['test_type']:
        test_type = task_dict['test_type']
        try:
            TestType(test_type.lower())
        except ValueError:
            valid_types = ', '.join(TestType.choices())
            raise ImportValidationError(
                f"Invalid test_type '{test_type}'. Allowed: {valid_types}"
            )
    
    # Validate status if provided
    if 'status' in task_dict and task_dict['status']:
        status = task_dict['status']
        try:
            TaskStatus(status.lower())
        except ValueError:
            valid_statuses = ', '.join([s.value for s in TaskStatus])
            raise ImportValidationError(
                f"Invalid status '{status}'. Allowed: {valid_statuses}"
            )
    
    # Validate coverage_status if provided
    if 'coverage_status' in task_dict and task_dict['coverage_status']:
        coverage_status = task_dict['coverage_status']
        try:
            CoverageStatus(coverage_status.lower())
        except ValueError:
            valid_statuses = ', '.join([s.value for s in CoverageStatus])
            raise ImportValidationError(
                f"Invalid coverage_status '{coverage_status}'. Allowed: {valid_statuses}"
            )


def _normalize_task_data(task_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize imported task data to match TestTask model structure.
    
    Args:
        task_dict: Dictionary containing task data
        
    Returns:
        Normalized dictionary with proper field names and types
    """
    normalized = {
        'id': str(task_dict.get('id', '')).strip(),
        'description': str(task_dict.get('description', '')).strip(),
    }
    
    # Normalize test_type
    if 'test_type' in task_dict and task_dict['test_type']:
        normalized['test_type'] = str(task_dict['test_type']).lower().strip()
    else:
        normalized['test_type'] = TestType.UNIT.value  # Default
    
    # Normalize status
    if 'status' in task_dict and task_dict['status']:
        normalized['status'] = str(task_dict['status']).lower().strip()
    else:
        normalized['status'] = TaskStatus.PENDING.value  # Default
    
    # Normalize owner (optional)
    if 'owner' in task_dict:
        owner = task_dict['owner']
        normalized['owner'] = str(owner).strip() if owner else None
    else:
        normalized['owner'] = None
    
    # Normalize coverage_status
    if 'coverage_status' in task_dict and task_dict['coverage_status']:
        normalized['coverage_status'] = str(task_dict['coverage_status']).lower().strip()
    else:
        normalized['coverage_status'] = CoverageStatus.NOT_STARTED.value  # Default
    
    # Normalize dependencies
    if 'dependencies' in task_dict:
        deps = task_dict['dependencies']
        if isinstance(deps, str):
            # Handle comma-separated string
            normalized['dependencies'] = [
                d.strip() for d in deps.split(',') if d.strip()
            ]
        elif isinstance(deps, list):
            normalized['dependencies'] = [str(d).strip() for d in deps if str(d).strip()]
        else:
            normalized['dependencies'] = []
    else:
        normalized['dependencies'] = []
    
    return normalized


def _create_test_task(task_dict: Dict[str, Any]) -> TestTask:
    """
    Create a TestTask object from normalized task data.
    
    Args:
        task_dict: Normalized dictionary containing task data
        
    Returns:
        TestTask object
    """
    return TestTask(
        id=task_dict['id'],
        description=task_dict['description'],
        test_type=task_dict['test_type'],
        status=task_dict['status'],
        owner=task_dict.get('owner'),
        coverage_status=task_dict['coverage_status'],
        dependencies=task_dict['dependencies'],
    )


def import_from_csv(file_path: Union[str, Path]) -> List[TestTask]:
    """
    Import test plans from CSV file.
    
    This function reads a CSV file and parses it into TestTask objects.
    The CSV should have a header row with columns: Task ID, Description, Owner, Coverage Status.
    Additional columns (Status, Test Type, Dependencies) are optional.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of TestTask objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ImportValidationError: If data validation fails
        ValueError: If CSV format is invalid
        
    Example:
        >>> tasks = import_from_csv('test_plan.csv')
        >>> print(f"Imported {len(tasks)} tasks")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    tasks = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        # Check if required columns exist
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row")
        
        # Normalize column names (case-insensitive, handle spaces)
        # Order matters - check more specific patterns first
        field_mapping = {}
        for field in reader.fieldnames:
            field_lower = field.lower().strip()
            # Map common variations (check more specific patterns first)
            if field_lower in ['task id', 'task_id', 'id', 'taskid']:
                field_mapping[field] = 'id'
            elif field_lower in ['description', 'desc', 'task description']:
                field_mapping[field] = 'description'
            elif field_lower in ['owner', 'assignee', 'assigned_to', 'assigned to']:
                field_mapping[field] = 'owner'
            elif field_lower in ['coverage status', 'coverage_status']:
                field_mapping[field] = 'coverage_status'
            elif field_lower in ['task status', 'task_status', 'state']:
                field_mapping[field] = 'status'
            elif field_lower in ['status'] and 'coverage' not in field_lower:
                # Only map 'status' to 'status' if it's not a coverage status
                # Check if 'coverage status' column already exists
                if not any('coverage' in f.lower() for f in reader.fieldnames if f != field):
                    field_mapping[field] = 'status'
                else:
                    # If coverage status exists, this status is likely task status
                    field_mapping[field] = 'status'
            elif field_lower in ['coverage']:
                field_mapping[field] = 'coverage_status'
            elif field_lower in ['test type', 'test_type', 'type']:
                field_mapping[field] = 'test_type'
            elif field_lower in ['dependencies', 'deps', 'depends on', 'depends_on']:
                field_mapping[field] = 'dependencies'
            else:
                # Keep original field name if not recognized
                field_mapping[field] = field_lower.replace(' ', '_')
        
        # Read and process rows
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
            try:
                # Map row data using field mapping
                task_dict = {}
                for csv_field, mapped_field in field_mapping.items():
                    if csv_field in row:
                        task_dict[mapped_field] = row[csv_field]
                
                # Validate and normalize
                _validate_task_data(task_dict)
                normalized = _normalize_task_data(task_dict)
                
                # Create TestTask object
                task = _create_test_task(normalized)
                tasks.append(task)
                
            except ImportValidationError as e:
                raise ImportValidationError(
                    f"Validation error in CSV row {row_num}: {e}"
                ) from e
            except Exception as e:
                raise ValueError(
                    f"Error processing CSV row {row_num}: {e}"
                ) from e
    
    return tasks


def import_from_csv_simple(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Simple CSV import function matching the microtask example.
    
    This function returns a list of dictionaries instead of TestTask objects.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        List of task dictionaries
        
    Example:
        >>> tasks = import_from_csv_simple('test_plan.csv')
        >>> for task in tasks:
        ...     print(task['id'], task['description'])
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    tasks = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip header
        
        for row in reader:
            if len(row) < 4:
                continue  # Skip incomplete rows
            
            task = {
                'id': row[0].strip(),
                'description': row[1].strip(),
                'owner': row[2].strip() if len(row) > 2 and row[2] else None,
                'coverage_status': row[3].strip() if len(row) > 3 and row[3] else 'not_started',
            }
            tasks.append(task)
    
    return tasks


def import_from_json(file_path: Union[str, Path]) -> List[TestTask]:
    """
    Import test plans from JSON file.
    
    This function reads a JSON file and parses it into TestTask objects.
    The JSON can be either:
    - A list of task objects: [{"id": "...", "description": "...", ...}, ...]
    - An object with a "test_plan" key: {"test_plan": [...], ...}
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of TestTask objects
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ImportValidationError: If data validation fails
        json.JSONDecodeError: If JSON is invalid
        
    Example:
        >>> tasks = import_from_json('test_plan.json')
        >>> print(f"Imported {len(tasks)} tasks")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Handle different JSON structures
    if isinstance(data, list):
        tasks_data = data
    elif isinstance(data, dict) and 'test_plan' in data:
        tasks_data = data['test_plan']
    elif isinstance(data, dict) and 'tasks' in data:
        tasks_data = data['tasks']
    else:
        raise ValueError(
            "JSON must be a list of tasks or an object with 'test_plan' or 'tasks' key"
        )
    
    tasks = []
    
    for idx, task_dict in enumerate(tasks_data, start=1):
        if not isinstance(task_dict, dict):
            raise ImportValidationError(
                f"Task at index {idx} must be a dictionary"
            )
        
        try:
            # Validate and normalize
            _validate_task_data(task_dict)
            normalized = _normalize_task_data(task_dict)
            
            # Create TestTask object
            task = _create_test_task(normalized)
            tasks.append(task)
            
        except ImportValidationError as e:
            raise ImportValidationError(
                f"Validation error in JSON task {idx}: {e}"
            ) from e
        except Exception as e:
            raise ValueError(
                f"Error processing JSON task {idx}: {e}"
            ) from e
    
    return tasks


def import_to_database(
    tasks: List[TestTask],
    dal: Any,  # TestTaskDAL type
    skip_existing: bool = True,
) -> Dict[str, Any]:
    """
    Import tasks into the database.
    
    Args:
        tasks: List of TestTask objects to import
        dal: TestTaskDAL instance
        skip_existing: If True, skip tasks that already exist (default: True)
        
    Returns:
        Dictionary with import results:
        {
            'imported': int,
            'skipped': int,
            'failed': int,
            'errors': List[str]
        }
        
    Example:
        >>> from database.data_access_layer import TestTaskDAL
        >>> from database.postgresql_setup import get_sessionmaker
        >>> 
        >>> sessionmaker = get_sessionmaker()
        >>> session = sessionmaker()
        >>> dal = TestTaskDAL(session)
        >>> 
        >>> tasks = import_from_csv('test_plan.csv')
        >>> result = import_to_database(tasks, dal)
        >>> print(f"Imported {result['imported']} tasks")
    """
    result = {
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'errors': [],
    }
    
    for task in tasks:
        try:
            # Check if task already exists
            if skip_existing:
                existing = dal.get_task(task.id)
                if existing:
                    result['skipped'] += 1
                    continue
            
            # Create task in database
            dal.create_task(
                id=task.id,
                description=task.description,
                test_type=task.test_type,
                status=task.status,
                owner=task.owner,
                coverage_status=task.coverage_status,
                dependencies=task.dependencies,
            )
            dal.session.commit()
            result['imported'] += 1
            
        except Exception as e:
            result['failed'] += 1
            result['errors'].append(f"Task {task.id}: {str(e)}")
            dal.session.rollback()
    
    return result


__all__ = [
    'import_from_csv',
    'import_from_csv_simple',
    'import_from_json',
    'import_to_database',
    'ImportValidationError',
]

