# Backend architecture

The backend is a Python application, using the Django and Django Rest Framework frameworks

- The application is in `backend/application`
- Configurations are in `backend/config`
- Unit tests are in `backend/unittests`

## Backend coding standards

- black, isort, flake8, backend/bin/run_mypy.sh and ../bin/run_pylint.shpython are used to check coding standards
- `backend/setup.cfg` contains definitions for the coding standards

## Backend unit tests

- The folder structure in `backend/unittests` matches the folder structure in `backend/application`
- All unit test classes are derived from `BaseTestCase` defined in `backend/unittests/base_test_case.py`
