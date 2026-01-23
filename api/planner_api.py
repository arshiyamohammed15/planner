from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional
from uuid import uuid4


# Ensure environment variables are set if not already present
# This helps when the API is started without the PowerShell script
if not os.environ.get("POSTGRES_PASSWORD") and os.environ.get("POSTGRES_USER") == "postgres":
    # Try to read from a config file or use defaults
    # For now, we'll let the database setup use defaults
    pass

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.authentication import auth_guard, register_auth_middleware
from error_logger import log_error, setup_exception_handler, setup_stderr_capture

# Set up automatic error logging
setup_exception_handler()
setup_stderr_capture()

# PostgreSQL environment variables are now set in postgresql_setup.py
# to ensure they are available before any database connections are attempted
from api.models import (
    AddCommentRequest,
    AssignTaskRequest,
    AssignTaskResponse,
    CommentResponse,
    CoverageAnalysisResponse,
    CoverageGapItem,
    CoverageGapResponse,
    ErrorResponse,
    PlanDetailResponse,
    PlanRequest,
    PlanResponse,
    TaskDetailResponse,
    TaskItem,
)
from coverage.coverage_analyzer import CoverageAnalyzer, TEST_TYPE_PRIORITY
from database.postgresql_setup import get_sessionmaker
from database.data_access_layer import TestTaskDAL
from database.models import TestTaskModel
from tasks.test_plan_generator import TestPlanGenerator
from tasks.task_assignment import TaskAssigner
from templates.test_plan_templates import generate_from_template, list_templates, TEMPLATE_REGISTRY
from tasks.test_task_model import TestTask, TaskStatus, CoverageStatus, TestType


def convert_task_model_to_test_task(model: TestTaskModel) -> TestTask:
    """Convert database model to TestTask dataclass."""
    return TestTask(
        id=model.id,
        description=model.description,
        test_type=model.test_type,
        dependencies=model.dependencies,
        status=model.status,
        owner=model.owner,
        coverage_status=model.coverage_status,
    )


class PlannerAgent:
    """
    Planner Agent implementation that generates test plans and assigns tasks.
    
    Integrates with:
    - Policy-driven configuration system
    - Template system for plan generation (loadable from YAML)
    - TestPlanGenerator for dependency-aware ordering
    - Database for persistence
    - TaskAssigner for automatic task assignment
    """

    def __init__(self, policy_loader=None, template_loader=None) -> None:
        """
        Initialize PlannerAgent with policy and template loaders.

        Args:
            policy_loader: Optional policy loader (uses global if None)
            template_loader: Optional template loader (uses global if None)
        """
        from policies import get_policy_loader
        from templates.template_loader import get_template_loader

        if policy_loader is None:
            policy_loader = get_policy_loader()
        if template_loader is None:
            template_loader = get_template_loader()

        self.policy_loader = policy_loader
        self.template_loader = template_loader
        self.plan_generator = TestPlanGenerator(policy_loader)

    def generate_test_plan(self, payload: PlanRequest, session: Session) -> PlanResponse:
        """
        Generate a test plan using templates and save to database if requested.
        
        Args:
            payload: Plan request with feature, goal, constraints, etc.
            session: Database session for persistence
            
        Returns:
            PlanResponse with generated plan details
        """
        plan_id = f"plan-{uuid4().hex[:8]}"
        
        # Get template name from policy or request
        policy = self.policy_loader.get_config()
        template_name = payload.template_name or policy.template.get_template()
        
        # Validate template name using template loader
        template = self.template_loader.get_template(template_name)
        if not template:
            available_templates = self.template_loader.list_templates()
            available = ', '.join([t['name'] for t in available_templates])
            raise ValueError(
                f"Template '{template_name}' not found. Available templates: {available}"
            )
        
        # Generate tasks from template (using template loader)
        task_id_prefix = f"{plan_id}-task"
        # Use template from loader
        template = self.template_loader.get_template(template_name)
        if not template:
            available_templates = self.template_loader.list_templates()
            available = ', '.join([t['name'] for t in available_templates])
            raise ValueError(
                f"Template '{template_name}' not found. Available templates: {available}"
            )
        
        # Generate tasks using the template
        test_tasks = generate_from_template(
            template_name=template_name,
            feature=payload.feature,
            goal=payload.goal,
            task_id_prefix=task_id_prefix,
            owner=payload.owner,
            constraints=payload.constraints,
        )
        
        # Generate ordered plan respecting dependencies
        ordered_tasks = self.plan_generator.generate_plan(test_tasks)
        
        # Save to database if requested
        dal = TestTaskDAL(session)
        saved_task_ids = []
        
        if payload.save_to_database:
            for task in ordered_tasks:
                try:
                    # Check if task already exists
                    existing = dal.get_task(task.id)
                    if existing:
                        # Update existing task
                        dal.update_task(
                            task.id,
                            description=task.description,
                            test_type=task.test_type,
                            status=task.status,
                            owner=task.owner,
                            dependencies=task.dependencies,
                        )
                    else:
                        # Create new task
                        dal.create_task(
                            id=task.id,
                            description=task.description,
                            test_type=task.test_type,
                            status=task.status,
                            owner=task.owner,
                            coverage_status=task.coverage_status,
                            dependencies=task.dependencies,
                        )
                    saved_task_ids.append(task.id)
                except Exception as e:
                    # Log error but continue with other tasks
                    print(f"Warning: Failed to save task {task.id}: {e}")
            
            # Commit all tasks
            try:
                session.commit()
            except Exception as e:
                session.rollback()
                raise ValueError(f"Failed to save plan to database: {e}") from e
        
        # Convert to API response format
        task_items = [
            TaskItem(
                id=task.id,
                description=task.description,
                test_type=task.test_type.value,
                status=task.status.value,
            )
            for task in ordered_tasks
        ]
        
        summary_parts = [
            f"{len(task_items)} tasks generated from '{template_name}' template",
            f"feature: {payload.feature}",
            f"goal: {payload.goal}",
        ]
        if payload.owner:
            summary_parts.append(f"owner: {payload.owner}")
        if payload.save_to_database:
            summary_parts.append(f"saved {len(saved_task_ids)} tasks to database")
        
        return PlanResponse(
            plan_id=plan_id,
            feature=payload.feature,
            goal=payload.goal,
            tasks=task_items,
            summary="; ".join(summary_parts),
        )

    def assign_task(self, request: AssignTaskRequest, session: Session) -> AssignTaskResponse:
        """
        Assign a task to an owner using the TaskAssigner.
        
        Args:
            request: Assignment request with task_id and owner
            session: Database session
            
        Returns:
            AssignTaskResponse with assignment details
        """
        dal = TestTaskDAL(session)
        task = dal.get_task(request.task_id)
        
        if not task:
            raise ValueError(f"Task {request.task_id} not found.")
        
        # Update task owner
        dal.update_task(request.task_id, owner=request.owner)
        session.commit()
        
        return AssignTaskResponse(
            task_id=request.task_id,
            owner=request.owner,
            message=f"Task {request.task_id} assigned to {request.owner}.",
        )
    
    def auto_assign_task(self, task_id: str, session: Session) -> AssignTaskResponse:
        """
        Automatically assign a task based on test type using TaskAssigner.
        Uses policy-driven assignment rules.
        
        Args:
            task_id: ID of the task to assign
            session: Database session
            
        Returns:
            AssignTaskResponse with assignment details
        """
        assigner = TaskAssigner(session, policy_loader=self.policy_loader)
        assignee = assigner.assign_task(task_id)
        
        if not assignee:
            raise ValueError(f"Could not auto-assign task {task_id}. Task not found or test type not mapped.")
        
        return AssignTaskResponse(
            task_id=task_id,
            owner=assignee,
            message=f"Task {task_id} automatically assigned to {assignee} based on test type.",
        )

    def analyze_coverage_gaps(self, plan_id: str, session: Session) -> CoverageGapResponse:
        """
        Analyze a plan to identify missing test coverage.
        
        Args:
            plan_id: ID of the plan to analyze
            session: Database session
            
        Returns:
            CoverageGapResponse with prioritized list of missing coverage tasks
        """
        dal = TestTaskDAL(session)
        all_tasks = dal.list_tasks()
        
        # Filter tasks for this plan
        plan_tasks = [t for t in all_tasks if t.id.startswith(f"{plan_id}-task")]
        
        if not plan_tasks:
            raise ValueError(f"Plan {plan_id} not found.")
        
        # Convert TestTaskModel to TestTask
        test_tasks = [convert_task_model_to_test_task(model) for model in plan_tasks]
        
        # Use CoverageAnalyzer to find and prioritize gaps
        analyzer = CoverageAnalyzer()
        prioritized_gaps = analyzer.prioritize_tests(test_tasks)
        
        # Convert to CoverageGapItem
        gap_items = []
        for task in prioritized_gaps:
            priority = TEST_TYPE_PRIORITY.get(task.test_type, 0)
            gap_items.append(
                CoverageGapItem(
                    task_id=task.id,
                    description=task.description,
                    test_type=task.test_type.value,
                    priority=priority,
                    coverage_status=task.coverage_status.value if hasattr(task.coverage_status, 'value') else str(task.coverage_status),
                )
            )
        
        # Generate summary
        summary_parts = [
            f"Found {len(gap_items)} missing coverage task(s) out of {len(plan_tasks)} total task(s)."
        ]
        if gap_items:
            summary_parts.append(
                f"Highest priority gaps: {gap_items[0].test_type} (priority {gap_items[0].priority})"
            )
        else:
            summary_parts.append("All tasks have coverage assigned.")
        
        return CoverageGapResponse(
            plan_id=plan_id,
            total_tasks=len(plan_tasks),
            missing_count=len(gap_items),
            gaps=gap_items,
            summary=" ".join(summary_parts),
        )


# Security scheme for Swagger UI
security_scheme = HTTPBearer(
    bearerFormat="JWT",
    description="Enter your JWT token. Get a token from POST /token endpoint.",
)

app = FastAPI(
    title="Planner Agent API",
    version="0.1.0",
    description="API surface for interacting with the Planner Agent.",
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "docExpansion": "list",
        "filter": True,
        "showExtensions": True,
        "showCommonExtensions": True,
    },
)


# Exception handlers for FastAPI
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handler for HTTPExceptions - logs 4xx and 5xx errors.
    """
    # Only log 5xx errors (server errors), not 4xx (client errors)
    if exc.status_code >= 500:
        error_context = {
            "path": str(request.url.path),
            "method": request.method,
            "status_code": exc.status_code,
            "client": request.client.host if request.client else "unknown",
        }
        log_error(exc, context=error_context)
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler that logs all unhandled exceptions to errors.log.
    """
    # Log the error
    error_context = {
        "path": str(request.url.path),
        "method": request.method,
        "client": request.client.host if request.client else "unknown",
        "error_type": type(exc).__name__,
    }
    log_error(exc, context=error_context)
    
    # Return error response
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

# Add security scheme to OpenAPI
app.openapi_schema = None  # Clear cache to regenerate

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi
    import json
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"schema-check","hypothesisId":"A","location":"planner_api.py:custom_openapi","message":"Checking /plan requestBody in schema","data":{"has_plan_path": "/plan" in openapi_schema.get("paths", {}), "plan_methods": list(openapi_schema.get("paths", {}).get("/plan", {}).keys()) if "/plan" in openapi_schema.get("paths", {}) else None},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token. Get a token from POST /token endpoint.",
        }
    }
    
    # #region agent log
    try:
        plan_post = openapi_schema.get("paths", {}).get("/plan", {}).get("post", {})
        has_request_body = "requestBody" in plan_post if plan_post else False
        request_body_content = plan_post.get("requestBody", {}).get("content", {}) if plan_post and "requestBody" in plan_post else {}
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"schema-check","hypothesisId":"B","location":"planner_api.py:custom_openapi","message":"Checking requestBody structure","data":{"has_request_body":has_request_body,"content_types":list(request_body_content.keys()),"request_body_keys":list(plan_post.get("requestBody", {}).keys()) if plan_post else None},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except Exception as e:
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"schema-check","hypothesisId":"B","location":"planner_api.py:custom_openapi","message":"Error checking requestBody","data":{"error":str(e)},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
    # #endregion
    
    # Add security requirement to all endpoints except public ones
    public_paths = {"/health", "/token", "/docs", "/openapi.json", "/redoc"}
    for path, path_item in openapi_schema.get("paths", {}).items():
        if path not in public_paths:
            for method in path_item.keys():
                if method.lower() != "options":
                    if "security" not in path_item[method]:
                        path_item[method]["security"] = [{"HTTPBearer": []}]
    
    # #region agent log
    try:
        final_plan_post = openapi_schema.get("paths", {}).get("/plan", {}).get("post", {})
        final_has_rb = "requestBody" in final_plan_post if final_plan_post else False
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"schema-check","hypothesisId":"E","location":"planner_api.py:custom_openapi","message":"Final schema check after security added","data":{"has_request_body_after":final_has_rb,"security_added":final_plan_post.get("security") if final_plan_post else None},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

planner_agent = PlannerAgent()
# Allow access to health check, token generation, and API documentation endpoints without authentication
register_auth_middleware(app, allow_paths={
    "/health", "/token", "/docs", "/openapi.json", "/redoc",
    "/frontend", "/frontend/*"
})

# CORS configuration — adjust origins as needed
allowed_origins_env = os.environ.get("PLANNER_ALLOWED_ORIGINS")
if allowed_origins_env:
    allow_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]
else:
    # Default to allowing localhost for development
    allow_origins = [
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", summary="Health check", response_model=dict)
def health() -> dict:
    """Lightweight health probe endpoint."""
    return {"status": "ok"}


@app.post(
    "/policies/reload",
    summary="Reload policies from configuration files",
    response_model=dict,
    tags=["administration"],
)
def reload_policies() -> dict:
    """
    Reload all policies from YAML configuration files.
    
    This endpoint allows you to update policies without restarting the server.
    Policies are reloaded from:
    - policies/assignment_policy.yaml
    - policies/priority_policy.yaml
    - policies/template_policy.yaml
    - policies/validation_policy.yaml
    
    Returns:
        Dictionary with reload status and loaded policy information
    """
    try:
        from policies import get_policy_loader
        from templates.template_loader import get_template_loader
        
        # Reload policies
        policy_loader = get_policy_loader()
        config = policy_loader.reload()
        
        # Reload templates
        template_loader = get_template_loader()
        templates = template_loader.load_all()
        
        # Update planner agent with new policies
        global planner_agent
        planner_agent = PlannerAgent(policy_loader=policy_loader, template_loader=template_loader)
        
        return {
            "status": "success",
            "message": "Policies and templates reloaded successfully",
            "policies": {
                "assignment": {
                    "role_map": config.assignment.role_map,
                    "default_role": config.assignment.default_role,
                },
                "priority": {
                    "priorities": config.priority.priorities,
                    "default_priority": config.priority.default_priority,
                },
                "template": {
                    "default_template": config.template.default_template,
                    "selection_rules": config.template.template_selection_rules,
                },
                "validation": {
                    "min_goal_length": config.validation.min_goal_length,
                    "min_feature_length": config.validation.min_feature_length,
                    "required_fields": config.validation.required_fields,
                    "max_constraints": config.validation.max_constraints,
                },
            },
            "templates": {
                "count": len(templates),
                "names": list(templates.keys()),
            },
        }
    except Exception as e:
        log_error(e, context={"endpoint": "/policies/reload", "action": "reload_policies"})
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload policies: {str(e)}"
        )


@app.post(
    "/token",
    summary="Generate an access token",
    response_model=dict,
    tags=["authentication"],
)
def generate_token(
    subject: str = "api-user",
    expires_minutes: int = 60,
) -> dict:
    """
    Generate a JWT access token for API authentication.
    
    This endpoint allows you to get a token for testing the API.
    Use the returned token in the Authorization header as: Bearer <token>
    
    Args:
        subject: User identifier (default: "api-user")
        expires_minutes: Token expiration time in minutes (default: 60)
    
    Returns:
        Dictionary with access_token and token_type
    """
    from api.authentication import create_access_token
    
    token = create_access_token(subject, expires_minutes=expires_minutes)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": expires_minutes,
        "subject": subject,
    }


@app.post(
    "/plan",
    summary="Generate a test plan",
    response_model=PlanResponse,
    responses={400: {"model": ErrorResponse}},
)
def create_plan(
    payload: PlanRequest,
    analyze_gaps: bool = Query(default=False, description="Whether to analyze coverage gaps after plan generation")
) -> PlanResponse:
    """
    Create a test plan for the given goal and feature.
    
    Uses templates to generate a comprehensive test plan with proper dependencies.
    The plan can be saved to the database for persistence and tracking.
    
    If analyze_gaps=True, the response will include coverage gap analysis in the summary.
    """
    import json
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"endpoint-call","hypothesisId":"D","location":"planner_api.py:create_plan","message":"Endpoint called with payload","data":{"has_goal":bool(payload.goal),"has_feature":bool(payload.feature),"template":payload.template_name,"analyze_gaps":analyze_gaps},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    if not payload.goal:
        raise HTTPException(status_code=400, detail="A goal is required.")
    if not payload.feature:
        raise HTTPException(status_code=400, detail="A feature is required.")

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        result = planner_agent.generate_test_plan(payload, session)
        
        # Analyze gaps if requested
        if analyze_gaps:
            try:
                gap_analysis = planner_agent.analyze_coverage_gaps(result.plan_id, session)
                # Append gap analysis to summary
                gap_summary = f" | Gap Analysis: {gap_analysis.missing_count} missing coverage task(s) out of {gap_analysis.total_tasks} total"
                if result.summary:
                    result.summary += gap_summary
                else:
                    result.summary = gap_summary.strip(" |")
            except Exception as gap_exc:
                # Log error but don't fail the plan generation
                log_error(gap_exc, context={"endpoint": "/plan", "action": "analyze_gaps", "plan_id": result.plan_id})
                # Optionally add a note to summary
                if result.summary:
                    result.summary += " | Gap analysis failed (see logs)"
        
        # #region agent log
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"endpoint-call","hypothesisId":"D","location":"planner_api.py:create_plan","message":"Plan generated successfully","data":{"plan_id":result.plan_id,"task_count":len(result.tasks),"analyze_gaps":analyze_gaps},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
        # #endregion
        return result
    except ValueError as exc:
        log_error(exc, context={"endpoint": "/plan", "action": "generate_test_plan"})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        log_error(exc, context={"endpoint": "/plan", "action": "generate_test_plan", "error_type": type(exc).__name__})
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {str(exc)}") from exc
    finally:
        session.close()


@app.post(
    "/assign_task",
    summary="Assign a task to an owner",
    response_model=AssignTaskResponse,
    responses={400: {"model": ErrorResponse}},
)
def assign_task(payload: AssignTaskRequest) -> AssignTaskResponse:
    """
    Assign a task to a developer or tester.
    
    Manually assigns a task to the specified owner.
    """
    if not payload.task_id:
        raise HTTPException(status_code=400, detail="task_id is required.")
    if not payload.owner:
        raise HTTPException(status_code=400, detail="owner is required.")

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        return planner_agent.assign_task(payload, session)
    except ValueError as exc:
        session.rollback()
        log_error(exc, context={"endpoint": "/assign_task", "task_id": payload.task_id})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        log_error(exc, context={"endpoint": "/assign_task", "task_id": payload.task_id, "error_type": type(exc).__name__})
        raise HTTPException(status_code=500, detail=f"Failed to assign task: {str(exc)}") from exc
    finally:
        session.close()


@app.post(
    "/assign_task/auto",
    summary="Auto-assign a task based on test type",
    response_model=AssignTaskResponse,
    responses={400: {"model": ErrorResponse}},
)
def auto_assign_task(payload: AssignTaskRequest) -> AssignTaskResponse:
    """
    Automatically assign a task based on its test type.
    
    Uses the TaskAssigner to automatically assign tasks:
    - unit/integration -> developer
    - e2e/exploratory -> tester
    - performance -> performance
    - security -> security
    """
    if not payload.task_id:
        raise HTTPException(status_code=400, detail="task_id is required.")

    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        return planner_agent.auto_assign_task(payload.task_id, session)
    except ValueError as exc:
        session.rollback()
        log_error(exc, context={"endpoint": "/assign_task/auto", "task_id": payload.task_id})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        log_error(exc, context={"endpoint": "/assign_task/auto", "task_id": payload.task_id, "error_type": type(exc).__name__})
        raise HTTPException(status_code=500, detail=f"Failed to auto-assign task: {str(exc)}") from exc
    finally:
        session.close()


@app.get(
    "/templates",
    summary="List available test plan templates",
    response_model=List[dict],
)
def list_plan_templates() -> List[dict]:
    """
    Get a list of all available test plan templates.
    
    Returns template names, descriptions, and task counts.
    """
    return list_templates()


@app.get(
    "/tasks/{task_id}",
    summary="Get task details with comments",
    response_model=TaskDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_task_details(task_id: str) -> TaskDetailResponse:
    """
    Get detailed information about a task, including all comments.
    """
    from database.postgresql_setup import get_sessionmaker
    from database.data_access_layer import TestTaskDAL
    from tasks.comments import get_comments
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        dal = TestTaskDAL(session)
        task = dal.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
        
        # Get comments for the task
        comments = get_comments(task_id, session=session)
        
        return TaskDetailResponse(
            id=task.id,
            description=task.description,
            test_type=task.test_type.value if hasattr(task.test_type, 'value') else str(task.test_type),
            status=task.status.value if hasattr(task.status, 'value') else str(task.status),
            owner=task.owner,
            coverage_status=task.coverage_status.value if hasattr(task.coverage_status, 'value') else str(task.coverage_status),
            dependencies=task.dependencies,
            comments=[
                CommentResponse(
                    id=comment.id,
                    task_id=comment.task_id,
                    user=comment.user,
                    comment_text=comment.comment_text,
                    timestamp=comment.timestamp.isoformat()
                )
                for comment in comments
            ]
        )
    finally:
        session.close()


@app.post(
    "/tasks/{task_id}/comments",
    summary="Add a comment to a task",
    response_model=CommentResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def add_task_comment(task_id: str, payload: AddCommentRequest) -> CommentResponse:
    """
    Add a comment to a specific task.
    
    The comment will be saved to the database and notifications will be sent
    to relevant users (task owner, mentioned users, etc.).
    """
    from database.postgresql_setup import get_sessionmaker
    from tasks.comments import add_comment
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        comment = add_comment(
            task_id=task_id,
            user=payload.user,
            comment_text=payload.comment_text,
            session=session
        )
        
        return CommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            user=comment.user,
            comment_text=comment.comment_text,
            timestamp=comment.timestamp.isoformat()
        )
    except ValueError as exc:
        session.rollback()
        log_error(exc, context={"endpoint": f"/tasks/{task_id}/comments", "action": "add_comment"})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        session.rollback()
        log_error(exc, context={"endpoint": f"/tasks/{task_id}/comments", "action": "add_comment", "task_id": task_id})
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        log_error(exc, context={"endpoint": f"/tasks/{task_id}/comments", "action": "add_comment", "error_type": type(exc).__name__})
        raise HTTPException(status_code=500, detail=f"Failed to add comment: {str(exc)}") from exc
    finally:
        session.close()


@app.get(
    "/tasks/{task_id}/comments",
    summary="Get comments for a task",
    response_model=List[CommentResponse],
    responses={404: {"model": ErrorResponse}},
)
def get_task_comments(task_id: str) -> List[CommentResponse]:
    """
    Get all comments for a specific task.
    
    Returns an empty array if the task has no comments.
    """
    from database.postgresql_setup import get_sessionmaker
    from database.data_access_layer import TestTaskDAL
    from tasks.comments import get_comments
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        # Verify task exists
        dal = TestTaskDAL(session)
        task = dal.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found.")
        
        # Get comments
        comments = get_comments(task_id, session=session)
        
        return [
            CommentResponse(
                id=comment.id,
                task_id=comment.task_id,
                user=comment.user,
                comment_text=comment.comment_text,
                timestamp=comment.timestamp.isoformat()
            )
            for comment in comments
        ]
    finally:
        session.close()


@app.get(
    "/tasks",
    summary="List all tasks",
    response_model=List[TaskItem],
)
def list_tasks(
    plan_id: Optional[str] = Query(None, description="Filter tasks by plan ID"),
    status: Optional[str] = Query(None, description="Filter tasks by status"),
    owner: Optional[str] = Query(None, description="Filter tasks by owner"),
) -> List[TaskItem]:
    """
    List all tasks with optional filtering.
    
    Query parameters:
    - plan_id: Filter tasks by plan ID (tasks with IDs starting with "{plan_id}-task")
    - status: Filter tasks by status (pending, in_progress, blocked, done)
    - owner: Filter tasks by owner
    """
    from database.postgresql_setup import get_sessionmaker
    from database.data_access_layer import TestTaskDAL
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        dal = TestTaskDAL(session)
        all_tasks = dal.list_tasks()
        
        # Apply filters
        filtered_tasks = all_tasks
        
        if plan_id:
            filtered_tasks = [t for t in filtered_tasks if t.id.startswith(f"{plan_id}-task")]
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status.value == status]
        
        if owner:
            filtered_tasks = [t for t in filtered_tasks if t.owner == owner]
        
        return [
            TaskItem(
                id=task.id,
                description=task.description,
                test_type=task.test_type.value,
                status=task.status.value,
            )
            for task in filtered_tasks
        ]
    finally:
        session.close()


@app.get(
    "/plans/{plan_id}",
    summary="Get plan details by plan ID",
    response_model=PlanDetailResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_plan_details(plan_id: str) -> PlanDetailResponse:
    """
    Get complete details of a plan by its plan_id.
    
    Returns the plan_id, feature, goal, all tasks, and summary.
    Use this to retrieve a plan after generating it.
    """
    from database.postgresql_setup import get_sessionmaker
    from database.data_access_layer import TestTaskDAL
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        dal = TestTaskDAL(session)
        all_tasks = dal.list_tasks()
        
        plan_tasks = [t for t in all_tasks if t.id.startswith(f"{plan_id}-task")]
        
        if not plan_tasks:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
        
        # Sort by task number for consistent ordering
        plan_tasks.sort(key=lambda t: t.id)
        
        # Extract feature and goal from first task description (if available)
        # Or use task IDs to infer
        feature = "Unknown"
        goal = "Unknown"
        
        # Try to extract from task descriptions
        if plan_tasks:
            first_desc = plan_tasks[0].description
            # Basic extraction - could be improved
            if "for " in first_desc:
                parts = first_desc.split("for ", 1)
                if len(parts) > 1:
                    feature = parts[1].split()[0] if parts[1] else "Unknown"
        
        task_items = [
            TaskItem(
                id=task.id,
                description=task.description,
                test_type=task.test_type.value,
                status=task.status.value,
            )
            for task in plan_tasks
        ]
        
        return PlanDetailResponse(
            plan_id=plan_id,
            feature=feature,
            goal=goal,
            tasks=task_items,
            summary=f"Plan {plan_id} with {len(task_items)} tasks",
        )
    finally:
        session.close()


@app.get(
    "/plans/{plan_id}/tasks",
    summary="Get all tasks for a plan",
    response_model=List[TaskItem],
    responses={404: {"model": ErrorResponse}},
)
def get_plan_tasks(plan_id: str) -> List[TaskItem]:
    """
    Get all tasks associated with a specific plan.
    
    Tasks are identified by IDs starting with "{plan_id}-task".
    """
    from database.postgresql_setup import get_sessionmaker
    from database.data_access_layer import TestTaskDAL
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        dal = TestTaskDAL(session)
        all_tasks = dal.list_tasks()
        
        plan_tasks = [t for t in all_tasks if t.id.startswith(f"{plan_id}-task")]
        
        if not plan_tasks:
            raise HTTPException(status_code=404, detail=f"No tasks found for plan {plan_id}.")
        
        # Sort by task number for consistent ordering
        plan_tasks.sort(key=lambda t: t.id)
        
        return [
            TaskItem(
                id=task.id,
                description=task.description,
                test_type=task.test_type.value,
                status=task.status.value,
            )
            for task in plan_tasks
        ]
    finally:
        session.close()


@app.get(
    "/plans/{plan_id}/coverage-gaps",
    summary="Get coverage gaps for a plan",
    response_model=CoverageGapResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_coverage_gaps(plan_id: str) -> CoverageGapResponse:
    """
    Analyze a plan to identify missing test coverage.
    
    Returns prioritized list of tasks with missing coverage,
    sorted by test type priority (E2E > integration > unit, etc.).
    """
    # #region agent log
    import json
    import os
    try:
        log_file = r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"planner_api.py:get_coverage_gaps","message":"Endpoint called - checking env vars","data":{"plan_id":plan_id,"POSTGRES_USER":os.environ.get("POSTGRES_USER","NOT_SET"),"POSTGRES_PASSWORD_SET":bool(os.environ.get("POSTGRES_PASSWORD")),"POSTGRES_PASSWORD_LEN":len(os.environ.get("POSTGRES_PASSWORD","")),"POSTGRES_HOST":os.environ.get("POSTGRES_HOST","NOT_SET"),"POSTGRES_DB":os.environ.get("POSTGRES_DB","NOT_SET")},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except Exception as log_err:
        # Even if logging fails, try to write to a simpler location
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\debug_fallback.log', 'a') as f2:
                f2.write(f"Logging error: {log_err}\n")
        except: pass
    # #endregion
    
    sessionmaker = get_sessionmaker()
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"planner_api.py:get_coverage_gaps","message":"About to create session","data":{"plan_id":plan_id},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    session = sessionmaker()
    
    # #region agent log
    try:
        with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"planner_api.py:get_coverage_gaps","message":"Session created, about to call analyze_coverage_gaps","data":{"plan_id":plan_id,"session_type":type(session).__name__},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
    except: pass
    # #endregion
    
    try:
        return planner_agent.analyze_coverage_gaps(plan_id, session)
    except ValueError as exc:
        session.rollback()
        # #region agent log
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"planner_api.py:get_coverage_gaps","message":"ValueError caught","data":{"error":str(exc)[:200]},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
        # #endregion
        log_error(exc, context={"endpoint": f"/plans/{plan_id}/coverage-gaps", "plan_id": plan_id})
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        session.rollback()
        # #region agent log
        try:
            with open(r'c:\Users\ASUS\Desktop\agents\Planner_1\.cursor\debug.log', 'a', encoding='utf-8') as f:
                error_str = str(exc)
                error_type = type(exc).__name__
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"E","location":"planner_api.py:get_coverage_gaps","message":"Exception caught in coverage gaps endpoint","data":{"error_type":error_type,"error_message":error_str[:300],"has_psycopg2":'psycopg2' in error_str,"has_password_auth":'password authentication' in error_str.lower(),"has_ipv6":'::1' in error_str or 'localhost' in error_str},"timestamp":int(__import__('time').time() * 1000)}) + '\n')
        except: pass
        # #endregion
        log_error(exc, context={"endpoint": f"/plans/{plan_id}/coverage-gaps", "plan_id": plan_id, "error_type": type(exc).__name__})
        raise HTTPException(status_code=500, detail=f"Failed to analyze coverage gaps: {str(exc)}") from exc
    finally:
        session.close()


@app.get(
    "/plans/{plan_id}/analysis",
    summary="Get comprehensive coverage analysis",
    response_model=CoverageAnalysisResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_coverage_analysis(plan_id: str) -> CoverageAnalysisResponse:
    """
    Get comprehensive coverage analysis for a plan.
    
    Includes:
    - Coverage breakdown by test type
    - Missing test types
    - Prioritized gap list
    - Overall coverage percentage
    """
    from collections import defaultdict
    
    sessionmaker = get_sessionmaker()
    session = sessionmaker()
    
    try:
        dal = TestTaskDAL(session)
        all_tasks = dal.list_tasks()
        
        # Filter tasks for this plan
        plan_tasks = [t for t in all_tasks if t.id.startswith(f"{plan_id}-task")]
        
        if not plan_tasks:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
        
        # Convert to TestTask objects
        test_tasks = [convert_task_model_to_test_task(model) for model in plan_tasks]
        
        # Group tasks by test type and calculate coverage
        coverage_by_type: Dict[str, Dict] = defaultdict(lambda: {"total": 0, "missing": 0, "complete": 0, "in_progress": 0, "not_started": 0})
        all_test_types = set(TestType)
        found_test_types = set()
        
        for task in test_tasks:
            test_type_str = task.test_type.value
            found_test_types.add(task.test_type)
            coverage_by_type[test_type_str]["total"] += 1
            
            if task.coverage_status == CoverageStatus.MISSING:
                coverage_by_type[test_type_str]["missing"] += 1
            elif task.coverage_status == CoverageStatus.COMPLETE:
                coverage_by_type[test_type_str]["complete"] += 1
            elif task.coverage_status == CoverageStatus.IN_PROGRESS:
                coverage_by_type[test_type_str]["in_progress"] += 1
            else:  # NOT_STARTED
                coverage_by_type[test_type_str]["not_started"] += 1
        
        # Find missing test types (types that should be covered but aren't)
        missing_test_types = [t.value for t in all_test_types if t not in found_test_types]
        
        # Use CoverageAnalyzer to get prioritized gaps
        analyzer = CoverageAnalyzer()
        prioritized_gaps = analyzer.prioritize_tests(test_tasks)
        
        gap_items = []
        for task in prioritized_gaps:
            priority = TEST_TYPE_PRIORITY.get(task.test_type, 0)
            gap_items.append(
                CoverageGapItem(
                    task_id=task.id,
                    description=task.description,
                    test_type=task.test_type.value,
                    priority=priority,
                    coverage_status=task.coverage_status.value if hasattr(task.coverage_status, 'value') else str(task.coverage_status),
                )
            )
        
        # Calculate overall coverage percentage
        total_tasks = len(test_tasks)
        if total_tasks > 0:
            complete_tasks = sum(1 for t in test_tasks if t.coverage_status == CoverageStatus.COMPLETE)
            coverage_percentage = (complete_tasks / total_tasks) * 100.0
        else:
            coverage_percentage = 0.0
        
        return CoverageAnalysisResponse(
            plan_id=plan_id,
            coverage_by_type=dict(coverage_by_type),
            missing_test_types=missing_test_types,
            prioritized_gaps=gap_items,
            coverage_percentage=round(coverage_percentage, 2),
        )
    except HTTPException:
        raise
    except Exception as exc:
        session.rollback()
        log_error(exc, context={"endpoint": f"/plans/{plan_id}/analysis", "plan_id": plan_id, "error_type": type(exc).__name__})
        raise HTTPException(status_code=500, detail=f"Failed to analyze coverage: {str(exc)}") from exc
    finally:
        session.close()


# Serve static files via API routes (allows them to work with auth middleware)
from fastapi.responses import FileResponse
import os

@app.get("/frontend/{path:path}")
def serve_frontend(path: str):
    """Serve frontend static files."""
    file_path = os.path.join("frontend", path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}


# If running directly: uvicorn api.planner_api:app --reload
if __name__ == "__main__":
    try:
        import uvicorn
        
        # Log startup
        print("Starting Planner Agent API...")
        print(f"Error logging enabled. Errors will be saved to: errors.log")
        
        uvicorn.run("api.planner_api:app", host="0.0.0.0", port=8080, reload=True)
    except ImportError as exc:  # pragma: no cover - guidance for local runs
        log_error(exc, context={"action": "startup", "error": "Missing uvicorn dependency"})
        raise SystemExit(
            "uvicorn is required to run the API. Install with `pip install uvicorn[standard] fastapi`."
        ) from exc
    except Exception as exc:
        log_error(exc, context={"action": "startup", "error_type": type(exc).__name__})
        raise

