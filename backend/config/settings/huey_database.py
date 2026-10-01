from typing import Any

from peewee import Database, MySQLDatabase, OperationalError, PostgresqlDatabase
from playhouse.shortcuts import ReconnectMixin


# Huey keeps its connections open for the lifetime of the process, and peewee keeps
# using a connection the server has closed instead of opening a new one.
class ReconnectPostgresqlDatabase(ReconnectMixin, PostgresqlDatabase):
    reconnect_errors = (
        (OperationalError, "server closed the connection"),
        (OperationalError, "terminating connection"),
        (OperationalError, "the connection is closed"),
    )


class ReconnectMySQLDatabase(ReconnectMixin, MySQLDatabase):
    pass


def create_huey_database(database_settings: dict[str, Any], sqlite_url: str) -> Database | str:
    engine = database_settings["ENGINE"]
    database_name = database_settings["NAME"]
    username = database_settings.get("USER")
    password = database_settings.get("PASSWORD")
    host = database_settings.get("HOST") or "localhost"

    if "postgresql" in engine:
        return ReconnectPostgresqlDatabase(
            database_name,
            user=username,
            password=password,
            host=host,
            port=int(database_settings.get("PORT") or 5432),
            **database_settings.get("OPTIONS", {}),
        )
    if "mysql" in engine:
        return ReconnectMySQLDatabase(
            database_name,
            user=username,
            password=password,
            host=host,
            port=int(database_settings.get("PORT") or 3306),
        )
    return sqlite_url
