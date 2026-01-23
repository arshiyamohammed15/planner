"""
Unit tests for test plan import functionality.
"""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

import pytest

# Import using importlib to handle 'import' as module name
import importlib.util
from pathlib import Path

# Load the import_test_plans module
spec = importlib.util.spec_from_file_location(
    "import_test_plans",
    Path(__file__).parent.parent / "import" / "import_test_plans.py"
)
import_test_plans = importlib.util.module_from_spec(spec)
spec.loader.exec_module(import_test_plans)  # type: ignore

# Import functions
ImportValidationError = import_test_plans.ImportValidationError
import_from_csv = import_test_plans.import_from_csv
import_from_csv_simple = import_test_plans.import_from_csv_simple
import_from_json = import_test_plans.import_from_json
import_to_database = import_test_plans.import_to_database
from tasks.test_task_model import CoverageStatus, TaskStatus, TestTask, TestType


def test_import_from_csv_simple():
    """Test simple CSV import matching microtask example."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['Task ID', 'Description', 'Owner', 'Coverage Status'])
        writer.writerow(['task-1', 'Write unit tests', 'john.doe', 'not_started'])
        writer.writerow(['task-2', 'Integration tests', 'jane.smith', 'in_progress'])
    
    try:
        tasks = import_from_csv_simple(output_path)
        
        assert len(tasks) == 2
        assert tasks[0]['id'] == 'task-1'
        assert tasks[0]['description'] == 'Write unit tests'
        assert tasks[0]['owner'] == 'john.doe'
        assert tasks[0]['coverage_status'] == 'not_started'
        
        assert tasks[1]['id'] == 'task-2'
        assert tasks[1]['description'] == 'Integration tests'
        assert tasks[1]['owner'] == 'jane.smith'
        assert tasks[1]['coverage_status'] == 'in_progress'
    finally:
        output_path.unlink()


def test_import_from_csv():
    """Test CSV import with full TestTask objects."""
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['Task ID', 'Description', 'Owner', 'Coverage Status', 'Status', 'Test Type', 'Dependencies'])
        writer.writerow(['task-1', 'Write unit tests', 'john.doe', 'not_started', 'pending', 'unit', ''])
        writer.writerow(['task-2', 'Integration tests', 'jane.smith', 'in_progress', 'in_progress', 'integration', 'task-1'])
    
    try:
        tasks = import_from_csv(output_path)
        
        assert len(tasks) == 2
        assert isinstance(tasks[0], TestTask)
        assert tasks[0].id == 'task-1'
        assert tasks[0].description == 'Write unit tests'
        assert tasks[0].owner == 'john.doe'
        assert tasks[0].coverage_status == CoverageStatus.NOT_STARTED
        assert tasks[0].status == TaskStatus.PENDING
        assert tasks[0].test_type == TestType.UNIT
        assert tasks[0].dependencies == []
        
        assert tasks[1].id == 'task-2'
        assert tasks[1].test_type == TestType.INTEGRATION
        assert tasks[1].dependencies == ['task-1']
    finally:
        output_path.unlink()


def test_import_from_csv_case_insensitive_headers():
    """Test CSV import with case-insensitive headers."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['TASK ID', 'DESCRIPTION', 'OWNER', 'COVERAGE STATUS'])
        writer.writerow(['task-1', 'Test task', 'john.doe', 'not_started'])
    
    try:
        tasks = import_from_csv(output_path)
        assert len(tasks) == 1
        assert tasks[0].id == 'task-1'
    finally:
        output_path.unlink()


def test_import_from_csv_alternative_column_names():
    """Test CSV import with alternative column names."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['task_id', 'desc', 'assignee', 'coverage'])
        writer.writerow(['task-1', 'Test task', 'john.doe', 'not_started'])
    
    try:
        tasks = import_from_csv(output_path)
        assert len(tasks) == 1
        assert tasks[0].id == 'task-1'
        assert tasks[0].description == 'Test task'
        assert tasks[0].owner == 'john.doe'
    finally:
        output_path.unlink()


def test_import_from_csv_missing_required_fields():
    """Test CSV import validation with missing required fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['Task ID', 'Description'])
        writer.writerow(['', 'Test task'])  # Missing ID
        writer.writerow(['task-2', ''])  # Missing description
    
    try:
        with pytest.raises(ImportValidationError, match="Task 'id' is required"):
            import_from_csv(output_path)
    finally:
        output_path.unlink()


def test_import_from_csv_invalid_enum_values():
    """Test CSV import validation with invalid enum values."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['Task ID', 'Description', 'Test Type'])
        writer.writerow(['task-1', 'Test task', 'invalid_type'])
    
    try:
        with pytest.raises(ImportValidationError, match="Invalid test_type"):
            import_from_csv(output_path)
    finally:
        output_path.unlink()


def test_import_from_csv_defaults():
    """Test CSV import with default values for optional fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['Task ID', 'Description'])
        writer.writerow(['task-1', 'Test task'])
    
    try:
        tasks = import_from_csv(output_path)
        assert len(tasks) == 1
        assert tasks[0].test_type == TestType.UNIT  # Default
        assert tasks[0].status == TaskStatus.PENDING  # Default
        assert tasks[0].coverage_status == CoverageStatus.NOT_STARTED  # Default
        assert tasks[0].owner is None  # Default
        assert tasks[0].dependencies == []  # Default
    finally:
        output_path.unlink()


def test_import_from_json_list():
    """Test JSON import from a list format."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
        json.dump([
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
        ], tmp, indent=2)
    
    try:
        tasks = import_from_json(output_path)
        
        assert len(tasks) == 2
        assert isinstance(tasks[0], TestTask)
        assert tasks[0].id == 'task-1'
        assert tasks[0].test_type == TestType.UNIT
        assert tasks[1].id == 'task-2'
        assert tasks[1].test_type == TestType.INTEGRATION
        assert tasks[1].dependencies == ['task-1']
    finally:
        output_path.unlink()


def test_import_from_json_with_test_plan_key():
    """Test JSON import from object with 'test_plan' key."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
        json.dump({
            'test_plan': [
                {
                    'id': 'task-1',
                    'description': 'Write unit tests',
                    'owner': 'john.doe',
                    'coverage_status': 'not_started',
                }
            ],
            'exported_at': '2026-01-15T14:00:00',
            'total_tasks': 1,
        }, tmp, indent=2)
    
    try:
        tasks = import_from_json(output_path)
        assert len(tasks) == 1
        assert tasks[0].id == 'task-1'
    finally:
        output_path.unlink()


def test_import_from_json_with_tasks_key():
    """Test JSON import from object with 'tasks' key."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
        json.dump({
            'tasks': [
                {
                    'id': 'task-1',
                    'description': 'Write unit tests',
                    'owner': 'john.doe',
                    'coverage_status': 'not_started',
                }
            ],
        }, tmp, indent=2)
    
    try:
        tasks = import_from_json(output_path)
        assert len(tasks) == 1
        assert tasks[0].id == 'task-1'
    finally:
        output_path.unlink()


def test_import_from_json_validation_error():
    """Test JSON import with validation errors."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
        json.dump([
            {
                'id': '',  # Invalid: empty ID
                'description': 'Test task',
            }
        ], tmp, indent=2)
    
    try:
        with pytest.raises(ImportValidationError, match="Task 'id' is required"):
            import_from_json(output_path)
    finally:
        output_path.unlink()


def test_import_from_csv_dependencies():
    """Test CSV import with dependencies."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as tmp:
        output_path = Path(tmp.name)
        writer = csv.writer(tmp)
        writer.writerow(['Task ID', 'Description', 'Dependencies'])
        writer.writerow(['task-1', 'First task', ''])
        writer.writerow(['task-2', 'Second task', 'task-1'])
        writer.writerow(['task-3', 'Third task', 'task-1,task-2'])
    
    try:
        tasks = import_from_csv(output_path)
        assert len(tasks) == 3
        assert tasks[0].dependencies == []
        assert tasks[1].dependencies == ['task-1']
        assert tasks[2].dependencies == ['task-1', 'task-2']
    finally:
        output_path.unlink()


def test_import_from_json_dependencies():
    """Test JSON import with dependencies as list."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        output_path = Path(tmp.name)
        json.dump([
            {
                'id': 'task-1',
                'description': 'First task',
                'dependencies': [],
            },
            {
                'id': 'task-2',
                'description': 'Second task',
                'dependencies': ['task-1'],
            },
        ], tmp, indent=2)
    
    try:
        tasks = import_from_json(output_path)
        assert len(tasks) == 2
        assert tasks[0].dependencies == []
        assert tasks[1].dependencies == ['task-1']
    finally:
        output_path.unlink()


@pytest.fixture(scope="module")
def engine():
    """Create in-memory SQLite database for testing."""
    from sqlalchemy import create_engine
    from database.models import Base
    eng = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    """Create a database session for each test."""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as session:
        yield session
        session.rollback()


def test_import_to_database(session):
    """Test importing tasks to database."""
    from database.data_access_layer import TestTaskDAL
    
    dal = TestTaskDAL(session)
    
    tasks = [
        TestTask(
            id='imported-task-1',
            description='Imported task 1',
            test_type=TestType.UNIT,
            owner='john.doe',
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=[],
        ),
        TestTask(
            id='imported-task-2',
            description='Imported task 2',
            test_type=TestType.INTEGRATION,
            owner='jane.smith',
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=['imported-task-1'],
        ),
    ]
    
    result = import_to_database(tasks, dal, skip_existing=True)
    
    assert result['imported'] == 2
    assert result['skipped'] == 0
    assert result['failed'] == 0
    assert len(result['errors']) == 0
    
    # Verify tasks were created
    task1 = dal.get_task('imported-task-1')
    assert task1 is not None
    assert task1.description == 'Imported task 1'
    
    task2 = dal.get_task('imported-task-2')
    assert task2 is not None
    assert task2.description == 'Imported task 2'


def test_import_to_database_skip_existing(session):
    """Test importing tasks with skip_existing=True."""
    from database.data_access_layer import TestTaskDAL
    
    dal = TestTaskDAL(session)
    
    # Create an existing task
    dal.create_task(
        id='existing-task',
        description='Existing task',
        test_type=TestType.UNIT,
    )
    session.commit()
    
    # Try to import the same task
    tasks = [
        TestTask(
            id='existing-task',
            description='Updated description',
            test_type=TestType.UNIT,
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=[],
        ),
        TestTask(
            id='new-task',
            description='New task',
            test_type=TestType.UNIT,
            status=TaskStatus.PENDING,
            coverage_status=CoverageStatus.NOT_STARTED,
            dependencies=[],
        ),
    ]
    
    result = import_to_database(tasks, dal, skip_existing=True)
    
    assert result['imported'] == 1  # Only new task imported
    assert result['skipped'] == 1  # Existing task skipped
    assert result['failed'] == 0
    
    # Verify existing task was not updated
    existing = dal.get_task('existing-task')
    assert existing is not None
    assert existing.description == 'Existing task'  # Original description


def test_import_from_csv_file_not_found():
    """Test CSV import with non-existent file."""
    with pytest.raises(FileNotFoundError):
        import_from_csv('nonexistent.csv')


def test_import_from_json_file_not_found():
    """Test JSON import with non-existent file."""
    with pytest.raises(FileNotFoundError):
        import_from_json('nonexistent.json')

