from unittest.mock import MagicMock, patch

from django.utils import timezone
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_409_CONFLICT,
)
from rest_framework.test import APIClient

from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status
from unittests.base_test_case import BaseTestCase

URL = "/api/status/background_task_statistics/"


class TestBackgroundTaskView(BaseTestCase):
    @patch("application.background_tasks.api.views.huey")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_background_task_statistics(self, mock_authentication, mock_huey):
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
        mock_huey._stats = stats

        api_client = APIClient()
        response = api_client.get(URL)

        self.assertEqual(HTTP_200_OK, response.status_code)
        stats.throughput.assert_called_once_with(minutes=60)
        stats.window_counts.assert_called_once_with(seconds=86400)
        expected_data = "{'registered': [{'task': 'task_a', 'full': 'module.task_a', 'executed': 10, 'completed': 8, 'errors': 2, 'retries': 1, 'avg': 1.5}], 'throughput': {'complete': [1, 2, 3], 'error': [0, 0, 1]}, 'counts': {'enqueued': 0, 'scheduled': 0, 'executing': 10, 'complete': 8, 'error': 2, 'retrying': 0, 'revoked': 0, 'canceled': 0, 'expired': 0, 'locked': 0, 'interrupted': 0}, 'running': [{'task': 'task_b', 'id': 'abc123', 'started': 1000.0, 'elapsed': 5.0}]}"
        self.assertEqual(expected_data, str(response.data))

    @patch("application.background_tasks.api.views.huey")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_background_task_statistics_forbidden(self, mock_authentication, mock_huey):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.get(URL)

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        mock_huey._stats.task_breakdown.assert_not_called()


REGISTERED_TASKS_URL = "/api/periodic_tasks/registered_tasks/"
RUN_URL = "/api/periodic_tasks/run/"


class TestPeriodicTaskRun(BaseTestCase):
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_registered_tasks(self, mock_authentication):
        mock_authentication.return_value = self.user_admin, None

        api_client = APIClient()
        response = api_client.get(REGISTERED_TASKS_URL)

        self.assertEqual(HTTP_200_OK, response.status_code)
        expected_tasks = [
            "Branch housekeeping",
            "Calculate product metrics",
            "Expire risk acceptances",
            "Import EPSS and cvss-bt",
            "Import SPDX licenses",
            "Import observations from API configurations, OSV and VulnerableCode",
        ]
        self.assertEqual(expected_tasks, response.data["tasks"])

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_registered_tasks_forbidden(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.get(REGISTERED_TASKS_URL)

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)

    @patch("application.background_tasks.api.views.get_periodic_task")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_run_successful(self, mock_authentication, mock_get_periodic_task):
        mock_authentication.return_value = self.user_admin, None
        mock_task = MagicMock()
        mock_get_periodic_task.return_value = mock_task

        api_client = APIClient()
        response = api_client.post(RUN_URL, {"task": "Test task"}, format="json")

        self.assertEqual(HTTP_202_ACCEPTED, response.status_code)
        mock_get_periodic_task.assert_called_once_with("Test task")
        mock_task.assert_called_once_with()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_run_unknown_task(self, mock_authentication):
        mock_authentication.return_value = self.user_admin, None

        api_client = APIClient()
        response = api_client.post(RUN_URL, {"task": "Unknown task"}, format="json")

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_run_missing_task(self, mock_authentication):
        mock_authentication.return_value = self.user_admin, None

        api_client = APIClient()
        response = api_client.post(RUN_URL, {}, format="json")

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)

    @patch("application.background_tasks.api.views.get_periodic_task")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_run_already_running(self, mock_authentication, mock_get_periodic_task):
        mock_authentication.return_value = self.user_admin, None
        mock_task = MagicMock()
        mock_get_periodic_task.return_value = mock_task
        Periodic_Task(task="Test task", start_time=timezone.now(), status=Status.STATUS_RUNNING).save()

        api_client = APIClient()
        response = api_client.post(RUN_URL, {"task": "Test task"}, format="json")

        self.assertEqual(HTTP_409_CONFLICT, response.status_code)
        mock_task.assert_not_called()

    @patch("application.background_tasks.api.views.get_periodic_task")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_run_forbidden(self, mock_authentication, mock_get_periodic_task):
        mock_authentication.return_value = self.user_internal, None
        mock_task = MagicMock()
        mock_get_periodic_task.return_value = mock_task

        api_client = APIClient()
        response = api_client.post(RUN_URL, {"task": "Test task"}, format="json")

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        mock_task.assert_not_called()
