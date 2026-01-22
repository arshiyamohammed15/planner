from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.postgresql_setup import Base
from tasks.test_task_model import CoverageStatus, TaskStatus, TestType


class TestTaskModel(Base):
    __tablename__ = "test_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    test_type: Mapped[TestType] = mapped_column(
        Enum(TestType, name="test_type_enum"), nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status_enum"), nullable=False
    )
    owner: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    coverage_status: Mapped[CoverageStatus] = mapped_column(
        Enum(CoverageStatus, name="coverage_status_enum"), nullable=False
    )
    # store dependencies as a simple comma-separated string
    dependencies_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    coverages: Mapped[List["CoverageModel"]] = relationship(
        "CoverageModel", back_populates="task", cascade="all, delete-orphan"
    )
    comments: Mapped[List["CommentModel"]] = relationship(
        "CommentModel", back_populates="task", cascade="all, delete-orphan"
    )

    @property
    def dependencies(self) -> List[str]:
        if not self.dependencies_raw:
            return []
        return [d.strip() for d in self.dependencies_raw.split(",") if d.strip()]

    @dependencies.setter
    def dependencies(self, deps: List[str]) -> None:
        if not deps:
            self.dependencies_raw = None
        else:
            self.dependencies_raw = ",".join(str(d).strip() for d in deps if str(d).strip())


class CoverageModel(Base):
    __tablename__ = "coverage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    coverage_status: Mapped[CoverageStatus] = mapped_column(
        Enum(CoverageStatus, name="coverage_status_enum"), nullable=False
    )

    task: Mapped[TestTaskModel] = relationship("TestTaskModel", back_populates="coverages")


class CommentModel(Base):
    """Model for storing comments on test tasks."""
    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("test_tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user: Mapped[str] = mapped_column(String(128), nullable=False)
    comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    task: Mapped[TestTaskModel] = relationship("TestTaskModel", back_populates="comments")

    def __repr__(self) -> str:
        return f"<CommentModel(id={self.id}, task_id={self.task_id}, user={self.user}, timestamp={self.timestamp})>"


__all__ = ["TestTaskModel", "CoverageModel", "CommentModel"]

