"""
JSON Export functionality for test plans.

This module provides functions to export test plan data to JSON format,
making it easy to exchange data and integrate with other systems.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from database.models import TestTaskModel
from tasks.test_task_model import TestTask


def _extract_task_data(task: Union[TestTask, TestTaskModel, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract task data from various input types for JSON serialization.
    
    Args:
        task: Task object (TestTask, TestTaskModel) or dictionary
        
    Returns:
        Dictionary with task data suitable for JSON serialization
    """
    if isinstance(task, dict):
        # Ensure all values are JSON-serializable
        result = {}
        for key, value in task.items():
            if value is None:
                result[key] = None
            elif isinstance(value, (str, int, float, bool)):
                result[key] = value
            elif isinstance(value, (list, tuple)):
                result[key] = list(value)
            else:
                result[key] = str(value)
        return result
    
    # Handle TestTask dataclass
    if isinstance(task, TestTask):
        return {
            'id': task.id,
            'description': task.description,
            'owner': task.owner,
            'coverage_status': getattr(task.coverage_status, 'value', str(task.coverage_status)),
            'status': getattr(task.status, 'value', str(task.status)),
            'test_type': getattr(task.test_type, 'value', str(task.test_type)),
            'dependencies': list(task.dependencies) if task.dependencies else [],
        }
    
    # Handle TestTaskModel (SQLAlchemy model)
    if isinstance(task, TestTaskModel):
        return {
            'id': task.id,
            'description': task.description,
            'owner': task.owner,
            'coverage_status': getattr(task.coverage_status, 'value', str(task.coverage_status)),
            'status': getattr(task.status, 'value', str(task.status)),
            'test_type': getattr(task.test_type, 'value', str(task.test_type)),
            'dependencies': list(task.dependencies) if task.dependencies else [],
        }
    
    raise TypeError(f"Unsupported task type: {type(task)}")


def export_to_json(
    test_plan: Iterable[Union[TestTask, TestTaskModel, Dict[str, Any]]],
    output_path: Union[str, Path],
    indent: int = 4,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> Path:
    """
    Export test plan data to JSON format.
    
    Args:
        test_plan: Iterable of task objects (TestTask, TestTaskModel) or dictionaries
        output_path: Path where the JSON file should be written
        indent: Number of spaces for indentation (default: 4)
        ensure_ascii: If True, escape non-ASCII characters (default: False)
        sort_keys: If True, sort dictionary keys in output (default: False)
    
    Returns:
        Path object pointing to the created JSON file
        
    Example:
        >>> from tasks.test_plan_generator import TestPlanGenerator
        >>> from database.data_access_layer import TestTaskDAL
        >>> 
        >>> generator = TestPlanGenerator()
        >>> dal = TestTaskDAL(session)
        >>> plan = generator.generate_plan_from_db(dal)
        >>> 
        >>> export_to_json(plan, 'test_plan.json')
        Path('test_plan.json')
    """
    output_path = Path(output_path)
    
    # Convert test plan to list and extract data
    tasks_data = []
    for task in test_plan:
        task_dict = _extract_task_data(task)
        tasks_data.append(task_dict)
    
    # Create JSON structure
    json_data = {
        'test_plan': tasks_data,
        'exported_at': datetime.utcnow().isoformat(),
        'total_tasks': len(tasks_data),
    }
    
    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(
            json_data,
            file,
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
        )
    
    return output_path


def export_to_json_simple(
    test_plan: Iterable[Dict[str, Any]],
    output_path: Union[str, Path],
    indent: int = 4,
) -> Path:
    """
    Simple JSON export function that writes the test plan directly as a JSON array.
    
    This is a convenience function that matches the microtask example format.
    
    Args:
        test_plan: Iterable of task dictionaries
        output_path: Path where the JSON file should be written
        indent: Number of spaces for indentation (default: 4)
        
    Returns:
        Path object pointing to the created JSON file
        
    Example:
        >>> test_plan = [
        ...     {'id': 'task-1', 'description': 'Write unit tests', 'owner': 'john.doe',
        ...      'coverage_status': 'not_started'},
        ...     {'id': 'task-2', 'description': 'Integration tests', 'owner': 'jane.smith',
        ...      'coverage_status': 'in_progress'},
        ... ]
        >>> export_to_json_simple(test_plan, 'test_plan.json')
        Path('test_plan.json')
    """
    output_path = Path(output_path)
    
    # Convert to list and ensure JSON-serializable
    tasks_list = []
    for task in test_plan:
        # Ensure all values are JSON-serializable
        serializable_task = {}
        for key, value in task.items():
            if value is None:
                serializable_task[key] = None
            elif isinstance(value, (str, int, float, bool)):
                serializable_task[key] = value
            elif isinstance(value, (list, tuple)):
                serializable_task[key] = list(value)
            else:
                serializable_task[key] = str(value)
        tasks_list.append(serializable_task)
    
    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(tasks_list, file, indent=indent, ensure_ascii=False)
    
    return output_path


def export_plan_from_db(
    dal: Any,  # TestTaskDAL type
    output_path: Union[str, Path],
    indent: int = 4,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
) -> Path:
    """
    Export test plan directly from database using DAL.
    
    This function fetches tasks from the database and exports them to JSON.
    
    Args:
        dal: TestTaskDAL instance to fetch tasks from database
        output_path: Path where the JSON file should be written
        indent: Number of spaces for indentation (default: 4)
        ensure_ascii: If True, escape non-ASCII characters (default: False)
        sort_keys: If True, sort dictionary keys in output (default: False)
        
    Returns:
        Path object pointing to the created JSON file
        
    Example:
        >>> from database.data_access_layer import TestTaskDAL
        >>> from database.postgresql_setup import get_sessionmaker
        >>> 
        >>> sessionmaker = get_sessionmaker()
        >>> session = sessionmaker()
        >>> dal = TestTaskDAL(session)
        >>> 
        >>> export_plan_from_db(dal, 'test_plan.json')
        Path('test_plan.json')
    """
    # Get tasks from database
    tasks = dal.plan_tasks()  # Returns ordered list of TestTaskModel
    
    return export_to_json(tasks, output_path, indent=indent, ensure_ascii=ensure_ascii, sort_keys=sort_keys)


__all__ = [
    'export_to_json',
    'export_to_json_simple',
    'export_plan_from_db',
]

