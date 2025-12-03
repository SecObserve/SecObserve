FROM python:3.14-alpine@sha256:d7fb7df19ca613dcebf0969d0ab2b04bb35e95f325c104da1b1718162468f6de AS python-base

# Python build stage
FROM python-base AS python-build-stage

ARG BUILD_ENVIRONMENT=prod

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
RUN poetry install --no-root && rm -rf "$POETRY_CACHE_DIR"


# Python 'run' stage
FROM python-base AS python-run-stage

ARG BUILD_ENVIRONMENT=prod
ARG APP_HOME=/app
ARG VERSION=unknown
ARG CREATED
ARG REVISION

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

LABEL org.opencontainers.image.created=${CREATED}
LABEL org.opencontainers.image.description="SecObserve is an open source vulnerability management system for software development and cloud environments."
LABEL org.opencontainers.image.documentation="https://secobserve.github.io/SecObserve"
LABEL org.opencontainers.image.licenses="BSD3-Clause"
LABEL org.opencontainers.image.revision=${REVISION}
LABEL org.opencontainers.image.source="https://github.com/SecObserve/SecObserve"
LABEL org.opencontainers.image.title="SecObserve backend"
LABEL org.opencontainers.image.url="https://github.com/SecObserve/SecObserve"
LABEL org.opencontainers.image.vendor="SecObserve"
LABEL org.opencontainers.image.version=${VERSION}

WORKDIR ${APP_HOME}

# Add user and group to avoid running as roolt
ARG user=django
ARG group=django

# copy dependencies from build stage
ENV VIRTUAL_ENV=/.venv \
    PATH="/.venv/bin:$PATH"
COPY --from=python-build-stage ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# copy startup scripts
COPY ./docker/backend/prod/django/entrypoint /entrypoint
COPY ./docker/backend/prod/django/wait-for-it.sh /wait-for-it.sh

# copy application code to WORKDIR
COPY ./backend ${APP_HOME}

# use prod settings
COPY ./backend/config/settings/prod.py ${APP_HOME}/config/settings/dist.py

# certificates for MS Azure managed MySQL database
# single server
COPY ./docker/backend/prod/database/BaltimoreCyberTrustRoot_combined.crt.pem ${APP_HOME}/BaltimoreCyberTrustRoot_combined.crt.pem
# flexible server
COPY ./docker/backend/prod/database/combined-ca-certificates.pem ${APP_HOME}/combined-ca-certificates.pem

# kics-scan ignore-block
# versions of dependencies from distribution are ok
RUN addgroup -g 1001 -S ${group} \
    && adduser -u 1001 -S ${user} -G ${group} \
    # Install binaries and libs for PostgreSQL and MySQL
    && apk add --no-cache --virtual postgresql-libs postgresql-client mariadb-dev mysql-client bash \
    # make startup scripts executable
    && chmod +x /entrypoint \
    && chmod +x /wait-for-it.sh \
    # insert version for status endpoint
    && sed -i 's/version_unknown/'"${VERSION}"'/g' ${APP_HOME}/application/commons/api/views.py \
    # make staticfiles writeable 
    && mkdir ${APP_HOME}/application/staticfiles \
    && chmod ugo+w ${APP_HOME}/application/staticfiles \
    # create directory for huey task queue
    && mkdir /var/lib/huey \
    && chown -R ${user}:${group} /var/lib/huey \
    && chmod ugo+rw /var/lib/huey \
    # create directory for possible sqlite db
    && mkdir /var/lib/sqlite \
    && chown -R ${user}:${group} /var/lib/sqlite \
    && chmod ugo+rw /var/lib/sqlite

HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD wget -nv -t1 --spider 'http://127.0.0.1:5000/api/status/health/' || exit 1

EXPOSE 5000

USER ${user}

ENTRYPOINT ["/entrypoint"]
