# Quick Start Guide - Docker Deployment

## Quick Reference

### Local Development (Simplest)
```bash
docker run -d \
  --name planner-agent-dev \
  -p 8000:8000 \
  -e APP_ENV=development \
  -e PLANNER_API_SECRET=dev-secret-key \
  arshiyamohammed15/planner-agent:latest
```

### With Database
```bash
docker run -d \
  --name planner-agent-dev \
  -p 8000:8000 \
  -e APP_ENV=development \
  -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
  -e PLANNER_API_SECRET=dev-secret-key \
  arshiyamohammed15/planner-agent:latest
```

### Production
```bash
docker run -d \
  --name planner-agent-prod \
  -p 8000:8000 \
  --restart always \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql://user:password@host:5432/dbname \
  -e PLANNER_API_SECRET=your-strong-secret-key \
  -e PLANNER_ALLOWED_ORIGINS=https://yourdomain.com \
  arshiyamohammed15/planner-agent:latest
```

## Using Scripts

### Linux/Mac
```bash
# Development
chmod +x docker-run-dev.sh
./docker-run-dev.sh

# Staging
chmod +x docker-run-staging.sh
export POSTGRES_PASSWORD=your-password
export PLANNER_API_SECRET=your-secret
./docker-run-staging.sh

# Production
chmod +x docker-run-prod.sh
export POSTGRES_PASSWORD=your-password
export PLANNER_API_SECRET=your-secret
export PLANNER_ALLOWED_ORIGINS=https://yourdomain.com
./docker-run-prod.sh
```

### Windows PowerShell
```powershell
# Development
.\docker-run-dev.ps1
```

## Verify Deployment

```bash
# Check container status
docker ps --filter name=planner-agent

# View logs
docker logs planner-agent-dev

# Test health endpoint
curl http://localhost:8000/health
```

## Full Documentation

See `docker-run-commands.md` for complete documentation with all options and examples.

