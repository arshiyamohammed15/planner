from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.data_access_layer import TestTaskDAL
from tasks.task_assignment import TaskAssigner
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


def test_assignment_by_test_type(session):
    dal = TestTaskDAL(session)
    assigner = TaskAssigner(session)

    dal.create_task(
        id="u1",
        description="Unit task",
        test_type=TestType.UNIT,
        status=TaskStatus.PENDING,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    dal.create_task(
        id="e1",
        description="E2E task",
        test_type=TestType.E2E,
        status=TaskStatus.PENDING,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    session.commit()

    assert assigner.assign_task("u1") == "developer"
    assert assigner.assign_task("e1") == "tester"

    t1 = dal.get_task("u1")
    t2 = dal.get_task("e1")
    assert t1.owner == "developer"
    assert t2.owner == "tester"


def test_assignment_missing_task_returns_none(session):
    assigner = TaskAssigner(session)
    assert assigner.assign_task("does-not-exist") is None


def test_assignment_invalid_type_returns_none(session):
    # If the mapping is missing, assignment should return None
    dal = TestTaskDAL(session)
    dal.create_task(
        id="x1",
        description="Custom type",
        test_type=TestType.UNIT,
        status=TaskStatus.PENDING,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    session.commit()

    # Provide a mapping that does not include UNIT to simulate unmapped type
    assigner = TaskAssigner(session, role_map={TestType.E2E: "tester"})
    assert assigner.assign_task("x1") is None

