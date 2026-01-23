#!/bin/bash
# Docker Run Script for Local Development
# Usage: ./docker-run-dev.sh

set -e

CONTAINER_NAME="planner-agent-dev"
IMAGE="arshiyamohammed15/planner-agent:latest"
HOST_PORT=8000
CONTAINER_PORT=8000

# Stop and remove existing container if it exists
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    echo "Stopping and removing existing container..."
    docker rm -f $CONTAINER_NAME
fi

# Run the container
echo "Starting Planner Agent container..."
docker run -d \
  --name $CONTAINER_NAME \
  -p $HOST_PORT:$CONTAINER_PORT \
  -e APP_ENV=development \
  -e POSTGRES_USER=${POSTGRES_USER:-postgres} \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-postgres} \
  -e POSTGRES_HOST=${POSTGRES_HOST:-localhost} \
  -e POSTGRES_PORT=${POSTGRES_PORT:-5432} \
  -e POSTGRES_DB=${POSTGRES_DB:-planner_dev} \
  -e SQLALCHEMY_ECHO=true \
  -e PLANNER_API_SECRET=${PLANNER_API_SECRET:-dev-secret-key-change-me} \
  -e PLANNER_ALLOWED_ORIGINS=${PLANNER_ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:8080} \
  $IMAGE

echo "Container started successfully!"
echo "View logs: docker logs -f $CONTAINER_NAME"
echo "Stop container: docker stop $CONTAINER_NAME"
echo "Health check: curl http://localhost:$HOST_PORT/health"

