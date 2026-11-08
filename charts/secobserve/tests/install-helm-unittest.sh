#!/usr/bin/env bash

set -euo pipefail

HELM_UNITTEST_VERSION=1.2.1

if helm plugin list | grep -q '^unittest[[:space:]]'; then
    exit 0
fi

if [[ "$(helm version --template '{{.Version}}')" == v4.* ]]; then
    # OCI package from ghcr.io, no install hook downloading from GitHub releases
    helm plugin install "oci://ghcr.io/helm-unittest/helm-unittest/unittest:${HELM_UNITTEST_VERSION}" --verify=false
else
    # Helm 3 cannot install OCI plugins
    helm plugin install https://github.com/helm-unittest/helm-unittest.git --version "v${HELM_UNITTEST_VERSION}"
fi
