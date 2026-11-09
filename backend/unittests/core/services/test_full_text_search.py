from unittest.mock import MagicMock, call, patch

from application.commons.models import Settings
from application.core.queries.observation import (
    OBSERVATION_FULL_TEXT_SEARCH_INDEXES,
    OBSERVATION_LOG_FULL_TEXT_SEARCH_INDEXES,
)
from application.core.services.full_text_search import (
    FullTextSearchError,
    activate_full_text_search,
    deactivate_full_text_search,
)
from unittests.base_test_case import BaseTestCase

ALL_INDEXES = list(OBSERVATION_FULL_TEXT_SEARCH_INDEXES.values()) + list(
    OBSERVATION_LOG_FULL_TEXT_SEARCH_INDEXES.values()
)


class TestFullTextSearch(BaseTestCase):
    def _mock_connection(self, mock_connection, invalid_indexes=None):
        mock_connection.vendor = "postgresql"
        mock_connection.ops.quote_name.side_effect = lambda name: f'"{name}"'
        cursor = MagicMock()
        cursor.fetchall.return_value = [(index_name,) for index_name in invalid_indexes or []]
        mock_connection.cursor.return_value.__enter__.return_value = cursor
        return cursor

    def _statements(self, cursor):
        return [execute_call.args[0] for execute_call in cursor.execute.call_args_list]

    @patch("application.core.services.full_text_search.connection")
    def test_activate(self, mock_connection):
        cursor = self._mock_connection(mock_connection)

        activate_full_text_search()

        statements = self._statements(cursor)
        self.assertEqual("CREATE EXTENSION IF NOT EXISTS pg_trgm", statements[0])
        self.assertIn("NOT i.indisvalid", statements[1])
        self.assertEqual([ALL_INDEXES], cursor.execute.call_args_list[1].args[1])
        self.assertEqual(
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS "core_obs_title_trgm_idx" ON "core_observation" '
            'USING gin (UPPER("title") gin_trgm_ops)',
            statements[2],
        )
        self.assertEqual(
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS "core_obs_log_comment_trgm_idx" ON "core_observation_log" '
            'USING gin (UPPER("comment") gin_trgm_ops)',
            statements[-1],
        )
        self.assertEqual(2 + len(ALL_INDEXES), len(statements))
        self.assertTrue(Settings.load().feature_full_text_search)

    @patch("application.core.services.full_text_search.connection")
    def test_activate_invalid_index(self, mock_connection):
        cursor = self._mock_connection(mock_connection, invalid_indexes=["core_obs_title_trgm_idx"])

        activate_full_text_search()

        statements = self._statements(cursor)
        self.assertEqual('DROP INDEX CONCURRENTLY IF EXISTS "core_obs_title_trgm_idx"', statements[2])
        self.assertTrue(statements[3].startswith('CREATE INDEX CONCURRENTLY IF NOT EXISTS "core_obs_title_trgm_idx"'))
        self.assertEqual(3 + len(ALL_INDEXES), len(statements))

    @patch("application.core.services.full_text_search.connection")
    def test_activate_index_error(self, mock_connection):
        cursor = self._mock_connection(mock_connection)
        cursor.execute.side_effect = [None, None, Exception("index error")]

        with self.assertRaises(Exception):
            activate_full_text_search()

        self.assertFalse(Settings.load().feature_full_text_search)

    @patch("application.core.services.full_text_search._set_feature_full_text_search")
    @patch("application.core.services.full_text_search.connection")
    def test_deactivate(self, mock_connection, mock_set_feature):
        cursor = self._mock_connection(mock_connection)
        manager = MagicMock()
        manager.attach_mock(mock_set_feature, "set_feature")
        manager.attach_mock(cursor.execute, "execute")

        deactivate_full_text_search()

        # The feature is deactivated before the indexes are dropped
        self.assertEqual(call.set_feature(False), manager.mock_calls[0])
        self.assertEqual(
            [f'DROP INDEX CONCURRENTLY IF EXISTS "{index_name}"' for index_name in ALL_INDEXES],
            self._statements(cursor),
        )

    @patch("application.core.services.full_text_search.connection")
    def test_deactivate_settings(self, mock_connection):
        self._mock_connection(mock_connection)
        Settings(feature_full_text_search=True).save()

        deactivate_full_text_search()

        self.assertFalse(Settings.load().feature_full_text_search)

    def test_activate_not_postgresql(self):
        with self.assertRaises(FullTextSearchError) as e:
            activate_full_text_search()

        self.assertEqual("Full text search is only available with PostgreSQL", str(e.exception))
        self.assertFalse(Settings.load().feature_full_text_search)

    def test_deactivate_not_postgresql(self):
        Settings(feature_full_text_search=True).save()

        with self.assertRaises(FullTextSearchError):
            deactivate_full_text_search()

        self.assertTrue(Settings.load().feature_full_text_search)
