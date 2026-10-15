from importlib import import_module
from unittest.mock import patch

from django.core.management import call_command
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.api.filters import ObservationFilter
from application.core.models import Observation
from application.core.queries.observation import (
    get_observation_log_search_vector,
    get_observation_search_vector,
)
from unittests.base_test_case import BaseTestCase

migration = import_module("application.core.migrations.0100_observation_full_text_search")


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

        queryset = ObservationFilter().get_full_text_search(
            Observation.objects.all(), "full_text_search", '"sql injection" -xss'
        )

        sql = str(queryset.query)
        self.assertIn("to_tsvector", sql)
        self.assertIn("regexp_replace((websearch_to_tsquery(", sql)
        self.assertIn("::tsquery", sql)
        self.assertIn('"U0"."vulnerability_id_aliases"', sql)
        self.assertIn(" UNION ", sql)
        self.assertIn(
            'FROM "core_observation_log" "U0" WHERE to_tsvector(simple::regconfig, COALESCE("U0"."comment"', sql
        )

    def test_search_vectors_match_indexes(self):
        self.assertEqual(migration.get_observation_search_vector(), get_observation_search_vector())
        self.assertEqual(migration.get_observation_log_search_vector(), get_observation_log_search_vector())
