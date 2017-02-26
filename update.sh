#!/bin/sh
echo -n "Enter hostname: "
read APP_HOSTNAME

echo "Updating image"
docker pull zenwalker/storagl

echo "Stopping old container"
docker stop static
docker rm static

echo "Starting new container"
docker run -d --name static \
    -e ALLOWED_HOST=$APP_HOSTNAME \
    -v $(pwd)/data:/app/data -p 8801:8000 \
    zenwalker/storagl
