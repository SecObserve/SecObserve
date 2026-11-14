from typing import Any
from unittest.mock import patch

from huey.api import Task
from huey.contrib.djhuey import HUEY

from application.background_tasks.services.task_cache import (
    activate_cache,
    deactivate_cache,
)
from application.commons.models import Settings
from application.commons.services.request_cache import _get_request_cache
from unittests.base_test_case import BaseTestCase


class LoadSettingsTwice(Task):
    def execute(self) -> Any:
        Settings.load()
        Settings.load()


class FailingTask(Task):
    def execute(self) -> Any:
        Settings.load()
        raise ValueError("task failed")


class TestTaskCache(BaseTestCase):
    def tearDown(self) -> None:
        deactivate_cache(None, None, None)
        super().tearDown()

    def test_hooks_registered(self) -> None:
        self.assertIs(activate_cache, HUEY._pre_execute["activate_task_cache"])
        self.assertIs(deactivate_cache, HUEY._post_execute["deactivate_task_cache"])

    def test_activate_deactivate(self) -> None:
        activate_cache(None)
        self.assertIsNotNone(_get_request_cache())

        deactivate_cache(None, None, None)
        self.assertIsNone(_get_request_cache())

    @patch("application.commons.models.Settings.objects.get")
    def test_settings_loaded_once_per_task(self, mock_get) -> None:
        mock_get.return_value = Settings()

        HUEY.execute(LoadSettingsTwice())
        self.assertEqual(1, mock_get.call_count)
        self.assertIsNone(_get_request_cache())

        HUEY.execute(LoadSettingsTwice())
        self.assertEqual(2, mock_get.call_count)

    @patch("application.commons.models.Settings.objects.get")
    def test_cache_deactivated_after_failing_task(self, mock_get) -> None:
        mock_get.return_value = Settings()

        # Huey logs the exception of the task instead of raising it
        with self.assertLogs("huey", level="ERROR"):
            HUEY.execute(FailingTask())

        self.assertEqual(1, mock_get.call_count)

        self.assertIsNone(_get_request_cache())
