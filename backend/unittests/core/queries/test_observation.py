from unittest.mock import patch

from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Observation_Log
from application.core.queries.observation import get_observation_logs
from unittests.base_test_case import BaseTestCase


class TestGetObservationLogs(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def _get_observation_log_ids(self, observation_logs):
        return list(observation_logs.values_list("id", flat=True))

    @patch("application.core.queries.observation.get_current_user")
    def test_no_user(self, mock_user):
        mock_user.return_value = None

        self.assertEqual([], self._get_observation_log_ids(get_observation_logs()))

    @patch("application.core.queries.observation.get_current_user")
    def test_superuser(self, mock_user):
        mock_user.return_value = User.objects.get(username="db_admin")

        self.assertEqual([1, 2, 3, 4], self._get_observation_log_ids(get_observation_logs()))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_product_member(self, mock_user, mock_product_user):
        user = User.objects.get(username="db_internal_write")
        mock_user.return_value = user
        mock_product_user.return_value = user

        self.assertEqual([1, 2], self._get_observation_log_ids(get_observation_logs()))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_product_group_member(self, mock_user, mock_product_user):
        user = User.objects.get(username="db_product_group_user")
        mock_user.return_value = user
        mock_product_user.return_value = user

        self.assertEqual([1, 2], self._get_observation_log_ids(get_observation_logs()))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.core.queries.observation.get_current_user")
    def test_other_product_member(self, mock_user, mock_product_user):
        user = User.objects.get(username="db_external")
        mock_user.return_value = user
        mock_product_user.return_value = user

        self.assertEqual([3, 4], self._get_observation_log_ids(get_observation_logs()))

    def test_list_number_of_queries(self):
        # The number of queries must not depend on the number of observation logs on the page
        Observation_Log.objects.filter(id=1).update(approval_user=User.objects.get(username="db_admin"))
        client = APIClient()
        client.force_authenticate(User.objects.get(username="db_product_group_user"))

        with CaptureQueriesContext(connection) as context:
            response = client.get("/api/observation_logs/", HTTP_HOST="localhost")

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.json()["count"])
        self.assertEqual(
            "db_product_group", response.json()["results"][0]["observation_data"]["product_data"]["product_group_name"]
        )
        self.assertEqual("db_admin", response.json()["results"][0]["approval_user_full_name"])
        # authorized products, count, observation logs (product group and approval user are joined)
        sql_queries = [query["sql"] for query in context.captured_queries if query["sql"].startswith("SELECT")]
        self.assertEqual(3, len(sql_queries), sql_queries)
