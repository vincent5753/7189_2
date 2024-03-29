#!/bin/bash

# *********************************************
# KIE Server - Docker image build script
# ********************************************

IMAGE_NAME="kiegroup/kie-server"
IMAGE_TAG="7.71.0.Final"


# Build the container image.
echo "Building container for $IMAGE_NAME:$IMAGE_TAG.."
# In case you want to build with Docker please use `docker` instead of ´podman´
docker build --rm -t $IMAGE_NAME:$IMAGE_TAG .
echo "Build done"
