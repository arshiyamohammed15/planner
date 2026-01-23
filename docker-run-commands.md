# Docker Run Commands for Deployment

This document provides Docker run commands for deploying the Planner Agent in different environments.

## Image Information

- **Docker Hub Image:** `arshiyamohammed15/planner-agent:latest`
- **Container Port:** `8000`
- **Default Host Port:** `8000`

---

## Environment Variables Reference

### Database Configuration
- `POSTGRES_USER` - PostgreSQL username (default: `postgres`)
- `POSTGRES_PASSWORD` - PostgreSQL password (default: `postgres`)
- `POSTGRES_HOST` - PostgreSQL host (default: `localhost`)
- `POSTGRES_PORT` - PostgreSQL port (default: `5432`)
- `POSTGRES_DB` - PostgreSQL database name (default: `planner`)
- `DATABASE_URL` - Full database connection URL (alternative to individual vars)

### Application Configuration
- `APP_ENV` or `ENVIRONMENT` - Environment name: `development`, `staging`, or `production`
- `SQLALCHEMY_ECHO` - Enable SQL query logging (`true`/`false` or empty)

### Security & Authentication
- `PLANNER_API_SECRET` - Secret key for JWT token generation (required in production)
- `PLANNER_ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins

### API Keys
- `SERVICE1_API_KEY` - API key for service 1
- `SERVICE2_API_KEY` - API key for service 2

### AWS Secrets (Optional)
- `AWS_REGION` or `AWS_DEFAULT_REGION` - AWS region for secrets manager
- `CONFIG_SECRET_NAME` - AWS Secrets Manager secret name

---

## 1. Local Development

### Basic Local Development (No Database)
```bash
docker run -d \
  --name planner-agent-dev \
  -p 8000:8000 \
  -e APP_ENV=development \
  -e SQLALCHEMY_ECHO=true \
  -e PLANNER_API_SECRET=dev-secret-key-change-me \
  -e PLANNER_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080 \
  arshiyamohammed15/planner-agent:latest
```

### Local Development with Local PostgreSQL
```bash
docker run -d \
  --name planner-agent-dev \
  -p 8000:8000 \
  --network host \
  -e APP_ENV=development \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_HOST=localhost \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=planner_dev \
  -e SQLALCHEMY_ECHO=true \
  -e PLANNER_API_SECRET=dev-secret-key-change-me \
  -e PLANNER_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080 \
  arshiyamohammed15/planner-agent:latest
```

### Local Development with Docker Network PostgreSQL
```bash
# First, create a network
docker network create planner-network

# Run PostgreSQL container
docker run -d \
  --name postgres-dev \
  --network planner-network \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=planner_dev \
  -p 5432:5432 \
  postgres:15

# Run Planner Agent
docker run -d \
  --name planner-agent-dev \
  --network planner-network \
  -p 8000:8000 \
  -e APP_ENV=development \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_HOST=postgres-dev \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=planner_dev \
  -e SQLALCHEMY_ECHO=true \
  -e PLANNER_API_SECRET=dev-secret-key-change-me \
  -e PLANNER_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080 \
  arshiyamohammed15/planner-agent:latest
```

### Local Development with DATABASE_URL
```bash
docker run -d \
  --name planner-agent-dev \
  -p 8000:8000 \
  -e APP_ENV=development \
  -e DATABASE_URL=postgresql://postgres:postgres@localhost:5432/planner_dev \
  -e SQLALCHEMY_ECHO=true \
  -e PLANNER_API_SECRET=dev-secret-key-change-me \
  -e PLANNER_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080 \
  arshiyamohammed15/planner-agent:latest
```

---

## 2. Staging Environment

### Staging with External Database
```bash
docker run -d \
  --name planner-agent-staging \
  -p 8000:8000 \
  --restart unless-stopped \
  -e APP_ENV=staging \
  -e POSTGRES_USER=planner_staging_user \
  -e POSTGRES_PASSWORD=your-staging-password \
  -e POSTGRES_HOST=staging-db.example.com \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=planner_staging \
  -e SQLALCHEMY_ECHO=false \
  -e PLANNER_API_SECRET=your-staging-secret-key \
  -e PLANNER_ALLOWED_ORIGINS=https://staging.example.com,https://staging-api.example.com \
  -e SERVICE1_API_KEY=your-service1-key \
  -e SERVICE2_API_KEY=your-service2-key \
  arshiyamohammed15/planner-agent:latest
```

### Staging with DATABASE_URL
```bash
docker run -d \
  --name planner-agent-staging \
  -p 8000:8000 \
  --restart unless-stopped \
  -e APP_ENV=staging \
  -e DATABASE_URL=postgresql://planner_staging_user:password@staging-db.example.com:5432/planner_staging \
  -e SQLALCHEMY_ECHO=false \
  -e PLANNER_API_SECRET=your-staging-secret-key \
  -e PLANNER_ALLOWED_ORIGINS=https://staging.example.com \
  -e SERVICE1_API_KEY=your-service1-key \
  -e SERVICE2_API_KEY=your-service2-key \
  arshiyamohammed15/planner-agent:latest
```

---

## 3. Production Environment

### Production with Environment Variables
```bash
docker run -d \
  --name planner-agent-prod \
  -p 8000:8000 \
  --restart always \
  -e APP_ENV=production \
  -e POSTGRES_USER=planner_prod_user \
  -e POSTGRES_PASSWORD=your-secure-production-password \
  -e POSTGRES_HOST=prod-db.example.com \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_DB=planner_production \
  -e SQLALCHEMY_ECHO=false \
  -e PLANNER_API_SECRET=your-strong-production-secret-key \
  -e PLANNER_ALLOWED_ORIGINS=https://app.example.com,https://api.example.com \
  -e SERVICE1_API_KEY=your-production-service1-key \
  -e SERVICE2_API_KEY=your-production-service2-key \
  arshiyamohammed15/planner-agent:latest
```

### Production with DATABASE_URL
```bash
docker run -d \
  --name planner-agent-prod \
  -p 8000:8000 \
  --restart always \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql://planner_prod_user:password@prod-db.example.com:5432/planner_production?sslmode=require \
  -e SQLALCHEMY_ECHO=false \
  -e PLANNER_API_SECRET=your-strong-production-secret-key \
  -e PLANNER_ALLOWED_ORIGINS=https://app.example.com \
  -e SERVICE1_API_KEY=your-production-service1-key \
  -e SERVICE2_API_KEY=your-production-service2-key \
  arshiyamohammed15/planner-agent:latest
```

### Production with Environment File
```bash
# Create .env.prod file (DO NOT commit to version control)
# Then run:
docker run -d \
  --name planner-agent-prod \
  -p 8000:8000 \
  --restart always \
  --env-file .env.prod \
  arshiyamohammed15/planner-agent:latest
```

---

## 4. Using Environment Files

### Create .env file
```bash
# .env.dev
APP_ENV=development
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=planner_dev
SQLALCHEMY_ECHO=true
PLANNER_API_SECRET=dev-secret-key-change-me
PLANNER_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Run with .env file
```bash
docker run -d \
  --name planner-agent-dev \
  -p 8000:8000 \
  --env-file .env.dev \
  arshiyamohammed15/planner-agent:latest
```

---

## 5. Advanced Options

### Custom Host Port Mapping
```bash
# Map container port 8000 to host port 3000
docker run -d \
  --name planner-agent \
  -p 3000:8000 \
  -e APP_ENV=development \
  -e PLANNER_API_SECRET=dev-secret \
  arshiyamohammed15/planner-agent:latest
```

### With Resource Limits
```bash
docker run -d \
  --name planner-agent-prod \
  -p 8000:8000 \
  --restart always \
  --memory="512m" \
  --cpus="1.0" \
  -e APP_ENV=production \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e PLANNER_API_SECRET=your-secret \
  arshiyamohammed15/planner-agent:latest
```

### With Volume Mounts (for logs or config)
```bash
docker run -d \
  --name planner-agent \
  -p 8000:8000 \
  -v /host/path/logs:/app/logs \
  -e APP_ENV=development \
  -e PLANNER_API_SECRET=dev-secret \
  arshiyamohammed15/planner-agent:latest
```

### With Docker Network
```bash
# Create network
docker network create planner-network

# Run container on network
docker run -d \
  --name planner-agent \
  --network planner-network \
  -p 8000:8000 \
  -e APP_ENV=development \
  -e POSTGRES_HOST=postgres-container \
  -e PLANNER_API_SECRET=dev-secret \
  arshiyamohammed15/planner-agent:latest
```

---

## 6. Docker Compose Alternative

For easier management, consider using `docker-compose.yml`:

```yaml
version: '3.8'

services:
  planner-agent:
    image: arshiyamohammed15/planner-agent:latest
    container_name: planner-agent-dev
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=development
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_HOST=postgres
      - POSTGRES_PORT=5432
      - POSTGRES_DB=planner_dev
      - SQLALCHEMY_ECHO=true
      - PLANNER_API_SECRET=dev-secret-key-change-me
      - PLANNER_ALLOWED_ORIGINS=http://localhost:3000
    depends_on:
      - postgres
    restart: unless-stopped

  postgres:
    image: postgres:15
    container_name: postgres-dev
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=planner_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with: `docker-compose up -d`

---

## 7. Verification Commands

### Check if container is running
```bash
docker ps --filter name=planner-agent
```

### View logs
```bash
docker logs planner-agent-dev
docker logs -f planner-agent-dev  # Follow logs
```

### Test health endpoint
```bash
curl http://localhost:8000/health
```

### Stop container
```bash
docker stop planner-agent-dev
```

### Remove container
```bash
docker rm planner-agent-dev
```

### Stop and remove
```bash
docker rm -f planner-agent-dev
```

---

## Security Notes

1. **Never commit `.env` files** to version control
2. **Use strong secrets** in production (`PLANNER_API_SECRET`)
3. **Use environment variables** or secrets management (AWS Secrets Manager, Kubernetes Secrets, etc.)
4. **Restrict CORS origins** in production to only trusted domains
5. **Use SSL/TLS** for database connections in production (`sslmode=require` in DATABASE_URL)
6. **Set resource limits** in production to prevent resource exhaustion

---

## Troubleshooting

### Container exits immediately
- Check logs: `docker logs planner-agent-dev`
- Verify environment variables are set correctly
- Ensure database is accessible if using one

### Port already in use
- Change host port: `-p 8080:8000`
- Stop conflicting container: `docker ps` then `docker stop <container-id>`

### Database connection issues
- Verify database host is accessible from container
- Check network configuration if using Docker networks
- Verify credentials and database name

### CORS errors
- Add your frontend origin to `PLANNER_ALLOWED_ORIGINS`
- Ensure origins are comma-separated without spaces

