from unittest import TestCase
from unittest.mock import Mock, patch

from peewee import MySQLDatabase, OperationalError, PostgresqlDatabase

from application.background_tasks.services.prefixed_sql_storage import PrefixedSqlHuey
from config.settings.huey_database import create_huey_database


class TestHueyDatabase(TestCase):
    def _database_settings(self, engine: str, password: str) -> dict[str, str]:
        return {
            "ENGINE": engine,
            "NAME": "secobserve",
            "USER": "service[user]@tenant",
            "PASSWORD": password,
            "HOST": "database.example.com",
            "PORT": "5432" if "postgresql" in engine else "3306",
        }

    def test_postgresql_preserves_credentials(self):
        for password in ("p[ass]word", "?#/%:@&=", "false", "1234"):
            with self.subTest(password=password):
                database = create_huey_database(
                    self._database_settings("django.db.backends.postgresql", password),
                    "sqlite:///:memory:",
                )

                self.assertIsInstance(database, PostgresqlDatabase)
                self.assertEqual("service[user]@tenant", database.connect_params["user"])
                self.assertEqual(password, database.connect_params["password"])
                self.assertEqual("database.example.com", database.connect_params["host"])
                self.assertEqual(5432, database.connect_params["port"])

    def test_mysql_preserves_credentials(self):
        for password in ("p[ass]word", "?#/%:@&=", "false", "1234"):
            with self.subTest(password=password):
                database = create_huey_database(
                    self._database_settings("django.db.backends.mysql", password),
                    "sqlite:///:memory:",
                )

                self.assertIsInstance(database, MySQLDatabase)
                self.assertEqual("service[user]@tenant", database.connect_params["user"])
                self.assertEqual(password, database.connect_params["password"])
                self.assertEqual("database.example.com", database.connect_params["host"])
                self.assertEqual(3306, database.connect_params["port"])

    def test_huey_storage_accepts_postgresql_database(self):
        database = create_huey_database(
            self._database_settings("django.db.backends.postgresql", "p[ass]word"),
            "sqlite:///:memory:",
        )

        huey = PrefixedSqlHuey(name="test", database=database, create_tables=False)

        self.assertIs(database, huey.storage.database)

    def test_huey_storage_accepts_mysql_database(self):
        database = create_huey_database(
            self._database_settings("django.db.backends.mysql", "p[ass]word"),
            "sqlite:///:memory:",
        )
        database.server_version = (8, 0, 1)
        database.execute_sql = Mock(return_value=Mock(fetchone=Mock(return_value=("MySQL 8.0.36",))))

        huey = PrefixedSqlHuey(name="test", database=database, create_tables=False)

        self.assertIs(database, huey.storage.database)

    def test_reconnects_when_the_server_closed_the_connection(self):
        for engine, database_class, message in (
            ("postgresql", PostgresqlDatabase, "terminating connection due to administrator command"),
            ("postgresql", PostgresqlDatabase, "consuming input failed: server closed the connection unexpectedly"),
            ("postgresql", PostgresqlDatabase, "the connection is closed"),
            ("mysql", MySQLDatabase, "(2013, 'Lost connection to MySQL server during query')"),
        ):
            with self.subTest(message=message):
                database = create_huey_database(
                    self._database_settings(f"django.db.backends.{engine}", "p[ass]word"),
                    "sqlite:///:memory:",
                )
                cursor = Mock()

                with (
                    patch.object(database_class, "execute_sql", side_effect=[OperationalError(message), cursor]),
                    patch.object(database, "is_closed", return_value=False),
                    patch.object(database, "close") as close,
                    patch.object(database, "connect") as connect,
                ):
                    self.assertIs(cursor, database.execute_sql("SELECT 1"))

                close.assert_called_once()
                connect.assert_called_once()

    def test_does_not_reconnect_on_other_errors(self):
        database = create_huey_database(
            self._database_settings("django.db.backends.postgresql", "p[ass]word"),
            "sqlite:///:memory:",
        )

        with (
            patch.object(
                PostgresqlDatabase, "execute_sql", side_effect=OperationalError("deadlock detected")
            ) as execute_sql,
            patch.object(database, "connect") as connect,
        ):
            with self.assertRaises(OperationalError):
                database.execute_sql("SELECT 1")

        execute_sql.assert_called_once()
        connect.assert_not_called()

    def test_sqlite_uses_configured_fallback_url(self):
        database = create_huey_database(
            {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/secobserve.db"},
            "sqlite:///:memory:",
        )

        self.assertEqual("sqlite:///:memory:", database)
