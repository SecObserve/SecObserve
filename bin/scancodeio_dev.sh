#!/bin/sh

cd ./frontend
npm install --no-audit --no-fund && 
cd ..
docker compose -f docker-compose-dev.yml -f docker-compose-dev-scancodeio.yaml up --build
