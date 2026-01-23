#!/bin/bash
# Docker Run Script for Staging Environment
# Usage: ./docker-run-staging.sh
# Note: Set required environment variables before running

set -e

CONTAINER_NAME="planner-agent-staging"
IMAGE="arshiyamohammed15/planner-agent:latest"
HOST_PORT=8000
CONTAINER_PORT=8000

# Validate required environment variables
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "Error: POSTGRES_PASSWORD environment variable is required"
    exit 1
fi

if [ -z "$PLANNER_API_SECRET" ]; then
    echo "Error: PLANNER_API_SECRET environment variable is required"
    exit 1
fi

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker rm -f $CONTAINER_NAME
fi

# Run the container
echo "Starting Planner Agent container for staging..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $HOST_PORT:$CONTAINER_PORT \
  --restart unless-stopped \
  -e APP_ENV=staging \
  -e POSTGRES_USER=${POSTGRES_USER:-planner_staging_user} \
  -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
  -e POSTGRES_HOST=${POSTGRES_HOST:-staging-db.example.com} \
  -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
  -e POSTGRES_DB=${POSTGRES_DB:-planner_staging} \
  -e SQLALCHEMY_ECHO=false \
  -e PLANNER_API_SECRET=$PLANNER_API_SECRET \
  -e PLANNER_ALLOWED_ORIGINS=${PLANNER_ALLOWED_ORIGINS:-https://staging.example.com} \
  -e SERVICE1_API_KEY=${SERVICE1_API_KEY:-} \
  -e SERVICE2_API_KEY=${SERVICE2_API_KEY:-} \
  $IMAGE

echo "Container started successfully!"
echo "View logs: docker logs -f $CONTAINER_NAME"
echo "Stop container: docker stop $CONTAINER_NAME"
echo "Health check: curl http://localhost:$HOST_PORT/health"

