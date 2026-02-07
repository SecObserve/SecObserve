FROM python:3.14-alpine@sha256:faee120f7885a06fcc9677922331391fa690d911c020abb9e8025ff3d908e510 AS python-base

# Python build stage
FROM python-base AS python-build-stage

ARG BUILD_ENVIRONMENT=dev

# Install packages
# kics-scan ignore-block
# versions of dependencies from distribution are ok
RUN apk add --no-cache --virtual .build-deps \
    ca-certificates gcc libffi-dev linux-headers mariadb-dev musl-dev postgresql-dev

# install dependencies with poetry
COPY ./backend/poetry_requirements.txt ./
RUN pip install --no-cache -r ./poetry_requirements.txt

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /

COPY backend/pyproject.toml backend/poetry.lock ./
RUN poetry install --extras "dev" --no-root && rm -rf "$POETRY_CACHE_DIR"


# Python 'run' stage
FROM python-base AS python-run-stage

ARG BUILD_ENVIRONMENT=dev
ARG APP_HOME=/app
ARG COMMIT_ID=undefined

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# Add user and group to avoid running as root
ARG user=django
ARG group=django

# copy dependencies from build stage
ENV VIRTUAL_ENV=/.venv \
    PATH="/.venv/bin:$PATH"
COPY --from=python-build-stage ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# copy startup scripts
COPY ./docker/backend/dev/django/entrypoint /entrypoint
COPY ./docker/backend/dev/django/wait-for-it.sh /wait-for-it.sh

# copy application code to WORKDIR
COPY ./backend ${APP_HOME}
# use dev settings
COPY ./backend/config/settings/dev.py ${APP_HOME}/config/settings/dist.py

# kics-scan ignore-block
# versions of dependencies from distribution are ok
RUN addgroup -g 1001 -S ${group} \
    && adduser -u 1001 -S ${user} -G ${group} \
    # Install binaries and libs for PostgreSQL and MySQL
    && apk add --no-cache --virtual postgresql-libs postgresql-client mariadb-dev mysql-client bash \
    # make startup scripts executable
    && chmod +x /entrypoint \
    && chmod +x /wait-for-it.sh \
    # insert commit id for status endpoint
    && sed -i 's/placeholder/'"${COMMIT_ID}"'/g' ${APP_HOME}/application/commons/api/views.py \
    # create directory for huey task queue
    && mkdir /var/lib/huey \
    && chown -R ${user}:${group} /var/lib/huey \
    && chmod ugo+rw /var/lib/huey

HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD wget -nv -t1 --spider 'http://127.0.0.1:8000/api/status/health/' || exit 1

USER ${user}

ENTRYPOINT ["/entrypoint"]
