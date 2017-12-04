#!/bin/sh
CONTAINER_NAME="static"
APP_PORT=8801

echo "Updating image"
docker pull zenwalker/storagl

echo "Stopping old container"
docker stop $CONTAINER_NAME
docker rm $CONTAINER_NAME

echo "Starting new container"
docker run -d --name=$CONTAINER_NAME -v $(pwd)/data:/app/data \
    -p $APP_PORT:8000 --restart=always zenwalker/storagl
