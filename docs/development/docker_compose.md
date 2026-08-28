# Docker Compose

Docker Compose is a tool for defining and running multi-container Docker applications. With Docker Compose, you use a YAML file to configure your application’s services. Then, with a single command, you create and start all the services from your configuration. These Docker Compose files are available:

## Development

* [`docker-compose-dev.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev.yml)
    - Starts the PostgreSQL database, as well as SecObserve's backend and frontend
    - Backend and frontend are build automatically if necessary and are started in development mode with hot reloading
* [`docker-compose-dev-multi.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev-multi.yml)
    - Starts the PostgreSQL database and the frontend, as well as SecObserve's backend split into one container per role: `init` (migrations, admin user, parsers, licenses), `background` (Huey consumer) and `api` (Django development server)
    - The roles are selected by the argument given to the backend's entrypoint, see `docker/backend/dev/django/entrypoint`
* [`docker-compose-dev-mysql.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev-mysql.yml)
    - Starts the MySQL database, as well as SecObserve's backend and frontend
    - Backend and frontend are build automatically if necessary and are started in development mode with hot reloading
* [`docker-compose-dev-keycloak.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-dev-keycloak.yml)
    - Starts the PostgreSQL database, the SecObserve backend, Keycloak and Mailhog
    - The frontend is only started, when the parameter `--profile frontend` is given
    - A predefined realm calles `secobserve` is imported on start-up. There is an administrator configured (username: `admin`, password: `admin`) and a regular user for SecObserve (username: `keycloak_user`, password: `keycloak`).
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
    - The environment variables of the backend container are defined in `docker/backend/prod/django/docker.env`
* [`docker-compose-prod-test-multi.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-prod-test-multi.yml)
    - Same as `docker-compose-prod-test.yml`, but with the backend split into one container per role: `init` (migrations, admin user, parsers, licenses), `background` (Huey consumer) and `api` (Gunicorn)
    - The roles are selected by the argument given to the backend's entrypoint, see `docker/backend/prod/django/entrypoint`
    - The environment variables of the backend containers are defined in `docker/backend/prod/django/docker.env`
* [`docker-compose-unittests.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose-unittests.yml)
    - Starts the unit tests for the backend
    - `./bin/unittests.sh` passes its arguments to `manage.py test`, e.g. `./bin/unittests.sh unittests.core.services.test_assessment` to run only the tests of one module. Without arguments all unit tests are run and the coverage is measured, with arguments the coverage measurement is skipped to get the results faster.
    - The database schemas are generated from the models, the migrations are not executed, see `MIGRATION_MODULES` in `backend/config/settings/unittests.py`. Running all migrations took a considerable amount of time for every run of the unit tests.
    - That the migrations result in the same schema is covered by the end to end tests, which start the backend with a fresh database and run all migrations
* [`docker-compose.yml`](https://github.com/SecObserve/SecObserve/blob/dev/docker-compose.yml)
    - This is a link to `docker-compose-dev.yml` and is used as a default for the `docker compose` command

## Production

See the [installation](../getting_started/installation.md) guide how to use the productive Docker Compose files.

* [`docker-compose-prod-postgres.yml`](https://github.com/SecObserve/SecObserve/blob/main/docker-compose-prod-postgres.yml)
* [`docker-compose-prod-mysql.yml`](https://github.com/SecObserve/SecObserve/blob/main/docker-compose-prod-mysql.yml)
