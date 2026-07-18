from unittest.mock import MagicMock, patch

from rest_framework.status import HTTP_200_OK, HTTP_403_FORBIDDEN
from rest_framework.test import APIClient

from unittests.base_test_case import BaseTestCase

URL = "/api/status/background_task_statistics/"


class TestBackgroundTaskView(BaseTestCase):
    @patch("application.background_tasks.api.views.enable_stats")
    @patch("application.background_tasks.api.views.SqliteDatabase")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_background_task_statistics(self, mock_authentication, mock_db, mock_enable_stats):
        mock_authentication.return_value = self.user_admin, None

        stats = MagicMock()
        stats.task_breakdown.return_value = [
            {
                "task": "task_a",
                "full": "module.task_a",
                "executed": 10,
                "completed": 8,
                "errors": 2,
                "retries": 1,
                "avg": 1.5,
            }
        ]
        stats.throughput.return_value = {"complete": [1, 2, 3], "error": [0, 0, 1]}
        # window_counts only contains the signals that actually occurred; missing
        # signals must be serialized as 0.
        stats.window_counts.return_value = {"complete": 8, "error": 2, "executing": 10}
        stats.inflight.return_value = [{"task": "task_b", "id": "abc123", "started": 1000.0, "elapsed": 5.0}]
        mock_enable_stats.return_value = stats

        api_client = APIClient()
        response = api_client.get(URL)

        self.assertEqual(HTTP_200_OK, response.status_code)
        stats.throughput.assert_called_once_with(minutes=60)
        stats.window_counts.assert_called_once_with(seconds=86400)
        expected_data = "{'registered': [{'task': 'task_a', 'full': 'module.task_a', 'executed': 10, 'completed': 8, 'errors': 2, 'retries': 1, 'avg': 1.5}], 'throughput': {'complete': [1, 2, 3], 'error': [0, 0, 1]}, 'counts': {'enqueued': 0, 'scheduled': 0, 'executing': 10, 'complete': 8, 'error': 2, 'retrying': 0, 'revoked': 0, 'canceled': 0, 'expired': 0, 'locked': 0, 'interrupted': 0}, 'running': [{'task': 'task_b', 'id': 'abc123', 'started': 1000.0, 'elapsed': 5.0}]}"
        self.assertEqual(expected_data, str(response.data))

    @patch("application.background_tasks.api.views.enable_stats")
    @patch("application.background_tasks.api.views.SqliteDatabase")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_background_task_statistics_forbidden(self, mock_authentication, mock_db, mock_enable_stats):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.get(URL)

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        mock_enable_stats.assert_not_called()
