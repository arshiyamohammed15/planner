from __future__ import annotations

import os
import shutil

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.backup_restore import backup_database, restore_database
from database.data_access_layer import CoverageDAL, TestTaskDAL
from database.models import Base
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


def test_task_crud(session: Session):
    dal = TestTaskDAL(session)

    # Create
    task = dal.create_task(
        id="t1",
        description="Write unit tests",
        test_type=TestType.UNIT,
        owner="qa",
        dependencies=["bootstrap"],
    )
    session.commit()

    fetched = dal.get_task("t1")
    assert fetched is not None
    assert fetched.description == "Write unit tests"
    assert fetched.test_type == TestType.UNIT
    assert fetched.dependencies == ["bootstrap"]

    # Update
    dal.update_task(
        "t1",
        description="Write unit tests for auth",
        status=TaskStatus.IN_PROGRESS,
        coverage_status=CoverageStatus.MISSING,
        dependencies=["bootstrap", "api-ready"],
    )
    session.commit()
    updated = dal.get_task("t1")
    assert updated.status == TaskStatus.IN_PROGRESS
    assert updated.coverage_status == CoverageStatus.MISSING
    assert updated.dependencies == ["bootstrap", "api-ready"]

    # Delete
    deleted = dal.delete_task("t1")
    session.commit()
    assert deleted == 1
    assert dal.get_task("t1") is None


def test_coverage_crud(session: Session):
    task_dal = TestTaskDAL(session)
    cov_dal = CoverageDAL(session)

    task_dal.create_task(
        id="t2",
        description="E2E checkout",
        test_type=TestType.E2E,
        status=TaskStatus.PENDING,
        coverage_status=CoverageStatus.NOT_STARTED,
    )
    session.commit()

    cov = cov_dal.add_coverage(task_id="t2", coverage_status=CoverageStatus.MISSING)
    session.commit()

    cov_list = cov_dal.list_by_task("t2")
    assert len(cov_list) == 1
    assert cov_list[0].coverage_status == CoverageStatus.MISSING

    cov_dal.update_coverage(cov_list[0].id, coverage_status=CoverageStatus.COMPLETE)
    session.commit()

    cov_list2 = cov_dal.list_by_task("t2")
    assert cov_list2[0].coverage_status == CoverageStatus.COMPLETE

    deleted = cov_dal.delete_coverage(cov_list2[0].id)
    session.commit()
    assert deleted == 1
    assert cov_dal.list_by_task("t2") == []


def test_backup_requires_pg_dump_when_missing():
    if shutil.which("pg_dump"):
        pytest.skip("pg_dump available; integration DB not configured for backup test.")
    with pytest.raises(RuntimeError):
        backup_database("dummy.sql", db_url="postgresql://user:pass@localhost/db")


def test_restore_requires_psql_or_pg_restore_when_missing():
    have_psql = shutil.which("psql") is not None
    have_pg_restore = shutil.which("pg_restore") is not None
    if have_psql or have_pg_restore:
        pytest.skip("psql/pg_restore available; integration DB not configured for restore test.")
    with pytest.raises(RuntimeError):
        restore_database("dummy.sql", db_url="postgresql://user:pass@localhost/db")

