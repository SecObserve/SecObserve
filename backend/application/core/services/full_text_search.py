import logging

from django.db import connection
from django.db.backends.utils import CursorWrapper

from application.commons.models import Settings
from application.core.models import Observation, Observation_Log
from application.core.queries.observation import (
    OBSERVATION_FULL_TEXT_SEARCH_INDEXES,
    OBSERVATION_LOG_FULL_TEXT_SEARCH_INDEXES,
)

logger = logging.getLogger("secobserve.core")


class FullTextSearchError(Exception):
    pass


def activate_full_text_search() -> None:
    _check_postgresql()

    with connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

        # An interrupted CREATE INDEX CONCURRENTLY leaves an invalid index behind,
        # which would be skipped by IF NOT EXISTS
        for index_name in _get_invalid_indexes(cursor):
            logger.info("Dropping invalid index %s ...", index_name)
            cursor.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {connection.ops.quote_name(index_name)}")

        # The indexes are built on UPPER(field), because Django filters with UPPER(field) LIKE UPPER(value) for
        # icontains. CONCURRENTLY doesn't block writes to the tables while the indexes are built.
        for table, field, index_name in _get_indexes():
            logger.info("Creating index %s ...", index_name)
            cursor.execute(
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {connection.ops.quote_name(index_name)} "
                f"ON {connection.ops.quote_name(table)} "
                f"USING gin (UPPER({connection.ops.quote_name(field)}) gin_trgm_ops)"
            )

    # Only activated when all indexes exist, otherwise the search would scan the whole tables
    _set_feature_full_text_search(True)
    logger.info("Full text search activated")


def deactivate_full_text_search() -> None:
    _check_postgresql()

    # Deactivated before the indexes are dropped, so that no search runs without the indexes
    _set_feature_full_text_search(False)

    with connection.cursor() as cursor:
        for _, _, index_name in _get_indexes():
            logger.info("Dropping index %s ...", index_name)
            cursor.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {connection.ops.quote_name(index_name)}")

    logger.info("Full text search deactivated")


def _check_postgresql() -> None:
    if connection.vendor != "postgresql":
        raise FullTextSearchError("Full text search is only available with PostgreSQL")


def _get_indexes() -> list[tuple[str, str, str]]:
    indexes = []
    for model, fields in (
        (Observation, OBSERVATION_FULL_TEXT_SEARCH_INDEXES),
        (Observation_Log, OBSERVATION_LOG_FULL_TEXT_SEARCH_INDEXES),
    ):
        for field, index_name in fields.items():
            indexes.append((model._meta.db_table, field, index_name))
    return indexes


def _get_invalid_indexes(cursor: CursorWrapper) -> list[str]:
    cursor.execute(
        "SELECT c.relname FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid "
        "WHERE NOT i.indisvalid AND c.relname = ANY(%s)",
        [[index_name for _, _, index_name in _get_indexes()]],
    )
    return [row[0] for row in cursor.fetchall()]


def _set_feature_full_text_search(value: bool) -> None:
    settings = Settings.load()
    settings.feature_full_text_search = value
    settings.save()
