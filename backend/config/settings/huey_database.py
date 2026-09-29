from typing import Any

from peewee import Database, MySQLDatabase, PostgresqlDatabase


def create_huey_database(database_settings: dict[str, Any], sqlite_url: str) -> Database | str:
    engine = database_settings["ENGINE"]
    database_name = database_settings["NAME"]
    username = database_settings.get("USER")
    password = database_settings.get("PASSWORD")
    host = database_settings.get("HOST") or "localhost"

    if "postgresql" in engine:
        return PostgresqlDatabase(
            database_name,
            user=username,
            password=password,
            host=host,
            port=int(database_settings.get("PORT") or 5432),
            **database_settings.get("OPTIONS", {}),
        )
    if "mysql" in engine:
        return MySQLDatabase(
            database_name,
            user=username,
            password=password,
            host=host,
            port=int(database_settings.get("PORT") or 3306),
        )
    return sqlite_url
