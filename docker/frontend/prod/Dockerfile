# build environment
FROM node:24.3.0-alpine@sha256:b8ea75e6dcdf7dbba1ea8b57f77ec89ef04c1719d2ae986c8fbea21f9f4ec187 AS build

ARG VERSION=unknown

WORKDIR /app
ENV PATH=/app/node_modules/.bin:$PATH
COPY frontend/package.json ./
COPY frontend/package-lock.json ./
COPY frontend/.npmrc ./


RUN npm ci
COPY ./frontend ./
# insert version for status endpoint
RUN sed -i 's/version_unknown/'"${VERSION}"'/g' ./src/commons/about/About.tsx && \
        npm run build

# insert hash of assets to detect changes
RUN ASSET_HASH=$(sha256sum ./build/assets/* | sha256sum | cut -d ' ' -f 1) && \
        sed -i 's/hash_unknown/'"${ASSET_HASH}"'/g' ./build/index.html

WORKDIR /app/lib/runtime-env-cra
RUN npm ci

# production environment
FROM nginx:stable-alpine-slim@sha256:75bff1ee799d4ec95dda1d294d7b53775d497b5f824e81afe0f82ebbd8bc4cb8

USER root

# kics-scan ignore-block
# versions of dependencies from distribution are ok
RUN apk add --no-cache --virtual --update npm && \
        npm i -g node

COPY --from=build /app/build /usr/share/nginx/html
COPY --from=build /app/lib/runtime-env-cra /usr/share/nginx/html/lib/runtime-env-cra
COPY ./frontend/.env.no_oidc /usr/share/nginx/html/.env
COPY ./frontend/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./frontend/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./frontend/robots.txt /usr/share/nginx/html/robots.txt

ARG user=so_nginx
ARG group=so_nginx
ARG VERSION=unknown
ARG CREATED
ARG REVISION

# We want to overwrite what's coming from the base image
LABEL maintainer="Stefan Fleckenstein"

LABEL org.opencontainers.image.created=${CREATED}
LABEL org.opencontainers.image.description="SecObserve is an open source vulnerability management system for software development and cloud environments."
LABEL org.opencontainers.image.documentation="https://secobserve.github.io/SecObserve"
LABEL org.opencontainers.image.licenses="BSD3-Clause"
LABEL org.opencontainers.image.revision=${REVISION}
LABEL org.opencontainers.image.source="https://github.com/SecObserve/SecObserve"
LABEL org.opencontainers.image.title="SecObserve frontend"
LABEL org.opencontainers.image.url="https://github.com/SecObserve/SecObserve"
LABEL org.opencontainers.image.vendor="SecObserve"
LABEL org.opencontainers.image.version=${VERSION}

RUN addgroup -g 1001 -S ${group} && \
    adduser -u 1001 -S ${user} -G ${group} && \
    chown -R ${user}:${group} /usr/share/nginx/html && \
    chmod -R 777 /usr/share/nginx/html && \
    chown -R ${user}:${group} /var/log/nginx && \
    chown -R ${user}:${group} /etc/nginx/conf.d

HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD wget -nv -t1 --spider 'http://127.0.0.1:3000/#/login' || exit 1

EXPOSE 3000

WORKDIR /usr/share/nginx/html

USER ${user}

CMD ["/bin/sh", "-c", "./lib/runtime-env-cra/lib/index.js --strict false && nginx -g \"daemon off;\""]
