# Quick Policy Reference

## Quick Start

1. **Edit Policy Files** in `policies/` directory
2. **Reload Policies** via API: `POST /policies/reload`
3. **No Restart Required** - Changes take effect immediately

## Policy File Locations

```
policies/
├── assignment_policy.yaml    # Who gets assigned what tasks
├── priority_policy.yaml       # Test execution order
├── template_policy.yaml       # Template defaults
└── validation_policy.yaml    # Input validation rules
```

## Common Changes

### Change Task Assignment

Edit `policies/assignment_policy.yaml`:
```yaml
role_map:
  unit: frontend_dev      # Changed
  e2e: qa_team            # Changed
```

Reload: `POST /policies/reload`

### Change Test Priorities

Edit `policies/priority_policy.yaml`:
```yaml
priorities:
  security: 10            # Higher priority
  unit: 2                # Changed from 1
```

Reload: `POST /policies/reload`

### Add Custom Template

Create `templates/templates/my_template.yaml`:
```yaml
name: my_template
description: My custom template
tasks:
  - description_template: "Test {feature}"
    test_type: UNIT
    dependencies: []
```

Reload: `POST /policies/reload`

## API Endpoint

**Reload Policies:**
```bash
POST http://localhost:8000/policies/reload
Authorization: Bearer <token>
```

## Test Types

Available test types for policies:
- `unit`
- `integration`
- `e2e`
- `exploratory`
- `performance`
- `security`

## Default Values

If policy files are missing, defaults are used:
- Assignment: unit/integration → developer, e2e/exploratory → tester
- Priorities: e2e=5, integration=4, unit=1
- Templates: basic, complex, minimal, full_coverage
- Validation: min_length=1

