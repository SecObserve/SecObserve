#!/bin/sh

set -e

case "$(uname -m)" in
  arm64|aarch64)
    export DOCKER_DEFAULT_PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/amd64}"
    ;;
esac

docker compose -f docker-compose-dev.yml up --build
