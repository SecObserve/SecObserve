#!/usr/bin/env bash

set -euo pipefail

if helm plugin list | grep -q '^unittest[[:space:]]'; then
    exit 0
fi

install_args=(
    https://github.com/helm-unittest/helm-unittest.git
    --version v0.8.2
)

if [[ "$(helm version --template '{{.Version}}')" == v4.* ]]; then
    install_args+=(--verify=false)
fi

helm plugin install "${install_args[@]}"
