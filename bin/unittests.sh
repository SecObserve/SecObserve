#!/bin/sh

# Without arguments all unit tests are run, arguments are passed to `manage.py test`, e.g.
# ./bin/unittests.sh unittests.core.services.test_assessment
docker compose -f docker-compose-unittests.yml run --rm --build django "$@"
