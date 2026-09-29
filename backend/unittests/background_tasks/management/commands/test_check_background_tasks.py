import time
from datetime import timedelta
from unittest.mock import MagicMock, patch

import peewee
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from huey.contrib.stats import HueyInflight

from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status

COMMAND = "check_background_tasks"
MODULE = "application.background_tasks.management.commands.check_background_tasks"


@override_settings(HUEY_TASK_MAX_RUNTIME_HOURS=12)
class TestCheckBackgroundTasksCommand(TestCase):
    def setUp(self) -> None:
        # The Huey statistics use peewee, not the Django ORM, see test_flush_huey_inflight
        self.database = peewee.SqliteDatabase(":memory:")
        self.bind_ctx = self.database.bind_ctx([HueyInflight])
        self.bind_ctx.__enter__()
        self.database.create_tables([HueyInflight])

        self.huey = MagicMock()
        self.huey.name = "secobserve"
        self.huey._stats = MagicMock()
        self.huey._stats.db.connect_params = {}
        huey_patch = patch(f"{MODULE}.huey", self.huey)
        huey_patch.start()
        self.addCleanup(huey_patch.stop)

    def tearDown(self) -> None:
        self.database.drop_tables([HueyInflight])
        self.bind_ctx.__exit__(None, None, None)
        self.database.close()

    def _inflight(self, task_id: str, hours_ago: float, queue: str = "secobserve") -> None:
        HueyInflight.create(
            task_id=task_id, queue=queue, task=f"module.{task_id}", started=time.time() - hours_ago * 3600
        )

    def _periodic_task(self, task: str, hours_ago: float, status: str = Status.STATUS_RUNNING) -> None:
        Periodic_Task.objects.create(task=task, start_time=timezone.now() - timedelta(hours=hours_ago), status=status)

    def test_nothing_stale(self) -> None:
        self._inflight("recent", 11)
        self._periodic_task("Housekeeping", 11)
        self._periodic_task("Import SPDX licenses", 24, Status.STATUS_SUCCESS)
        self._periodic_task("Import EPSS and cvss-bt", 24, Status.STATUS_FAILURE)

        call_command(COMMAND)

    def test_stale_inflight_task(self) -> None:
        self._inflight("recent", 11)
        self._inflight("stuck", 13)

        with self.assertRaises(CommandError) as context:
            call_command(COMMAND)

        self.assertEqual(1, context.exception.returncode)
        lines = str(context.exception).splitlines()
        self.assertEqual("Tasks running for longer than HUEY_TASK_MAX_RUNTIME_HOURS (12):", lines[0])
        self.assertEqual(2, len(lines))
        self.assertRegex(lines[1], r"^Task module\.stuck \(stuck\) is running since \d{4}-\d\d-\d\dT")

    def test_stale_periodic_task(self) -> None:
        self._periodic_task("Housekeeping", 11)
        self._periodic_task("Calculate product metrics", 13)

        with self.assertRaises(CommandError) as context:
            call_command(COMMAND)

        lines = str(context.exception).splitlines()
        self.assertEqual(2, len(lines))
        self.assertRegex(lines[1], r'^Periodic task "Calculate product metrics" is running since \d{4}-\d\d-\d\dT')

    @override_settings(HUEY_TASK_MAX_RUNTIME_HOURS=1.5)
    def test_max_runtime_from_settings(self) -> None:
        self._inflight("two_hours", 2)

        with self.assertRaisesRegex(CommandError, r"HUEY_TASK_MAX_RUNTIME_HOURS \(1\.5\)(.|\n)*module\.two_hours"):
            call_command(COMMAND)

    def test_other_queues_are_ignored(self) -> None:
        self._inflight("stuck", 24, queue="other_queue")

        call_command(COMMAND)

    def test_inflight_tasks_are_ignored_when_statistics_are_disabled(self) -> None:
        self._inflight("stuck", 24)
        self.huey._stats = None

        call_command(COMMAND)

    def test_database_access_is_bounded(self) -> None:
        cases = [
            ("postgresql", {"connect_timeout": 5, "options": "-c statement_timeout=10s"}),
            ("mysql", {"connect_timeout": 5, "read_timeout": 10}),
            ("sqlite", {}),
        ]
        for vendor, expected in cases:
            options = connection.settings_dict["OPTIONS"]
            with self.subTest(vendor=vendor), patch.dict(options), patch.object(connection, "vendor", vendor):
                self.huey._stats.db.connect_params = {}
                unchanged = dict(options)

                call_command(COMMAND)

                self.assertEqual(unchanged | expected, options)
                self.assertEqual(expected, self.huey._stats.db.connect_params)


class TestHueyStatsSettings(SimpleTestCase):
    def test_inflight_entries_outlive_the_max_runtime(self) -> None:
        self.assertGreater(settings.HUEY_STATS["inflight_hours"], settings.HUEY_TASK_MAX_RUNTIME_HOURS)
