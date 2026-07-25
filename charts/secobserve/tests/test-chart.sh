#!/usr/bin/env bash

set -euo pipefail

chart_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_dir="$(mktemp -d "${TMPDIR:-/tmp}/secobserve-chart-test.XXXXXX")"
trap 'find "$test_dir" -depth -delete' EXIT

helm dependency build "$chart_dir"
helm lint "$chart_dir"

helm template secobserve "$chart_dir" --namespace secobserve >"$test_dir/default.yaml"
helm template custom "$chart_dir" --namespace secobserve >"$test_dir/custom-release.yaml"
helm template custom "$chart_dir" --namespace secobserve \
    --set postgresql.architecture=replication >"$test_dir/replication.yaml"
helm template custom "$chart_dir" --namespace secobserve \
    --set postgresql.auth.existingSecret=external-db \
    --set postgresql.auth.secretKeys.userPasswordKey=db-password >"$test_dir/existing-secret.yaml"
helm template custom "$chart_dir" --namespace secobserve \
    --set postgresql.enabled=false \
    --set database.host=postgres.example.internal \
    --set database.passwordSecret.name=external-db \
    --set database.passwordSecret.key=db-password >"$test_dir/external-database.yaml"
helm template custom "$chart_dir" --namespace secobserve \
    --values "$chart_dir/tests/values/render-options.yaml" >"$test_dir/render-options.yaml"

grep -q 'value: "custom-postgresql"' "$test_dir/custom-release.yaml"
grep -q 'value: "custom-postgresql-primary"' "$test_dir/replication.yaml"
grep -q "name: external-db" "$test_dir/existing-secret.yaml"
grep -q "key: db-password" "$test_dir/existing-secret.yaml"
grep -q 'value: "postgres.example.internal"' "$test_dir/external-database.yaml"
grep -q "example.com/second: two" "$test_dir/render-options.yaml"
grep -q "mountPath: /extra" "$test_dir/render-options.yaml"
grep -q "path: /extra" "$test_dir/render-options.yaml"

if helm template custom "$chart_dir" --set replicaCount=2 >"$test_dir/invalid-replicas.yaml" 2>&1; then
    echo "Expected replicaCount=2 to fail schema validation" >&2
    exit 1
fi

if helm template custom "$chart_dir" --set postgresql.enabled=false >"$test_dir/missing-external-database.yaml" 2>&1; then
    echo "Expected an external database without host and password Secret to fail" >&2
    exit 1
fi

helm unittest "$chart_dir"
