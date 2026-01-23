# Planner Agent API - Comprehensive Test Plan

This test plan covers all scenarios for testing the Planner Agent API across different use cases, error conditions, and edge cases.

## Test Categories

1. **Authentication & Authorization Tests**
2. **Plan Generation Tests**
3. **Task Assignment Tests**
4. **Task Retrieval Tests**
5. **Comment Management Tests**
6. **Template Management Tests**
7. **Error Handling & Validation Tests**
8. **Edge Cases & Boundary Tests**
9. **Integration & Workflow Tests**
10. **Performance & Load Tests**

## Test Scenarios

### 1. Authentication & Authorization Tests

#### TC-AUTH-001: Generate Token Successfully
- **Endpoint:** `POST /token`
- **Input:** `subject=test_user&expires_minutes=60`
- **Expected:** 200 OK, returns access_token, token_type, expires_in_minutes, subject
- **Validation:** Token is valid JWT, contains subject claim

#### TC-AUTH-002: Generate Token with Custom Subject
- **Endpoint:** `POST /token?subject=developer&expires_minutes=30`
- **Expected:** 200 OK, subject matches input
- **Validation:** Token subject claim matches input

#### TC-AUTH-003: Access Protected Endpoint Without Token
- **Endpoint:** `POST /plan` (without Authorization header)
- **Expected:** 401 Unauthorized
- **Error Message:** "Authorization header missing or invalid"

#### TC-AUTH-004: Access Protected Endpoint with Invalid Token
- **Endpoint:** `POST /plan` with `Authorization: Bearer invalid_token_123`
- **Expected:** 401 Unauthorized
- **Error Message:** "Invalid token"

#### TC-AUTH-005: Access Protected Endpoint with Expired Token
- **Endpoint:** `POST /plan` with expired token
- **Expected:** 401 Unauthorized
- **Error Message:** "Token expired"

#### TC-AUTH-006: Access Public Endpoints Without Token
- **Endpoints:** `GET /health`, `POST /token`, `GET /docs`, `GET /openapi.json`
- **Expected:** 200 OK (no authentication required)

### 2. Plan Generation Tests

#### TC-PLAN-001: Generate Plan with Basic Template
- **Endpoint:** `POST /plan`
- **Input:** Valid request with `template_name: "basic"`
- **Expected:** 200 OK, returns plan_id, feature, goal, tasks array
- **Validation:** Plan contains 3 tasks (unit, integration, e2e)

#### TC-PLAN-002: Generate Plan with Complex Template
- **Endpoint:** `POST /plan`
- **Input:** Valid request with `template_name: "complex"`
- **Expected:** 200 OK
- **Validation:** Plan contains 6 tasks (unit, integration, e2e, exploratory, security, performance)

#### TC-PLAN-003: Generate Plan with Minimal Template
- **Endpoint:** `POST /plan`
- **Input:** Valid request with `template_name: "minimal"`
- **Expected:** 200 OK
- **Validation:** Plan contains 2 tasks

#### TC-PLAN-004: Generate Plan with Full Coverage Template
- **Endpoint:** `POST /plan`
- **Input:** Valid request with `template_name: "full_coverage"`
- **Expected:** 200 OK
- **Validation:** Plan contains comprehensive task set

#### TC-PLAN-005: Generate Plan with Default Template
- **Endpoint:** `POST /plan`
- **Input:** Valid request without template_name (should default to "basic")
- **Expected:** 200 OK
- **Validation:** Uses basic template

#### TC-PLAN-006: Generate Plan with Constraints
- **Endpoint:** `POST /plan`
- **Input:** Request with constraints array
- **Expected:** 200 OK
- **Validation:** Constraints are included in task descriptions

#### TC-PLAN-007: Generate Plan and Save to Database
- **Endpoint:** `POST /plan`
- **Input:** `save_to_database: true`
- **Expected:** 200 OK
- **Validation:** Plan is persisted, can be retrieved via GET /plans/{plan_id}

#### TC-PLAN-008: Generate Plan Without Saving to Database
- **Endpoint:** `POST /plan`
- **Input:** `save_to_database: false`
- **Expected:** 200 OK
- **Validation:** Plan is not persisted

#### TC-PLAN-009: Generate Plan with Missing Goal
- **Endpoint:** `POST /plan`
- **Input:** Request without `goal` field
- **Expected:** 422 Validation Error
- **Error Message:** "goal is required" or validation error

#### TC-PLAN-010: Generate Plan with Missing Feature
- **Endpoint:** `POST /plan`
- **Input:** Request without `feature` field
- **Expected:** 422 Validation Error
- **Error Message:** "feature is required"

#### TC-PLAN-011: Generate Plan with Blank Goal
- **Endpoint:** `POST /plan`
- **Input:** `goal: ""` or `goal: "   "`
- **Expected:** 422 Validation Error
- **Error Message:** "goal must not be empty"

#### TC-PLAN-012: Generate Plan with Blank Feature
- **Endpoint:** `POST /plan`
- **Input:** `feature: ""` or `feature: "   "`
- **Expected:** 422 Validation Error
- **Error Message:** "feature must not be empty"

#### TC-PLAN-013: Generate Plan with Invalid Template
- **Endpoint:** `POST /plan`
- **Input:** `template_name: "invalid_template"`
- **Expected:** 400 Bad Request
- **Error Message:** Template not found, lists available templates

#### TC-PLAN-014: Generate Plan with Long Strings
- **Endpoint:** `POST /plan`
- **Input:** Very long goal and feature strings (1000+ characters)
- **Expected:** 200 OK or 422 if length validation exists
- **Validation:** Handles long strings appropriately

#### TC-PLAN-015: Generate Plan with Special Characters
- **Endpoint:** `POST /plan`
- **Input:** Goal/feature with special characters: `!@#$%^&*()`, unicode, emojis
- **Expected:** 200 OK
- **Validation:** Special characters are handled correctly

### 3. Task Assignment Tests

#### TC-ASSIGN-001: Manual Task Assignment Success
- **Endpoint:** `POST /assign_task`
- **Input:** Valid task_id and owner
- **Expected:** 200 OK, returns task_id, owner, message
- **Validation:** Task is assigned to specified owner

#### TC-ASSIGN-002: Auto Task Assignment - Unit Test
- **Endpoint:** `POST /assign_task/auto`
- **Input:** task_id for unit test type
- **Expected:** 200 OK
- **Validation:** Task assigned to "developer" (based on test type)

#### TC-ASSIGN-003: Auto Task Assignment - E2E Test
- **Endpoint:** `POST /assign_task/auto`
- **Input:** task_id for e2e test type
- **Expected:** 200 OK
- **Validation:** Task assigned to "tester"

#### TC-ASSIGN-004: Auto Task Assignment - Security Test
- **Endpoint:** `POST /assign_task/auto`
- **Input:** task_id for security test type
- **Expected:** 200 OK
- **Validation:** Task assigned to "security"

#### TC-ASSIGN-005: Auto Task Assignment - Performance Test
- **Endpoint:** `POST /assign_task/auto`
- **Input:** task_id for performance test type
- **Expected:** 200 OK
- **Validation:** Task assigned to "performance"

#### TC-ASSIGN-006: Assign Task with Missing task_id
- **Endpoint:** `POST /assign_task`
- **Input:** Request without task_id
- **Expected:** 422 Validation Error
- **Error Message:** "task_id is required"

#### TC-ASSIGN-007: Assign Task with Missing owner
- **Endpoint:** `POST /assign_task`
- **Input:** Request without owner
- **Expected:** 422 Validation Error
- **Error Message:** "owner is required"

#### TC-ASSIGN-008: Assign Non-Existent Task
- **Endpoint:** `POST /assign_task`
- **Input:** task_id that doesn't exist
- **Expected:** 400 Bad Request or 404 Not Found
- **Error Message:** Task not found

#### TC-ASSIGN-009: Auto Assign Non-Existent Task
- **Endpoint:** `POST /assign_task/auto`
- **Input:** Invalid task_id
- **Expected:** 400 Bad Request or 404 Not Found

#### TC-ASSIGN-010: Reassign Task to Different Owner
- **Endpoint:** `POST /assign_task`
- **Input:** Task already assigned, assign to new owner
- **Expected:** 200 OK
- **Validation:** Owner is updated

### 4. Task Retrieval Tests

#### TC-TASK-001: Get Task Details Successfully
- **Endpoint:** `GET /tasks/{task_id}`
- **Input:** Valid task_id
- **Expected:** 200 OK, returns task details with comments
- **Validation:** All task fields present (id, description, test_type, status, owner, etc.)

#### TC-TASK-002: Get Non-Existent Task
- **Endpoint:** `GET /tasks/{task_id}`
- **Input:** Invalid task_id
- **Expected:** 404 Not Found
- **Error Message:** Task not found

#### TC-TASK-003: List All Tasks
- **Endpoint:** `GET /tasks`
- **Expected:** 200 OK, returns array of tasks
- **Validation:** Returns all tasks from database

#### TC-TASK-004: List Tasks with Filter - plan_id
- **Endpoint:** `GET /tasks?plan_id={plan_id}`
- **Expected:** 200 OK
- **Validation:** Returns only tasks for specified plan

#### TC-TASK-005: List Tasks with Filter - status
- **Endpoint:** `GET /tasks?status=pending`
- **Expected:** 200 OK
- **Validation:** Returns only tasks with specified status

#### TC-TASK-006: List Tasks with Filter - owner
- **Endpoint:** `GET /tasks?owner=developer`
- **Expected:** 200 OK
- **Validation:** Returns only tasks assigned to specified owner

#### TC-TASK-007: List Tasks with Multiple Filters
- **Endpoint:** `GET /tasks?plan_id={id}&status=pending&owner=developer`
- **Expected:** 200 OK
- **Validation:** Returns tasks matching all filters

#### TC-TASK-008: List Tasks - Empty Result
- **Endpoint:** `GET /tasks?status=completed`
- **Input:** No tasks with status "completed"
- **Expected:** 200 OK, returns empty array []

### 5. Comment Management Tests

#### TC-COMMENT-001: Add Comment to Task
- **Endpoint:** `POST /tasks/{task_id}/comments`
- **Input:** Valid task_id, user, comment_text
- **Expected:** 200 OK, returns comment with id, timestamp
- **Validation:** Comment is saved and associated with task

#### TC-COMMENT-002: Add Comment with Missing user
- **Endpoint:** `POST /tasks/{task_id}/comments`
- **Input:** Request without user field
- **Expected:** 422 Validation Error
- **Error Message:** "user is required" or validation error

#### TC-COMMENT-003: Add Comment with Missing comment_text
- **Endpoint:** `POST /tasks/{task_id}/comments`
- **Input:** Request without comment_text
- **Expected:** 422 Validation Error
- **Error Message:** "comment_text is required"

#### TC-COMMENT-004: Add Comment with Blank Fields
- **Endpoint:** `POST /tasks/{task_id}/comments`
- **Input:** user: "", comment_text: ""
- **Expected:** 422 Validation Error
- **Error Message:** Fields must not be empty

#### TC-COMMENT-005: Add Comment to Non-Existent Task
- **Endpoint:** `POST /tasks/{invalid_task_id}/comments`
- **Expected:** 404 Not Found
- **Error Message:** Task not found

#### TC-COMMENT-006: Get Comments for Task
- **Endpoint:** `GET /tasks/{task_id}/comments`
- **Expected:** 200 OK, returns array of comments
- **Validation:** Returns all comments for task, ordered by timestamp

#### TC-COMMENT-007: Get Comments for Task with No Comments
- **Endpoint:** `GET /tasks/{task_id}/comments`
- **Input:** Task with no comments
- **Expected:** 200 OK, returns empty array []

#### TC-COMMENT-008: Get Comments for Non-Existent Task
- **Endpoint:** `GET /tasks/{invalid_task_id}/comments`
- **Expected:** 404 Not Found

#### TC-COMMENT-009: Add Multiple Comments to Same Task
- **Endpoint:** `POST /tasks/{task_id}/comments` (multiple times)
- **Expected:** 200 OK each time
- **Validation:** All comments are saved and retrievable

#### TC-COMMENT-010: Add Comment with Long Text
- **Endpoint:** `POST /tasks/{task_id}/comments`
- **Input:** Very long comment_text (1000+ characters)
- **Expected:** 200 OK
- **Validation:** Long comment is handled correctly

### 6. Template Management Tests

#### TC-TEMPLATE-001: List Available Templates
- **Endpoint:** `GET /templates`
- **Expected:** 200 OK, returns array of templates
- **Validation:** Returns all available templates (basic, complex, minimal, full_coverage)

#### TC-TEMPLATE-002: Template Details Include Name and Description
- **Endpoint:** `GET /templates`
- **Expected:** 200 OK
- **Validation:** Each template has name and description fields

### 7. Plan Retrieval Tests

#### TC-PLAN-RET-001: Get Plan Details by ID
- **Endpoint:** `GET /plans/{plan_id}`
- **Input:** Valid plan_id
- **Expected:** 200 OK, returns plan details
- **Validation:** Returns plan_id, feature, goal, tasks, summary

#### TC-PLAN-RET-002: Get Non-Existent Plan
- **Endpoint:** `GET /plans/{invalid_plan_id}`
- **Expected:** 404 Not Found
- **Error Message:** Plan not found

#### TC-PLAN-RET-003: Get Tasks for Plan
- **Endpoint:** `GET /plans/{plan_id}/tasks`
- **Input:** Valid plan_id
- **Expected:** 200 OK, returns array of tasks
- **Validation:** Returns all tasks for the plan

#### TC-PLAN-RET-004: Get Tasks for Non-Existent Plan
- **Endpoint:** `GET /plans/{invalid_plan_id}/tasks`
- **Expected:** 404 Not Found

### 8. Error Handling & Validation Tests

#### TC-ERROR-001: Invalid JSON in Request Body
- **Endpoint:** `POST /plan`
- **Input:** Malformed JSON
- **Expected:** 422 Unprocessable Entity
- **Error Message:** JSON parsing error

#### TC-ERROR-002: Missing Content-Type Header
- **Endpoint:** `POST /plan`
- **Input:** Request without Content-Type: application/json
- **Expected:** 422 or 400 error

#### TC-ERROR-003: Wrong HTTP Method
- **Endpoint:** `GET /plan` (should be POST)
- **Expected:** 405 Method Not Allowed

#### TC-ERROR-004: Invalid Endpoint Path
- **Endpoint:** `GET /invalid_endpoint`
- **Expected:** 404 Not Found

#### TC-ERROR-005: Database Connection Error Handling
- **Scenario:** Database unavailable
- **Expected:** 500 Internal Server Error with appropriate message
- **Validation:** Error is logged to errors.log

### 9. Edge Cases & Boundary Tests

#### TC-EDGE-001: Empty Constraints Array
- **Endpoint:** `POST /plan`
- **Input:** `constraints: []`
- **Expected:** 200 OK
- **Validation:** Handles empty array gracefully

#### TC-EDGE-002: Null Constraints
- **Endpoint:** `POST /plan`
- **Input:** `constraints: null`
- **Expected:** 200 OK
- **Validation:** Null constraints are handled

#### TC-EDGE-003: Very Large Constraints Array
- **Endpoint:** `POST /plan`
- **Input:** Array with 100+ constraints
- **Expected:** 200 OK or appropriate limit
- **Validation:** System handles large arrays

#### TC-EDGE-004: Unicode Characters in Input
- **Endpoint:** `POST /plan`
- **Input:** Goal/feature with unicode characters (中文, العربية, etc.)
- **Expected:** 200 OK
- **Validation:** Unicode is handled correctly

#### TC-EDGE-005: SQL Injection Attempt
- **Endpoint:** `GET /tasks?plan_id=' OR '1'='1`
- **Expected:** 400 Bad Request or safe handling
- **Validation:** SQL injection is prevented

#### TC-EDGE-006: XSS Attempt in Comments
- **Endpoint:** `POST /tasks/{task_id}/comments`
- **Input:** `comment_text: "<script>alert('xss')</script>"`
- **Expected:** 200 OK (sanitized) or 400 Bad Request
- **Validation:** XSS is prevented or sanitized

### 10. Integration & Workflow Tests

#### TC-WORKFLOW-001: Complete Workflow - Generate Plan to Task Completion
1. Generate token
2. Create plan with complex template
3. Get plan details
4. List tasks for plan
5. Get task details
6. Add comment to task
7. Assign task manually
8. Auto-assign another task
9. List all tasks with filters
10. Get comments for task

#### TC-WORKFLOW-002: Multiple Plans Workflow
1. Create plan 1 (basic template)
2. Create plan 2 (complex template)
3. List tasks filtered by plan_id for plan 1
4. List tasks filtered by plan_id for plan 2
5. Verify tasks are correctly associated

#### TC-WORKFLOW-003: Task Assignment Workflow
1. Create plan
2. Get all tasks
3. Auto-assign all tasks
4. Verify assignments based on test types
5. Reassign some tasks manually
6. Verify updates

### 11. Performance & Load Tests

#### TC-PERF-001: Health Check Response Time
- **Endpoint:** `GET /health`
- **Expected:** Response time < 100ms
- **Validation:** Fast response for health checks

#### TC-PERF-002: Generate Multiple Plans Sequentially
- **Endpoint:** `POST /plan` (10 times)
- **Expected:** All succeed, reasonable response times
- **Validation:** No performance degradation

#### TC-PERF-003: Concurrent Requests
- **Scenario:** 10 simultaneous requests to `POST /plan`
- **Expected:** All requests handled correctly
- **Validation:** No race conditions, all plans created

#### TC-PERF-004: Large Plan Generation
- **Endpoint:** `POST /plan` with full_coverage template
- **Expected:** 200 OK within reasonable time
- **Validation:** Handles large plans efficiently

## Test Execution Checklist

### Pre-Test Setup
- [ ] API server is running (`.\start_api.ps1`)
- [ ] Database is accessible
- [ ] Postman or testing tool is ready
- [ ] Test data is prepared

### Test Execution Order
1. Authentication tests (TC-AUTH-001 to TC-AUTH-006)
2. Template tests (TC-TEMPLATE-001 to TC-TEMPLATE-002)
3. Plan generation tests (TC-PLAN-001 to TC-PLAN-015)
4. Plan retrieval tests (TC-PLAN-RET-001 to TC-PLAN-RET-004)
5. Task assignment tests (TC-ASSIGN-001 to TC-ASSIGN-010)
6. Task retrieval tests (TC-TASK-001 to TC-TASK-008)
7. Comment tests (TC-COMMENT-001 to TC-COMMENT-010)
8. Error handling tests (TC-ERROR-001 to TC-ERROR-005)
9. Edge cases (TC-EDGE-001 to TC-EDGE-006)
10. Workflow tests (TC-WORKFLOW-001 to TC-WORKFLOW-003)
11. Performance tests (TC-PERF-001 to TC-PERF-004)

### Test Results Tracking
- **Pass:** Test passed as expected
- **Fail:** Test failed, document issue
- **Skip:** Test skipped (prerequisites not met)
- **Block:** Test blocked (known issue)

## Test Data Requirements

### Valid Test Data
- Sample goals: "Ensure secure authentication", "Verify payment processing"
- Sample features: "User Authentication", "Checkout Flow"
- Sample constraints: ["Must comply with OAuth 2.0", "Rate limiting: 5/min"]
- Sample owners: "developer", "tester", "security-team"

### Invalid Test Data
- Empty strings
- Null values
- Very long strings
- Special characters
- SQL injection attempts
- XSS attempts

## Expected Test Coverage

- **Functional Coverage:** 100% of endpoints
- **Error Coverage:** All error scenarios
- **Edge Case Coverage:** Critical edge cases
- **Integration Coverage:** Complete workflows

## Test Tools

- **Postman:** Manual API testing
- **curl/PowerShell:** Command-line testing
- **Python requests:** Automated testing scripts
- **Swagger UI:** Interactive API testing

## Reporting

After test execution, document:
- Total tests: X
- Passed: Y
- Failed: Z
- Skipped: W
- Pass rate: (Y/X) * 100%
- Critical issues found
- Recommendations

