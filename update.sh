#!/usr/bin/env sh
OWNER=1000:1000
CONTAINER_NAME="storagl"
APP_PORT=8801

echo "Updating image"
docker pull zenwalker/storagl

echo "Stopping old container"
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

echo "Starting new container"
docker run -d \
    --name=$CONTAINER_NAME \
    -v $(pwd)/data:/app/data \
    -e FILE_OWNER=$OWNER \
    -p $APP_PORT:8000 \
    --restart=always \
    zenwalker/storagl
