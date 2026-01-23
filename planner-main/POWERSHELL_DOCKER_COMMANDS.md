# PowerShell Docker Commands Guide

## Root Cause of the Error

**Problem:** Using bash syntax (backslashes `\`) in PowerShell

**Why it fails:**
- Bash uses `\` for line continuation
- PowerShell uses `` ` `` (backtick) for line continuation
- PowerShell interprets each line as a separate command when using `\`

## Correct Syntax for PowerShell

### Option 1: Single-Line Command (Recommended for PowerShell)

```powershell
docker run -d --name planner-agent-dev -p 8000:8000 -e APP_ENV=development -e PLANNER_API_SECRET=dev-secret-key-change-me arshiyamohammed15/planner-agent:latest
```

### Option 2: Multi-Line with Backticks

```powershell
docker run -d `
  --name planner-agent-dev `
  -p 8000:8000 `
  -e APP_ENV=development `
  -e PLANNER_API_SECRET=dev-secret-key-change-me `
  arshiyamohammed15/planner-agent:latest
```

**Important:** 
- Use backticks (`` ` ``) not backslashes (`\`)
- No spaces after the backtick
- Backtick must be the last character on the line

### Option 3: Use PowerShell Scripts

```powershell
# Simple version
.\docker-run-simple.ps1

# Full version with all options
.\docker-run-dev.ps1
```

## Common Examples

### Basic Development
```powershell
docker run -d --name planner-agent-dev -p 8000:8000 -e APP_ENV=development -e PLANNER_API_SECRET=dev-secret arshiyamohammed15/planner-agent:latest
```

### With Database
```powershell
docker run -d --name planner-agent-dev -p 8000:8000 -e APP_ENV=development -e DATABASE_URL=postgresql://user:pass@host:5432/db -e PLANNER_API_SECRET=dev-secret arshiyamohammed15/planner-agent:latest
```

### Multi-line with Database
```powershell
docker run -d `
  --name planner-agent-dev `
  -p 8000:8000 `
  -e APP_ENV=development `
  -e POSTGRES_USER=postgres `
  -e POSTGRES_PASSWORD=postgres `
  -e POSTGRES_HOST=localhost `
  -e POSTGRES_PORT=5432 `
  -e POSTGRES_DB=planner_dev `
  -e PLANNER_API_SECRET=dev-secret `
  arshiyamohammed15/planner-agent:latest
```

## Key Differences: Bash vs PowerShell

| Feature | Bash | PowerShell |
|---------|------|------------|
| Line continuation | `\` (backslash) | `` ` `` (backtick) |
| Variable syntax | `$VAR` or `${VAR}` | `$VAR` or `$env:VAR` |
| Default values | `${VAR:-default}` | `$(if ($VAR) { $VAR } else { "default" })` |
| Script extension | `.sh` | `.ps1` |

## Troubleshooting

### Error: "invalid reference format"
- **Cause:** Using `\` instead of `` ` `` in PowerShell
- **Fix:** Use backticks or single-line command

### Error: "-e : The term '-e' is not recognized"
- **Cause:** Line continuation failed, PowerShell trying to execute `-e` as command
- **Fix:** Use backticks or single-line command

### Error: "The term '...' is not recognized"
- **Cause:** Command split incorrectly due to wrong line continuation
- **Fix:** Use backticks or single-line command

## Best Practices for PowerShell

1. **Prefer single-line commands** for simplicity
2. **Use scripts** (`.ps1` files) for complex deployments
3. **Use backticks** if you need multi-line (no space after backtick!)
4. **Test commands** in PowerShell ISE or terminal before using in scripts

## Quick Reference

```powershell
# Start container
docker run -d --name planner-agent-dev -p 8000:8000 -e APP_ENV=development -e PLANNER_API_SECRET=dev-secret arshiyamohammed15/planner-agent:latest

# Check status
docker ps --filter name=planner-agent-dev

# View logs
docker logs planner-agent-dev

# Stop container
docker stop planner-agent-dev

# Remove container
docker rm planner-agent-dev
```

