from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class TestType(str, Enum):
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    EXPLORATORY = "exploratory"
    PERFORMANCE = "performance"
    SECURITY = "security"
    __test__ = False  # prevent pytest from collecting as tests

    @classmethod
    def choices(cls) -> List[str]:
        """Return list of allowed test type strings."""
        return [item.value for item in cls]


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"
    __test__ = False


class CoverageStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    MISSING = "missing"
    __test__ = False


@dataclass
class TestTask:
    """
    Represents a test task with metadata for planning and coverage tracking.
    """

    __test__ = False  # prevent pytest from collecting this dataclass as a test

    id: str
    description: str
    test_type: TestType
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    owner: Optional[str] = None
    coverage_status: CoverageStatus = CoverageStatus.NOT_STARTED

    def is_ready(self) -> bool:
        """Returns True if the task has no dependencies."""
        return len(self.dependencies) == 0

    def __post_init__(self) -> None:
        # Accept string inputs for test_type and coerce to TestType if valid
        if isinstance(self.test_type, str):
            try:
                self.test_type = TestType(self.test_type)
            except ValueError as exc:
                raise ValueError(
                    f"Invalid test_type '{self.test_type}'. "
                    f"Allowed: {', '.join(TestType.choices())}"
                ) from exc
        if not isinstance(self.test_type, TestType):
            raise ValueError(
                f"Invalid test_type '{self.test_type}'. Allowed: {', '.join(TestType.choices())}"
            )

        # Normalize dependencies to strings
        self.dependencies = [str(dep) for dep in self.dependencies]

