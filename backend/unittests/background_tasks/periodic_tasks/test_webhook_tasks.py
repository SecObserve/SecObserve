from unittest.mock import patch

from application.background_tasks.periodic_tasks.webhook_tasks import (
    task_dispatch_webhooks,
)
from unittests.base_test_case import BaseTestCase


class TestWebhookTasks(BaseTestCase):
    @patch("application.background_tasks.periodic_tasks.webhook_tasks.handle_task_exception")
    @patch("application.background_tasks.periodic_tasks.webhook_tasks.dispatch_webhooks")
    def test_task_dispatch_webhooks_reports_and_reraises(self, mock_dispatch_webhooks, mock_handle_task_exception):
        error = RuntimeError("boom")
        mock_dispatch_webhooks.side_effect = error

        with self.assertRaises(RuntimeError):
            task_dispatch_webhooks.call_local()

        mock_handle_task_exception.assert_called_once_with(error)
