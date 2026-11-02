from importlib import import_module
from unittest.mock import patch

from django.core.management import call_command
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.api.filters import ObservationFilter
from application.core.models import Observation
from application.core.queries.observation import (
    OBSERVATION_FULL_TEXT_SEARCH_FIELDS,
    OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS,
    _get_full_text_search_terms,
)
from unittests.base_test_case import BaseTestCase

migration = import_module("application.core.migrations.0101_observation_full_text_search")


class TestObservationFilterFullTextSearch(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )
        super().setUpClass()

    def test_not_postgresql(self):
        with self.assertRaises(ValidationError) as e:
            ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", "injection")

        self.assertEqual(["Full text search is only available with PostgreSQL"], e.exception.detail)

    def test_not_postgresql_api(self):
        auth_path = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        with patch(auth_path) as mock_authenticate:
            mock_authenticate.return_value = User.objects.get(username="db_admin"), None
            response = APIClient().get("/api/observations/?full_text_search=injection")

        self.assertEqual(400, response.status_code)
        self.assertEqual({"message": "Full text search is only available with PostgreSQL"}, response.data)

    @patch("application.commons.services.functions.connection")
    def test_postgresql(self, mock_connection):
        mock_connection.vendor = "postgresql"

        queryset = ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", "jection")

        sql = str(queryset.query)
        for field in OBSERVATION_FULL_TEXT_SEARCH_FIELDS:
            self.assertIn(f'"U0"."{field}" LIKE %jection%', sql)
        self.assertIn(" UNION ", sql)
        self.assertIn('FROM "core_observation_log" "U0" WHERE "U0"."comment" LIKE %jection%', sql)

    @patch("application.commons.services.functions.connection")
    def test_postgresql_whole_word(self, mock_connection):
        mock_connection.vendor = "postgresql"

        queryset = ObservationFilter().get_full_text_search(
            Observation.objects.all(), "full_text_search", '"sql" jection'
        )

        sql = str(queryset.query)
        for field in OBSERVATION_FULL_TEXT_SEARCH_FIELDS:
            self.assertIn(f'"U0"."{field}" LIKE %sql%', sql)
            self.assertIn(f'"U0"."{field}" REGEXP \'(?i)\' || (?<!\\w)sql(?!\\w)', sql)
            self.assertIn(f'"U0"."{field}" LIKE %jection%', sql)
        self.assertEqual(2, sql.count(" UNION "))

    def _search(self, value):
        with patch("application.commons.services.functions.connection") as mock_connection:
            mock_connection.vendor = "postgresql"
            queryset = ObservationFilter().get_full_text_search(Observation.objects.all(), "full_text_search", value)
        return [observation.title for observation in queryset]

    def test_postgresql_result_part_of_word(self):
        self.assertEqual(["db_observation_external_active"], self._search("BSERVATION_EXTERNAL"))

    def test_postgresql_result_whole_word(self):
        self.assertEqual([], self._search('"external"'))
        self.assertEqual(["db_observation_external_active"], self._search('"DB_OBSERVATION_EXTERNAL_ACTIVE"'))

    def test_postgresql_result_all_terms(self):
        self.assertEqual(["db_observation_external_active"], self._search('external "db_observation_external_active"'))
        self.assertEqual([], self._search("external xyz_not_there"))

    def test_postgresql_result_no_terms(self):
        self.assertEqual(Observation.objects.count(), len(self._search(' "" ')))

    def test_get_full_text_search_terms(self):
        self.assertEqual([("sql", False), ("injection", False)], _get_full_text_search_terms(" sql  injection "))
        self.assertEqual([("sql", True)], _get_full_text_search_terms('"sql"'))
        self.assertEqual([("sql injection", True)], _get_full_text_search_terms('" sql injection "'))
        self.assertEqual(
            [("xss", False), ("sql", True), ("injection", False)],
            _get_full_text_search_terms('xss "sql" injection'),
        )
        self.assertEqual([("sql", False), ("inj", False)], _get_full_text_search_terms('"sql inj'))
        self.assertEqual([("CVE-2021-44228", False)], _get_full_text_search_terms("CVE-2021-44228"))
        self.assertEqual([], _get_full_text_search_terms('"" "  "'))
        self.assertEqual([], _get_full_text_search_terms(""))

    def test_fields_match_indexes(self):
        self.assertEqual(list(migration.OBSERVATION_FULL_TEXT_SEARCH_FIELDS), OBSERVATION_FULL_TEXT_SEARCH_FIELDS)
        self.assertEqual(
            list(migration.OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS), OBSERVATION_LOG_FULL_TEXT_SEARCH_FIELDS
        )
