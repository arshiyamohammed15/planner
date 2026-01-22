"""
CSV Export functionality for test plans.

This module provides functions to export test plan data to CSV format,
making it easy to share and work with in tools like Excel or Google Sheets.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from database.models import TestTaskModel
from tasks.test_task_model import TestTask


def _extract_task_data(task: Union[TestTask, TestTaskModel, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract task data from various input types.
    
    Args:
        task: Task object (TestTask, TestTaskModel) or dictionary
        
    Returns:
        Dictionary with task data
    """
    if isinstance(task, dict):
        return task
    
    # Handle TestTask dataclass
    if isinstance(task, TestTask):
        return {
            'id': task.id,
            'description': task.description,
            'owner': task.owner or '',
            'coverage_status': getattr(task.coverage_status, 'value', str(task.coverage_status)),
            'status': getattr(task.status, 'value', str(task.status)),
            'test_type': getattr(task.test_type, 'value', str(task.test_type)),
            'dependencies': ', '.join(task.dependencies) if task.dependencies else '',
        }
    
    # Handle TestTaskModel (SQLAlchemy model)
    if isinstance(task, TestTaskModel):
        return {
            'id': task.id,
            'description': task.description,
            'owner': task.owner or '',
            'coverage_status': getattr(task.coverage_status, 'value', str(task.coverage_status)),
            'status': getattr(task.status, 'value', str(task.status)),
            'test_type': getattr(task.test_type, 'value', str(task.test_type)),
            'dependencies': ', '.join(task.dependencies) if task.dependencies else '',
        }
    
    raise TypeError(f"Unsupported task type: {type(task)}")


def export_to_csv(
    test_plan: Iterable[Union[TestTask, TestTaskModel, Dict[str, Any]]],
    output_path: Union[str, Path],
    include_headers: bool = True,
    columns: Optional[List[str]] = None,
) -> Path:
    """
    Export test plan data to CSV format.
    
    Args:
        test_plan: Iterable of task objects (TestTask, TestTaskModel) or dictionaries
        output_path: Path where the CSV file should be written
        include_headers: Whether to include column headers (default: True)
        columns: Optional list of column names to include. If None, uses default columns.
                 Default columns: ['Task ID', 'Description', 'Owner', 'Coverage Status', 
                                  'Status', 'Test Type', 'Dependencies']
    
    Returns:
        Path object pointing to the created CSV file
        
    Example:
        >>> from tasks.test_plan_generator import TestPlanGenerator
        >>> from database.data_access_layer import TestTaskDAL
        >>> 
        >>> generator = TestPlanGenerator()
        >>> dal = TestTaskDAL(session)
        >>> plan = generator.generate_plan_from_db(dal)
        >>> 
        >>> export_to_csv(plan, 'test_plan.csv')
        Path('test_plan.csv')
    """
    output_path = Path(output_path)
    
    # Default columns if not specified
    if columns is None:
        columns = [
            'Task ID',
            'Description',
            'Owner',
            'Coverage Status',
            'Status',
            'Test Type',
            'Dependencies',
        ]
    
    # Map column names to task data keys
    column_mapping = {
        'Task ID': 'id',
        'Description': 'description',
        'Owner': 'owner',
        'Coverage Status': 'coverage_status',
        'Status': 'status',
        'Test Type': 'test_type',
        'Dependencies': 'dependencies',
    }
    
    # Convert test plan to list and extract data
    tasks_data = []
    for task in test_plan:
        task_dict = _extract_task_data(task)
        tasks_data.append(task_dict)
    
    # Write CSV file
    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write headers if requested
        if include_headers:
            writer.writerow(columns)
        
        # Write task data rows
        for task_dict in tasks_data:
            row = []
            for column in columns:
                key = column_mapping.get(column, column.lower().replace(' ', '_'))
                value = task_dict.get(key, '')
                # Convert to string and handle None values
                row.append(str(value) if value is not None else '')
            writer.writerow(row)
    
    return output_path


def export_to_csv_simple(
    test_plan: Iterable[Dict[str, Any]],
    output_path: Union[str, Path],
) -> Path:
    """
    Simple CSV export function with minimal columns (Task ID, Description, Owner, Coverage Status).
    
    This is a convenience function that uses only the essential columns as specified
    in the microtask requirements.
    
    Args:
        test_plan: Iterable of task dictionaries with keys: id, description, owner, coverage_status
        output_path: Path where the CSV file should be written
        
    Returns:
        Path object pointing to the created CSV file
        
    Example:
        >>> test_plan = [
        ...     {'id': 'task-1', 'description': 'Write unit tests', 'owner': 'john.doe', 
        ...      'coverage_status': 'not_started'},
        ...     {'id': 'task-2', 'description': 'Integration tests', 'owner': 'jane.smith',
        ...      'coverage_status': 'in_progress'},
        ... ]
        >>> export_to_csv_simple(test_plan, 'test_plan.csv')
        Path('test_plan.csv')
    """
    output_path = Path(output_path)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Task ID', 'Description', 'Owner', 'Coverage Status'])
        
        for task in test_plan:
            writer.writerow([
                task.get('id', ''),
                task.get('description', ''),
                task.get('owner', ''),
                task.get('coverage_status', ''),
            ])
    
    return output_path


def export_plan_from_db(
    dal: Any,  # TestTaskDAL type
    output_path: Union[str, Path],
    include_headers: bool = True,
    columns: Optional[List[str]] = None,
) -> Path:
    """
    Export test plan directly from database using DAL.
    
    This function fetches tasks from the database and exports them to CSV.
    
    Args:
        dal: TestTaskDAL instance to fetch tasks from database
        output_path: Path where the CSV file should be written
        include_headers: Whether to include column headers (default: True)
        columns: Optional list of column names to include
        
    Returns:
        Path object pointing to the created CSV file
        
    Example:
        >>> from database.data_access_layer import TestTaskDAL
        >>> from database.postgresql_setup import get_sessionmaker
        >>> 
        >>> sessionmaker = get_sessionmaker()
        >>> session = sessionmaker()
        >>> dal = TestTaskDAL(session)
        >>> 
        >>> export_plan_from_db(dal, 'test_plan.csv')
        Path('test_plan.csv')
    """
    # Get tasks from database
    tasks = dal.plan_tasks()  # Returns ordered list of TestTaskModel
    
    return export_to_csv(tasks, output_path, include_headers=include_headers, columns=columns)


__all__ = [
    'export_to_csv',
    'export_to_csv_simple',
    'export_plan_from_db',
]

