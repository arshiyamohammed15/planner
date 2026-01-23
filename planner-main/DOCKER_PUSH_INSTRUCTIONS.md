# Docker Image Push Instructions

## Prerequisites

1. **Docker Hub Account**: Make sure you have a Docker Hub account at https://hub.docker.com
2. **Docker Login**: Authenticate with Docker Hub

## Step 1: Login to Docker Hub

```powershell
docker login
```

Enter your Docker Hub username and password when prompted.

## Step 2: Tag the Image

Replace `YOUR_DOCKERHUB_USERNAME` with your actual Docker Hub username:

```powershell
docker tag planner-agent:latest YOUR_DOCKERHUB_USERNAME/planner-agent:latest
```

## Step 3: Push the Image

```powershell
docker push YOUR_DOCKERHUB_USERNAME/planner-agent:latest
```

## Alternative: Using the PowerShell Script

You can use the provided script:

```powershell
.\push-docker-image.ps1 -DockerHubUsername YOUR_DOCKERHUB_USERNAME
```

## Verify the Push

After pushing, you can verify the image is available at:
- https://hub.docker.com/r/YOUR_DOCKERHUB_USERNAME/planner-agent

## Pull the Image Later

Others (or you on another machine) can pull the image with:

```powershell
docker pull YOUR_DOCKERHUB_USERNAME/planner-agent:latest
```

## Other Container Registries

### GitHub Container Registry (ghcr.io)

```powershell
# Login
echo $env:GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Tag
docker tag planner-agent:latest ghcr.io/YOUR_GITHUB_USERNAME/planner-agent:latest

# Push
docker push ghcr.io/YOUR_GITHUB_USERNAME/planner-agent:latest
```

### AWS ECR

```powershell
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Tag
docker tag planner-agent:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/planner-agent:latest

# Push
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/planner-agent:latest
```

