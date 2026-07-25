# Docker Compose

Docker Compose is a tool for defining and running multi-container Docker applications. With Docker Compose, you use a YAML file to configure your application’s services. Then, with a single command, you create and start all the services from your configuration. These Docker Compose files are available:

## Development

* [`docker-compose-dev-keycloak.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev-keycloak.yml)
    - Starts the PostgreSQL database, the SecObserve backend, Keycloak and Mailhog
    - The frontend is only started, when the parameter `--profile frontend` is given
    - A predefined realm calles `secobserve` is imported on start-up. There is an administrator configured (username: `admin`, password: `admin`) and a regular user for SecObserve (username: `keycloak_user`, password: `keycloak`).
* [`docker-compose-dev-mysql.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev-mysql.yml)
    - Starts the MySQL database, as well as SecObserve's backend and frontend
    - Backend and frontend are build automatically if necessary and are started in development mode with hot reloading
* [`docker-compose-dev.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev.yml)
    - Starts the PostgreSQL database, as well as SecObserve's backend and frontend
    - Backend and frontend are build automatically if necessary and are started in development mode with hot reloading
* [`docker-compose-dev-arm.yaml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev-arm.yaml)
    - Overrides the development stack for macOS on Apple Silicon
    - Runs the main services on ARM64 and installs frontend dependencies inside the container using a Docker-managed volume
    - Start it together with the standard development file:

      ```shell
      docker compose -f docker-compose-dev.yml -f docker-compose-dev-arm.yaml up --build
      ```
* [`docker-compose-playwright.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-playwright.yml)
    - Starts the end-to-end tests with Playwright
* [`docker-compose-prod-test.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-prod-test.yml)
    - Starts the PostgreSQL database, as well as SecObserve's backend and frontend
    - Backend and frontend are build automatically if necessary with the production Dockerfiles
* [`docker-compose-unittests.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-unittests.yml)
    - Starts the unit tests for the backend
* [`docker-compose.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose.yml)
    - This is a link to `docker-compose-dev.yml` and is used as a default for the `docker compose` command

## Production

See the [installation](../getting_started/installation.md) guide how to use the productive Docker Compose files.

* [`docker-compose-prod-mysql.yml`](https://github.com/SecObserve/SecObserve/blob/main/docker-compose-prod-mysql.yml)
* [`docker-compose-prod-postgres.yml`](https://github.com/SecObserve/SecObserve/blob/main/docker-compose-prod-postgres.yml)
