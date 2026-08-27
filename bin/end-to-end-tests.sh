#!/bin/sh

cd ./end_to_end_tests && npm ci --no-audit --no-fund && cd ..

docker compose -f docker-compose-playwright.yml up --build --abort-on-container-exit --exit-code-from playwright
