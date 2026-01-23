from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class PlanRequest(BaseModel):
    """Input payload for generating a test plan."""

    goal: str = Field(..., description="Primary testing objective.")
    feature: str = Field(..., description="Feature under test.")
    constraints: Optional[List[str]] = Field(
        default=None, description="Optional constraints or considerations."
    )
    owner: Optional[str] = Field(
        default=None, description="Requester or team initiating the plan."
    )
    template_name: Optional[str] = Field(
        default="basic", description="Template to use for plan generation (basic, complex, minimal, full_coverage)."
    )
    save_to_database: Optional[bool] = Field(
        default=True, description="Whether to save the generated plan to the database."
    )

    @field_validator("goal", "feature")
    @classmethod
    def must_not_be_blank(cls, value: str, info: ValidationInfo):
        # Use policy-driven validation if available
        try:
            from policies import get_policy_loader
            policy = get_policy_loader().get_config().validation
            min_length = policy.min_goal_length if info.field_name == "goal" else policy.min_feature_length
            if not value or len(str(value).strip()) < min_length:
                raise ValueError(
                    f"{info.field_name} must not be empty and must be at least {min_length} character(s)."
                )
        except Exception:
            # Fall back to basic validation if policy not available
            if not value or not str(value).strip():
                raise ValueError(f"{info.field_name} must not be empty.")
        return str(value).strip()

    @field_validator("constraints")
    @classmethod
    def normalize_constraints(cls, constraints: Optional[List[str]]):
        if constraints is None:
            return constraints
        
        # Use policy-driven validation if available
        try:
            from policies import get_policy_loader
            policy = get_policy_loader().get_config().validation
            if policy.max_constraints is not None and len(constraints) > policy.max_constraints:
                raise ValueError(
                    f"Maximum {policy.max_constraints} constraint(s) allowed, got {len(constraints)}."
                )
        except ValueError:
            raise
        except Exception:
            pass  # Fall back to basic normalization
        
        cleaned = [c.strip() for c in constraints if c and c.strip()]
        return cleaned or None


class TaskItem(BaseModel):
    """Minimal representation of a planned task."""

    id: str
    description: str
    test_type: str = Field(
        ...,
        description="Type of test (unit, integration, e2e, exploratory, etc.).",
    )
    status: str = Field(default="pending", description="Task status.")

    @field_validator("id", mode="before")
    @classmethod
    def validate_task_id(cls, value: str):
        if not value or not str(value).strip():
            raise ValueError("task id must not be empty.")
        return str(value).strip()


class PlanResponse(BaseModel):
    """Response structure for a generated plan."""

    plan_id: str
    feature: str
    goal: str
    tasks: List[TaskItem]
    summary: Optional[str] = None


class PlanDetailResponse(BaseModel):
    """Detailed plan information with all tasks."""

    plan_id: str
    feature: str
    goal: str
    tasks: List[TaskItem]
    summary: Optional[str] = None
    created_at: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized error response."""

    detail: str


class AssignTaskRequest(BaseModel):
    """Input payload for assigning a task."""

    task_id: str = Field(..., description="Identifier of the task to assign.")
    owner: str = Field(..., description="Assignee (developer or tester).")

    @field_validator("task_id", "owner")
    @classmethod
    def must_not_be_blank(cls, value: str, info: ValidationInfo):
        if not value or not str(value).strip():
            raise ValueError(f"{info.field_name} must not be empty.")
        return str(value).strip()


class AssignTaskResponse(BaseModel):
    """Response payload for a task assignment."""

    task_id: str
    owner: str
    message: str


class CommentResponse(BaseModel):
    """Response structure for a comment."""

    id: int
    task_id: str
    user: str
    comment_text: str
    timestamp: str


class AddCommentRequest(BaseModel):
    """Request payload for adding a comment to a task."""

    user: str = Field(..., description="Username/author of the comment")
    comment_text: str = Field(..., description="The comment text content")

    @field_validator("user", "comment_text")
    @classmethod
    def must_not_be_blank(cls, value: str, info: ValidationInfo):
        if not value or not str(value).strip():
            raise ValueError(f"{info.field_name} must not be empty.")
        return str(value).strip()


class TaskDetailResponse(BaseModel):
    """Detailed task information including comments."""

    id: str
    description: str
    test_type: str
    status: str
    owner: Optional[str] = None
    coverage_status: str
    dependencies: List[str] = Field(default_factory=list)
    comments: List[CommentResponse] = Field(default_factory=list)


class CoverageGapItem(BaseModel):
    """Represents a single missing test scenario."""

    task_id: str
    description: str
    test_type: str
    priority: int = Field(..., description="Priority value (higher = more important)")
    coverage_status: str


class CoverageGapResponse(BaseModel):
    """Response for coverage gap analysis endpoint."""

    plan_id: str
    total_tasks: int
    missing_count: int
    gaps: List[CoverageGapItem]
    summary: str


class CoverageAnalysisResponse(BaseModel):
    """Comprehensive coverage analysis response."""

    plan_id: str
    coverage_by_type: Dict[str, Dict] = Field(
        ..., description="Coverage breakdown by test type"
    )
    missing_test_types: List[str] = Field(
        default_factory=list, description="Test types not covered"
    )
    prioritized_gaps: List[CoverageGapItem]
    coverage_percentage: float = Field(
        ..., description="Overall coverage percentage (0-100)"
    )
