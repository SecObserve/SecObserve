import os
import runpy
from unittest import TestCase
from unittest.mock import patch

import environ

from config.settings import base
from config.settings.database_options import postgresql_options

KEEPALIVE_VARIABLES = (
    "DATABASE_KEEPALIVES_IDLE",
    "DATABASE_KEEPALIVES_INTERVAL",
    "DATABASE_KEEPALIVES_COUNT",
    "DATABASE_TCP_USER_TIMEOUT_MS",
)
DEFAULT_OPTIONS = {
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 3,
    "tcp_user_timeout": 60000,
}


def _environment_without_keepalive_variables(**variables: str) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if key not in KEEPALIVE_VARIABLES}
    return environment | variables


def _database_environment(engine: str) -> dict[str, str]:
    return _environment_without_keepalive_variables(
        DATABASE_ENGINE=engine,
        DATABASE_HOST="database.example.com",
        DATABASE_PORT="5432",
        DATABASE_DB="secobserve",
        DATABASE_USER="secobserve",
        DATABASE_PASSWORD="secobserve",
    )


class TestDatabaseOptions(TestCase):
    def test_postgresql_options_defaults(self):
        with patch.dict(os.environ, _environment_without_keepalive_variables(), clear=True):
            self.assertEqual(DEFAULT_OPTIONS, postgresql_options(environ.Env()))

    @patch.dict(
        os.environ,
        {
            "DATABASE_KEEPALIVES_IDLE": "60",
            "DATABASE_KEEPALIVES_INTERVAL": "5",
            "DATABASE_KEEPALIVES_COUNT": "6",
            "DATABASE_TCP_USER_TIMEOUT_MS": "0",
        },
    )
    def test_postgresql_options_from_environment(self):
        self.assertEqual(
            {
                "keepalives": 1,
                "keepalives_idle": 60,
                "keepalives_interval": 5,
                "keepalives_count": 6,
                "tcp_user_timeout": 0,
            },
            postgresql_options(environ.Env()),
        )

    def test_postgresql_settings_use_options_for_django_and_huey(self):
        with patch.dict(os.environ, _database_environment("django.db.backends.postgresql"), clear=True):
            settings = runpy.run_path(base.__file__)

        self.assertEqual(DEFAULT_OPTIONS, settings["DATABASES"]["default"].get("OPTIONS"))
        for database in (settings["HUEY"]["database"], settings["HUEY_STATS"]["database"]):
            self.assertEqual(DEFAULT_OPTIONS, {key: database.connect_params.get(key) for key in DEFAULT_OPTIONS})

    def test_mysql_settings_do_not_use_options(self):
        with patch.dict(os.environ, _database_environment("django.db.backends.mysql"), clear=True):
            settings = runpy.run_path(base.__file__)

        self.assertEqual({"charset": "utf8mb4"}, settings["DATABASES"]["default"].get("OPTIONS"))
        for database in (settings["HUEY"]["database"], settings["HUEY_STATS"]["database"]):
            self.assertFalse(DEFAULT_OPTIONS.keys() & database.connect_params.keys())
