# Docker Image Push Script
# This script tags and pushes the planner-agent image to Docker Hub
# Replace YOUR_DOCKERHUB_USERNAME with your actual Docker Hub username

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername
)

$IMAGE_NAME = "planner-agent"
$TAG = "latest"
$REMOTE_IMAGE = "${DockerHubUsername}/${IMAGE_NAME}:${TAG}"

Write-Host "Tagging image..." -ForegroundColor Cyan
docker tag "${IMAGE_NAME}:${TAG}" $REMOTE_IMAGE

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to tag image" -ForegroundColor Red
    exit 1
}

Write-Host "Tagged successfully: $REMOTE_IMAGE" -ForegroundColor Green

Write-Host "`nPushing image to Docker Hub..." -ForegroundColor Cyan
docker push $REMOTE_IMAGE

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to push image. Make sure you're logged in with: docker login" -ForegroundColor Red
    exit 1
}

Write-Host "`nSuccessfully pushed image to Docker Hub!" -ForegroundColor Green
Write-Host "Image available at: https://hub.docker.com/r/${DockerHubUsername}/${IMAGE_NAME}" -ForegroundColor Yellow

