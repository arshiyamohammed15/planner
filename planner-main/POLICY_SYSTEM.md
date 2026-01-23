# Policy-Driven Configuration System

The Planner Agent has been refactored to use a **dynamic, policy-driven configuration system** instead of hardcoded rules. All business rules can now be configured via YAML files without code changes.

## Overview

The agent now supports:
- **Policy-driven task assignment** - Configure role mappings via YAML
- **Policy-driven priorities** - Configure test type priorities via YAML
- **Policy-driven templates** - Load templates from YAML files
- **Policy-driven validation** - Configure validation rules via YAML
- **Hot reload** - Reload policies without restarting the server

## Policy Files

All policy files are located in the `policies/` directory:

### 1. `assignment_policy.yaml`
Defines how tasks are assigned to team members based on test type.

```yaml
role_map:
  unit: developer
  integration: developer
  e2e: tester
  exploratory: tester
  performance: performance
  security: security

default_role: null  # Leave unassigned if not found
```

### 2. `priority_policy.yaml`
Defines the priority order for test types in plan generation (higher = higher priority).

```yaml
priorities:
  e2e: 5
  integration: 4
  security: 4
  performance: 3
  exploratory: 2
  unit: 1

default_priority: 0
```

### 3. `template_policy.yaml`
Defines template selection rules and defaults.

```yaml
default_template: basic

template_selection_rules:
  high_risk: full_coverage
  quick_test: minimal
  standard: basic
  comprehensive: complex
```

### 4. `validation_policy.yaml`
Defines validation rules for API inputs.

```yaml
min_goal_length: 1
min_feature_length: 1

required_fields:
  - goal
  - feature

max_constraints: null  # null = unlimited
```

## Template Files

Templates can now be loaded from YAML files in `templates/templates/` directory.

### Template YAML Format

```yaml
name: custom_template
description: Custom test plan template
tasks:
  - description_template: "Write unit tests for {feature} core logic"
    test_type: UNIT
    dependencies: []
    owner: null  # optional
  - description_template: "Cover service and API flows for {feature}"
    test_type: INTEGRATION
    dependencies: ["task-1"]
    owner: developer
```

## API Endpoints

### Reload Policies

**POST** `/policies/reload`

Reload all policies and templates from configuration files without restarting the server.

**Response:**
```json
{
  "status": "success",
  "message": "Policies and templates reloaded successfully",
  "policies": {
    "assignment": {...},
    "priority": {...},
    "template": {...},
    "validation": {...}
  },
  "templates": {
    "count": 4,
    "names": ["basic", "complex", "minimal", "full_coverage"]
  }
}
```

## Architecture Changes

### Before (Hardcoded)

```python
# Hardcoded in TaskAssigner
role_map = {
    TestType.UNIT: "developer",
    TestType.E2E: "tester",
    # ...
}

# Hardcoded in TestPlanGenerator
priorities = {
    TestType.E2E: 5,
    TestType.UNIT: 1,
    # ...
}

# Hardcoded templates in Python code
TEMPLATE_REGISTRY = {
    "basic": BASIC_TEMPLATE,
    # ...
}
```

### After (Policy-Driven)

```python
# Loaded from YAML
policy_loader = get_policy_loader()
config = policy_loader.get_config()

# Use policy
assignee = config.assignment.get_role_for_test_type(test_type)
priority = config.priority.get_priority_for_test_type(test_type)
template = template_loader.get_template(template_name)
```

## Components

### PolicyLoader (`policies/policy_loader.py`)
- Loads policies from YAML files
- Provides `get_config()` to access current policies
- Supports `reload()` to refresh policies

### Policy Models (`policies/policy_models.py`)
- `AssignmentPolicy` - Task assignment rules
- `PriorityPolicy` - Test type priorities
- `TemplatePolicy` - Template selection rules
- `ValidationPolicy` - Input validation rules
- `PolicyConfig` - Complete policy configuration

### TemplateLoader (`templates/template_loader.py`)
- Loads templates from YAML files
- Falls back to hardcoded templates if YAML not found
- Provides `get_template()` and `list_templates()`

## Migration Guide

### Updating Assignment Rules

**Before:** Edit `tasks/task_assignment.py`

**After:** Edit `policies/assignment_policy.yaml`

```yaml
role_map:
  unit: frontend_developer  # Changed from "developer"
  e2e: qa_engineer          # Changed from "tester"
```

Then reload: `POST /policies/reload`

### Updating Priorities

**Before:** Edit `tasks/test_plan_generator.py`

**After:** Edit `policies/priority_policy.yaml`

```yaml
priorities:
  security: 10  # Increased priority
  unit: 2       # Changed from 1
```

Then reload: `POST /policies/reload`

### Adding Custom Templates

**Before:** Add Python code to `templates/test_plan_templates.py`

**After:** Create `templates/templates/my_template.yaml`

```yaml
name: my_template
description: My custom template
tasks:
  - description_template: "Test {feature}"
    test_type: UNIT
    dependencies: []
```

Then reload: `POST /policies/reload`

## Benefits

1. **No Code Changes** - Update behavior by editing YAML files
2. **Hot Reload** - Apply changes without restarting the server
3. **Version Control** - Track policy changes in Git
4. **Environment-Specific** - Different policies for dev/staging/prod
5. **Team Collaboration** - Non-developers can update policies
6. **Backward Compatible** - Falls back to defaults if YAML missing

## Default Behavior

If policy files are missing, the system falls back to the original hardcoded defaults:
- Assignment: unit/integration → developer, e2e/exploratory → tester
- Priorities: e2e=5, integration=4, unit=1, etc.
- Templates: basic, complex, minimal, full_coverage (hardcoded)
- Validation: min_length=1, required_fields=["goal", "feature"]

## Testing

Test policy changes:

1. Edit policy YAML file
2. Call `POST /policies/reload`
3. Test the affected functionality
4. Verify changes are applied

Example:
```bash
# Update assignment_policy.yaml
# Then reload
curl -X POST http://localhost:8000/policies/reload \
  -H "Authorization: Bearer <token>"

# Test assignment
curl -X POST http://localhost:8000/assign_task/auto \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task-1"}'
```

## File Structure

```
.
├── policies/
│   ├── __init__.py
│   ├── policy_models.py          # Policy data models
│   ├── policy_loader.py          # Policy loader
│   ├── assignment_policy.yaml    # Assignment rules
│   ├── priority_policy.yaml      # Priority rules
│   ├── template_policy.yaml      # Template rules
│   └── validation_policy.yaml    # Validation rules
├── templates/
│   ├── template_loader.py        # Template loader
│   ├── test_plan_templates.py    # Hardcoded templates (fallback)
│   └── templates/                # YAML template files (optional)
│       └── custom_template.yaml
└── api/
    └── planner_api.py            # API with policy reload endpoint
```

## Next Steps

1. **Customize Policies** - Edit YAML files to match your team's needs
2. **Create Templates** - Add custom templates in `templates/templates/`
3. **Set Up Environments** - Use different policy files for dev/staging/prod
4. **Automate Reload** - Set up CI/CD to reload policies after deployment

