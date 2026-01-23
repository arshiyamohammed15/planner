from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.data_access_layer import TestTaskDAL
from tasks.task_assignment_workflow import TaskAssignmentWorkflow
from tasks.task_dependencies import TaskDependencies
from tasks.dependency_resolution import DependencyResolver
from tasks.task_status import TaskStatusManager
from tasks.test_task_model import CoverageStatus, TaskStatus, TestType


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session(engine):
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with SessionLocal() as session:
        yield session
        session.rollback()


def test_auto_assignment_by_test_type(session):
    workflow = TaskAssignmentWorkflow(session)

    # Unit -> developer
    t1 = workflow.create_and_assign_task(
        id="unit-1",
        description="Unit test",
        test_type=TestType.UNIT,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    # E2E -> tester
    t2 = workflow.create_and_assign_task(
        id="e2e-1",
        description="E2E test",
        test_type=TestType.E2E,
        coverage_status=CoverageStatus.NOT_STARTED,
    )

    assert t1.owner == "developer"
    assert t2.owner == "tester"


def test_dependencies_block_progress_until_done(session):
    dal = TestTaskDAL(session)
    deps = TaskDependencies(session)
    resolver = DependencyResolver(session)
    status_mgr = TaskStatusManager(session)

    # Create two tasks: tA depends on tB
    dal.create_task(
        id="tA",
        description="Depends on tB",
        test_type=TestType.INTEGRATION,
        status=TaskStatus.PENDING,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    dal.create_task(
        id="tB",
        description="Prereq",
        test_type=TestType.UNIT,
        status=TaskStatus.PENDING,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    session.commit()

    deps.set_dependencies("tA", ["tB"])

    # Cannot start tA until tB is done
    assert resolver.start_if_ready("tA") is False

    # Complete tB
    status_mgr.update_status("tB", TaskStatus.DONE)

    # Now tA can start
    assert resolver.start_if_ready("tA") is True
    # And can complete
    assert resolver.complete_if_ready("tA") is True

    # Verify final statuses
    tA = dal.get_task("tA")
    tB = dal.get_task("tB")
    assert tA.status == TaskStatus.DONE
    assert tB.status == TaskStatus.DONE

