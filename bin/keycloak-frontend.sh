#!/bin/sh

docker compose -f docker-compose/docker-compose-dev-keycloak.yml --profile frontend up --build  
