#!/bin/sh

# Builds and runs the tests via Docker.

# set the build context to the parent directory
cd ../ && docker build -f tests/Dockerfile -t review-testing .
docker run review-testing
