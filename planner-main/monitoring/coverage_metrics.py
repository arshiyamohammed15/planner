"""Database model for storing test coverage metrics over time."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.postgresql_setup import Base


class CoverageMetricsModel(Base):
    """
    Store test coverage metrics over time for dashboard visualization.
    
    Tracks coverage percentage, total lines, covered lines, and timestamp
    for historical trend analysis.
    """
    __tablename__ = "coverage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    
    # Coverage metrics
    coverage_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    total_lines: Mapped[int] = mapped_column(Integer, nullable=False)
    covered_lines: Mapped[int] = mapped_column(Integer, nullable=False)
    missing_lines: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Additional metadata
    branch_coverage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    test_suite: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    commit_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    branch_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CoverageMetricsModel(id={self.id}, "
            f"timestamp={self.timestamp}, "
            f"coverage={self.coverage_percentage}%)>"
        )


__all__ = ["CoverageMetricsModel"]

