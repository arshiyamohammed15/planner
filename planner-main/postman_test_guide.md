# Postman Test Guide - Planner Agent API

Complete guide for testing all endpoints of the Planner Agent API using Postman.

## Table of Contents
1. [Setup & Authentication](#setup--authentication)
2. [GET Endpoints](#get-endpoints)
3. [POST Endpoints](#post-endpoints)
4. [Complete Test Scenarios](#complete-test-scenarios)
5. [Troubleshooting](#troubleshooting)

---

## Setup & Authentication

### Step 1: Get Access Token

**Request:**
- **Method:** `POST`
- **URL:** `http://localhost:8000/token?subject=your_username&expires_minutes=60`
- **Headers:** None required
- **Body:** None

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in_minutes": 60,
  "subject": "your_username"
}
```

**Postman Setup:**
1. Create new request
2. Set method to `POST`
3. Enter URL: `http://localhost:8000/token?subject=test_user&expires_minutes=60`
4. Click "Send"
5. Copy the `access_token` from response

### Step 2: Configure Authorization

**For All Protected Endpoints:**
1. Go to "Authorization" tab
2. Type: Select "Bearer Token"
3. Token: Paste your `access_token` (the long string)
4. This will automatically add `Authorization: Bearer <token>` header

**Alternative - Manual Header:**
- Go to "Headers" tab
- Add header:
  - Key: `Authorization`
  - Value: `Bearer <your_access_token>`

---

## GET Endpoints

### 1. Health Check

**Purpose:** Verify API is running

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/health`
- **Headers:** None required
- **Authorization:** Not required

**Expected Response:**
```json
{
  "status": "ok"
}
```

**Status Code:** `200 OK`

---

### 2. List Available Templates

**Purpose:** Get all available test plan templates

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/templates`
- **Headers:** None required
- **Authorization:** Not required

**Expected Response:**
```json
[
  {
    "name": "basic",
    "description": "Basic test plan with essential test types (unit, integration, e2e)",
    "task_count": 3
  },
  {
    "name": "complex",
    "description": "Complex test plan with comprehensive coverage including security and performance",
    "task_count": 6
  },
  {
    "name": "minimal",
    "description": "Minimal test plan with just unit and integration tests",
    "task_count": 2
  },
  {
    "name": "full_coverage",
    "description": "Full coverage test plan with all test types",
    "task_count": 6
  }
]
```

**Status Code:** `200 OK`

---

### 3. List All Tasks

**Purpose:** Get all tasks with optional filtering

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/tasks`
- **Query Parameters (Optional):**
  - `plan_id`: Filter by plan ID (e.g., `plan-abc12345`)
  - `status`: Filter by status (`pending`, `in_progress`, `blocked`, `done`)
  - `owner`: Filter by owner name
- **Authorization:** Required (Bearer Token)

**Example URLs:**
- All tasks: `http://localhost:8000/tasks`
- Filter by plan: `http://localhost:8000/tasks?plan_id=plan-abc12345`
- Filter by status: `http://localhost:8000/tasks?status=pending`
- Filter by owner: `http://localhost:8000/tasks?owner=developer`
- Combined filters: `http://localhost:8000/tasks?plan_id=plan-abc12345&status=pending`

**Expected Response:**
```json
[
  {
    "id": "plan-abc12345-task-1",
    "description": "Write unit tests for Checkout core logic",
    "test_type": "unit",
    "status": "pending"
  },
  {
    "id": "plan-abc12345-task-2",
    "description": "Cover service and API flows for Checkout",
    "test_type": "integration",
    "status": "pending"
  }
]
```

**Status Code:** `200 OK`

---

### 4. Get Plan Details

**Purpose:** Get complete details of a plan by plan_id

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/plans/{plan_id}`
- **Path Parameter:**
  - `plan_id`: The plan ID (e.g., `plan-abc12345`)
- **Authorization:** Required (Bearer Token)

**Example URL:**
```
http://localhost:8000/plans/plan-abc12345
```

**Expected Response:**
```json
{
  "plan_id": "plan-abc12345",
  "feature": "Checkout",
  "goal": "Ensure checkout flow reliability",
  "tasks": [
    {
      "id": "plan-abc12345-task-1",
      "description": "Write unit tests for Checkout core logic",
      "test_type": "unit",
      "status": "pending"
    },
    {
      "id": "plan-abc12345-task-2",
      "description": "Cover service and API flows for Checkout",
      "test_type": "integration",
      "status": "pending"
    }
  ],
  "summary": "Plan plan-abc12345 with 3 tasks",
  "created_at": null
}
```

**Status Code:** `200 OK`

**Error Response (404):**
```json
{
  "detail": "Plan plan-abc12345 not found."
}
```

---

### 5. Get Tasks for a Plan

**Purpose:** Get all tasks associated with a specific plan

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/plans/{plan_id}/tasks`
- **Path Parameter:**
  - `plan_id`: The plan ID (e.g., `plan-abc12345`)
- **Authorization:** Required (Bearer Token)

**Example URL:**
```
http://localhost:8000/plans/plan-abc12345/tasks
```

**Expected Response:**
```json
[
  {
    "id": "plan-abc12345-task-1",
    "description": "Write unit tests for Checkout core logic",
    "test_type": "unit",
    "status": "pending"
  },
  {
    "id": "plan-abc12345-task-2",
    "description": "Cover service and API flows for Checkout",
    "test_type": "integration",
    "status": "pending"
  }
]
```

**Status Code:** `200 OK`

**Error Response (404):**
```json
{
  "detail": "No tasks found for plan plan-abc12345."
}
```

---

### 6. Get Task Details

**Purpose:** Get detailed information about a task, including comments

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/tasks/{task_id}`
- **Path Parameter:**
  - `task_id`: The task ID (e.g., `plan-abc12345-task-1`)
- **Authorization:** Required (Bearer Token)

**Example URL:**
```
http://localhost:8000/tasks/plan-abc12345-task-1
```

**Expected Response:**
```json
{
  "id": "plan-abc12345-task-1",
  "description": "Write unit tests for Checkout core logic",
  "test_type": "unit",
  "status": "pending",
  "owner": "developer",
  "coverage_status": "not_started",
  "dependencies": [],
  "comments": [
    {
      "id": 1,
      "task_id": "plan-abc12345-task-1",
      "user": "john.doe",
      "comment_text": "This task needs more test coverage",
      "timestamp": "2026-01-15T12:00:00"
    }
  ]
}
```

**Status Code:** `200 OK`

**Error Response (404):**
```json
{
  "detail": "Task plan-abc12345-task-1 not found."
}
```

---

### 7. Get Task Comments

**Purpose:** Get all comments for a specific task

**Request:**
- **Method:** `GET`
- **URL:** `http://localhost:8000/tasks/{task_id}/comments`
- **Path Parameter:**
  - `task_id`: The task ID (e.g., `plan-abc12345-task-1`)
- **Authorization:** Required (Bearer Token)

**Example URL:**
```
http://localhost:8000/tasks/plan-abc12345-task-1/comments
```

**Expected Response (with comments):**
```json
[
  {
    "id": 1,
    "task_id": "plan-abc12345-task-1",
    "user": "john.doe",
    "comment_text": "This task needs more test coverage",
    "timestamp": "2026-01-15T12:00:00"
  },
  {
    "id": 2,
    "task_id": "plan-abc12345-task-1",
    "user": "jane.smith",
    "comment_text": "I'll work on this next week",
    "timestamp": "2026-01-15T12:30:00"
  }
]
```

**Expected Response (no comments):**
```json
[]
```

**Status Code:** `200 OK`

**Error Response (404):**
```json
{
  "detail": "Task plan-abc12345-task-1 not found."
}
```

---

## POST Endpoints

### 1. Generate Test Plan

**Purpose:** Generate a test plan with tasks

**Request:**
- **Method:** `POST`
- **URL:** `http://localhost:8000/plan`
- **Headers:**
  - `Content-Type: application/json`
- **Authorization:** Required (Bearer Token)
- **Body (JSON):**

**Basic Request:**
```json
{
  "goal": "Ensure checkout flow reliability",
  "feature": "Checkout",
  "template_name": "basic",
  "save_to_database": true
}
```

**Full Request with All Fields:**
```json
{
  "goal": "Ensure checkout flow reliability",
  "feature": "Checkout",
  "constraints": ["PCI compliance", "limited staging data"],
  "owner": "qa-team",
  "template_name": "basic",
  "save_to_database": true
}
```

**Postman Setup:**
1. Method: `POST`
2. URL: `http://localhost:8000/plan`
3. Go to "Body" tab
4. Select "raw" and "JSON" from dropdown
5. Paste the JSON above
6. Click "Send"

**Expected Response:**
```json
{
  "plan_id": "plan-abc12345",
  "feature": "Checkout",
  "goal": "Ensure checkout flow reliability",
  "tasks": [
    {
      "id": "plan-abc12345-task-1",
      "description": "Write unit tests for Checkout core logic",
      "test_type": "unit",
      "status": "pending"
    },
    {
      "id": "plan-abc12345-task-2",
      "description": "Cover service and API flows for Checkout",
      "test_type": "integration",
      "status": "pending"
    },
    {
      "id": "plan-abc12345-task-3",
      "description": "Validate user journeys for Checkout: Ensure checkout flow reliability",
      "test_type": "e2e",
      "status": "pending"
    }
  ],
  "summary": "3 tasks generated from 'basic' template; feature: Checkout; goal: Ensure checkout flow reliability; saved 3 tasks to database"
}
```

**Status Code:** `200 OK`

**Error Responses:**

**400 - Missing Required Fields:**
```json
{
  "detail": "A goal is required."
}
```

**400 - Invalid Template:**
```json
{
  "detail": "Template 'invalid_template' not found. Available templates: basic, complex, minimal, full_coverage"
}
```

**Template Options:**
- `"basic"` - 3 tasks (unit, integration, e2e)
- `"complex"` - 6 tasks (includes security, performance)
- `"minimal"` - 2 tasks (unit, integration)
- `"full_coverage"` - 6 tasks (all test types)

---

### 2. Manually Assign Task

**Purpose:** Assign a task to a specific owner

**Request:**
- **Method:** `POST`
- **URL:** `http://localhost:8000/assign_task`
- **Headers:**
  - `Content-Type: application/json`
- **Authorization:** Required (Bearer Token)
- **Body (JSON):**
```json
{
  "task_id": "plan-abc12345-task-1",
  "owner": "john.doe"
}
```

**Postman Setup:**
1. Method: `POST`
2. URL: `http://localhost:8000/assign_task`
3. Body tab → raw → JSON
4. Paste the JSON above (replace with your actual task_id)
5. Click "Send"

**Expected Response:**
```json
{
  "task_id": "plan-abc12345-task-1",
  "owner": "john.doe",
  "message": "Task plan-abc12345-task-1 assigned to john.doe."
}
```

**Status Code:** `200 OK`

**Error Responses:**

**400 - Missing Fields:**
```json
{
  "detail": "task_id is required."
}
```

**400 - Task Not Found:**
```json
{
  "detail": "Task plan-abc12345-task-1 not found."
}
```

---

### 3. Auto-Assign Task

**Purpose:** Automatically assign task based on test type

**Request:**
- **Method:** `POST`
- **URL:** `http://localhost:8000/assign_task/auto`
- **Headers:**
  - `Content-Type: application/json`
- **Authorization:** Required (Bearer Token)
- **Body (JSON):**
```json
{
  "task_id": "plan-abc12345-task-1",
  "owner": "dummy"
}
```

**Note:** The `owner` field is ignored - assignment is automatic based on test type:
- `unit` / `integration` → `"developer"`
- `e2e` / `exploratory` → `"tester"`
- `performance` → `"performance"`
- `security` → `"security"`

**Postman Setup:**
1. Method: `POST`
2. URL: `http://localhost:8000/assign_task/auto`
3. Body tab → raw → JSON
4. Paste the JSON above (replace with your actual task_id)
5. Click "Send"

**Expected Response:**
```json
{
  "task_id": "plan-abc12345-task-1",
  "owner": "developer",
  "message": "Task plan-abc12345-task-1 automatically assigned to developer based on test type."
}
```

**Status Code:** `200 OK`

**Error Responses:**

**400 - Task Not Found:**
```json
{
  "detail": "Task plan-abc12345-task-1 not found."
}
```

**400 - Cannot Auto-Assign:**
```json
{
  "detail": "Could not auto-assign task plan-abc12345-task-1. Task not found or test type not mapped."
}
```

---

### 4. Add Comment to Task

**Purpose:** Add a comment to a task

**Request:**
- **Method:** `POST`
- **URL:** `http://localhost:8000/tasks/{task_id}/comments`
- **Path Parameter:**
  - `task_id`: The task ID (e.g., `plan-abc12345-task-1`)
- **Headers:**
  - `Content-Type: application/json`
- **Authorization:** Required (Bearer Token)
- **Body (JSON):**
```json
{
  "user": "john.doe",
  "comment_text": "This task needs more test coverage for edge cases"
}
```

**Example URL:**
```
http://localhost:8000/tasks/plan-abc12345-task-1/comments
```

**Postman Setup:**
1. Method: `POST`
2. URL: `http://localhost:8000/tasks/plan-abc12345-task-1/comments`
3. Body tab → raw → JSON
4. Paste the JSON above
5. Click "Send"

**Expected Response:**
```json
{
  "id": 1,
  "task_id": "plan-abc12345-task-1",
  "user": "john.doe",
  "comment_text": "This task needs more test coverage for edge cases",
  "timestamp": "2026-01-15T12:00:00"
}
```

**Status Code:** `200 OK`

**Error Responses:**

**400 - Missing Fields:**
```json
{
  "detail": "user cannot be empty"
}
```

**404 - Task Not Found:**
```json
{
  "detail": "Task with id 'plan-abc12345-task-1' does not exist"
}
```

---

## Complete Test Scenarios

### Scenario 1: Complete Workflow - Generate Plan and View Tasks

**Step 1: Get Token**
```
POST http://localhost:8000/token?subject=test_user&expires_minutes=60
```
- Copy `access_token`

**Step 2: Generate Plan**
```
POST http://localhost:8000/plan
Authorization: Bearer <token>
Body:
{
  "goal": "Test payment processing",
  "feature": "Payment",
  "template_name": "basic",
  "save_to_database": true
}
```
- Copy `plan_id` from response (e.g., `plan-abc12345`)

**Step 3: View Plan Details**
```
GET http://localhost:8000/plans/plan-abc12345
Authorization: Bearer <token>
```

**Step 4: View Plan Tasks**
```
GET http://localhost:8000/plans/plan-abc12345/tasks
Authorization: Bearer <token>
```

**Step 5: Get Task Details**
```
GET http://localhost:8000/tasks/plan-abc12345-task-1
Authorization: Bearer <token>
```

---

### Scenario 2: Task Assignment Workflow

**Prerequisites:** Have a plan with tasks (from Scenario 1)

**Step 1: View Unassigned Tasks**
```
GET http://localhost:8000/tasks?status=pending
Authorization: Bearer <token>
```

**Step 2: Auto-Assign a Task**
```
POST http://localhost:8000/assign_task/auto
Authorization: Bearer <token>
Body:
{
  "task_id": "plan-abc12345-task-1",
  "owner": "dummy"
}
```

**Step 3: Verify Assignment**
```
GET http://localhost:8000/tasks/plan-abc12345-task-1
Authorization: Bearer <token>
```
- Check that `owner` field is now set

**Step 4: Manually Reassign (Optional)**
```
POST http://localhost:8000/assign_task
Authorization: Bearer <token>
Body:
{
  "task_id": "plan-abc12345-task-1",
  "owner": "john.doe"
}
```

---

### Scenario 3: Comment Workflow

**Prerequisites:** Have a task (from Scenario 1)

**Step 1: Add Comment**
```
POST http://localhost:8000/tasks/plan-abc12345-task-1/comments
Authorization: Bearer <token>
Body:
{
  "user": "john.doe",
  "comment_text": "Starting work on this task"
}
```

**Step 2: View Comments**
```
GET http://localhost:8000/tasks/plan-abc12345-task-1/comments
Authorization: Bearer <token>
```

**Step 3: Add Another Comment**
```
POST http://localhost:8000/tasks/plan-abc12345-task-1/comments
Authorization: Bearer <token>
Body:
{
  "user": "jane.smith",
  "comment_text": "I'll review this after completion"
}
```

**Step 4: View All Comments**
```
GET http://localhost:8000/tasks/plan-abc12345-task-1/comments
Authorization: Bearer <token>
```
- Should see both comments

**Step 5: View Task with Comments**
```
GET http://localhost:8000/tasks/plan-abc12345-task-1
Authorization: Bearer <token>
```
- Comments are included in the response

---

### Scenario 4: Filtering and Searching

**Step 1: List All Tasks**
```
GET http://localhost:8000/tasks
Authorization: Bearer <token>
```

**Step 2: Filter by Plan**
```
GET http://localhost:8000/tasks?plan_id=plan-abc12345
Authorization: Bearer <token>
```

**Step 3: Filter by Status**
```
GET http://localhost:8000/tasks?status=pending
Authorization: Bearer <token>
```

**Step 4: Filter by Owner**
```
GET http://localhost:8000/tasks?owner=developer
Authorization: Bearer <token>
```

**Step 5: Combined Filters**
```
GET http://localhost:8000/tasks?plan_id=plan-abc12345&status=pending&owner=developer
Authorization: Bearer <token>
```

---

### Scenario 5: Different Template Types

**Test Basic Template:**
```
POST http://localhost:8000/plan
Authorization: Bearer <token>
Body:
{
  "goal": "Test basic functionality",
  "feature": "Login",
  "template_name": "basic",
  "save_to_database": true
}
```
- Expected: 3 tasks (unit, integration, e2e)

**Test Complex Template:**
```
POST http://localhost:8000/plan
Authorization: Bearer <token>
Body:
{
  "goal": "Comprehensive testing",
  "feature": "Payment",
  "template_name": "complex",
  "save_to_database": true
}
```
- Expected: 6 tasks (includes security, performance)

**Test Minimal Template:**
```
POST http://localhost:8000/plan
Authorization: Bearer <token>
Body:
{
  "goal": "Quick testing",
  "feature": "Search",
  "template_name": "minimal",
  "save_to_database": true
}
```
- Expected: 2 tasks (unit, integration)

**Test Full Coverage Template:**
```
POST http://localhost:8000/plan
Authorization: Bearer <token>
Body:
{
  "goal": "Complete coverage",
  "feature": "Checkout",
  "template_name": "full_coverage",
  "save_to_database": true
}
```
- Expected: 6 tasks (all test types)

---

## Troubleshooting

### Common Issues

**1. 401 Unauthorized Error**
- **Problem:** Missing or invalid token
- **Solution:** 
  - Get a new token: `POST http://localhost:8000/token`
  - Make sure "Bearer Token" is selected in Authorization tab
  - Verify token is pasted correctly (no extra spaces)

**2. 404 Not Found**
- **Problem:** Invalid plan_id or task_id
- **Solution:**
  - Verify the ID exists by listing tasks first
  - Check for typos in the ID
  - Make sure you're using plan_id (not task_id) for plan endpoints

**3. 400 Bad Request**
- **Problem:** Missing required fields or invalid data
- **Solution:**
  - Check request body has all required fields
  - Verify JSON is valid (proper quotes, commas, braces)
  - Check template_name is one of: basic, complex, minimal, full_coverage

**4. Empty Response Array**
- **Problem:** No data exists
- **Solution:**
  - This is normal if no tasks/comments exist yet
  - Generate a plan first to create tasks
  - Add comments to see them in responses

**5. Server Not Responding**
- **Problem:** API server is not running
- **Solution:**
  - Check server is running: `GET http://localhost:8000/health`
  - Start server: `python -m uvicorn api.planner_api:app --host 0.0.0.0 --port 8000 --reload`
  - Verify database connection

### Postman Tips

**1. Save Token as Environment Variable**
- Create environment in Postman
- Add variable: `token` = `<your_access_token>`
- Use `{{token}}` in Authorization → Bearer Token

**2. Create Collection**
- Organize all requests in a collection
- Share collection with team
- Use collection variables for base URL

**3. Use Pre-request Scripts**
- Automatically get token before each request
- Store token in environment variable

**4. Save Examples**
- Save successful responses as examples
- Use for documentation and testing

---

## Quick Reference

### No Authentication Required
- `GET /health`
- `GET /templates`
- `POST /token`

### Authentication Required
- All other endpoints need Bearer Token

### Common Status Codes
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `404 Not Found` - Resource doesn't exist
- `422 Validation Error` - Invalid data format
- `500 Internal Server Error` - Server error

### ID Formats
- **Plan ID:** `plan-{8-hex-chars}` (e.g., `plan-abc12345`)
- **Task ID:** `plan-{8-hex-chars}-task-{number}` (e.g., `plan-abc12345-task-1`)

---

## Summary

This guide covers all endpoints of the Planner Agent API:
- ✅ Authentication (token generation)
- ✅ Plan generation with different templates
- ✅ Task listing and filtering
- ✅ Task assignment (manual and auto)
- ✅ Comment management
- ✅ Plan and task details retrieval

Use this guide to test all functionality of your Planner Agent API in Postman!

