#!/bin/bash

# Local development script for WorshipFlow
# Builds Docker image, removes old image, and runs container

set -e  # Exit on error

IMAGE_NAME="worshipflow-local"
CONTAINER_NAME="worshipflow-dev"
PORT=8080

echo "💾 Saving old image ID (if exists)..."
OLD_IMAGE_ID=$(docker images -q ${IMAGE_NAME}:latest 2>/dev/null || echo "")

echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME}:latest .

echo "🧹 Cleaning up old image..."
if [ -n "$OLD_IMAGE_ID" ]; then
  # Get the new image ID
  NEW_IMAGE_ID=$(docker images -q ${IMAGE_NAME}:latest)

  # Only remove if the old and new IDs are different
  if [ "$OLD_IMAGE_ID" != "$NEW_IMAGE_ID" ]; then
    echo "Removing old image: $OLD_IMAGE_ID"
    docker rmi -f $OLD_IMAGE_ID 2>/dev/null || true
  else
    echo "No changes detected, image is the same"
  fi
else
  echo "No previous image to remove"
fi

# Also clean up dangling images
docker image prune -f

echo "🛑 Stopping and removing existing container..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

echo "🚀 Running Docker container..."
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8080 \
  -e DJANGO_SECRET_KEY="local-dev-secret-key-change-in-production" \
  -e DJANGO_DEBUG="True" \
  ${IMAGE_NAME}:latest

echo ""
echo "✅ WorshipFlow is running!"
echo "📍 Access the app at: http://localhost:${PORT}"
echo ""
echo "Useful commands:"
echo "  View logs:    docker logs -f ${CONTAINER_NAME}"
echo "  Stop:         docker stop ${CONTAINER_NAME}"
echo "  Restart:      docker restart ${CONTAINER_NAME}"
echo "  Shell access: docker exec -it ${CONTAINER_NAME} /bin/bash"
