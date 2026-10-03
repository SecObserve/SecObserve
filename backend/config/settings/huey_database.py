from typing import Any

from peewee import Database, MySQLDatabase, OperationalError, PostgresqlDatabase
from playhouse.shortcuts import ReconnectMixin


# Huey keeps its connections open for the lifetime of the process, and peewee keeps
# using a connection the server has closed instead of opening a new one. Huey's own
# SqlStorage.check_conn() doesn't help: a connection dropped while idle still looks
# usable, and neither the size queries nor the stats queries call it.
#
# peewee warns against using ReconnectMixin with PostgreSQL. It is safe here because:
# - The default reconnect_errors are MySQL error codes, so they are replaced with
#   psycopg 3 messages.
# - peewee runs PostgreSQL in autocommit mode, and Huey runs every multi-statement
#   operation in atomic(). The mixin never reconnects inside a transaction, so no
#   uncommitted work can be lost silently.
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
