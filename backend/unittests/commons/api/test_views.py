from unittest.mock import patch

from django.test import override_settings
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
)
from rest_framework.test import APIClient

from unittests.base_test_case import BaseTestCase


class TestViews(BaseTestCase):
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_version(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.get("/api/status/version/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual({"version": "unittest_version"}, response.data)

    @override_settings(TIME_ZONE="Asia/Ho_Chi_Minh")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_status_settings_time_zone(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        response = APIClient().get("/api/status/settings/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual("Asia/Ho_Chi_Minh", response.data["time_zone"])

    @override_settings(BACKGROUND_TASKS_TIME_ZONE="Asia/Ho_Chi_Minh")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_status_settings_background_tasks_time_zone(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        response = APIClient().get("/api/status/settings/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual("Asia/Ho_Chi_Minh", response.data["background_tasks_time_zone"])

    def test_status_settings_background_tasks_time_zone_unauthenticated(self):
        response = APIClient().get("/api/status/settings/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertNotIn("background_tasks_time_zone", response.data)

    def test_health(self):
        api_client = APIClient()
        response = api_client.get("/api/status/health/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(None, response.data)

    def test_empty(self):
        api_client = APIClient()
        response = api_client.get("/")

        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)
