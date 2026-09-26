#!/bin/sh

cd ./frontend
npm install --no-audit --no-fund && 
cd ..
docker compose -f docker-compose/docker-compose-dev.yml -f docker-compose/docker-compose-dev-vulnerablecode.yaml up --build
