from datetime import timedelta
from unittest.mock import MagicMock, patch

import peewee
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from huey.contrib.stats import HueyInflight

from application.background_tasks.management.commands.flush_huey_inflight import (
    STALE_MESSAGE,
)
from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status

COMMAND = "flush_huey_inflight"
MODULE = "application.background_tasks.management.commands.flush_huey_inflight"


class TestFlushHueyInflightCommand(TestCase):
    """Tests for the `flush_huey_inflight` management command.

    The command deletes the entries of the `huey_inflight` table for its own queue. They are
    written by the Huey statistics when a task starts and are only deleted when the task emits a
    terminal signal, which does not happen when the container is killed while the task is running.
    """

    def setUp(self) -> None:
        # The Huey statistics use peewee, not the Django ORM, so the table cannot be created by a
        # Django migration and has to be set up here.
        self.database = peewee.SqliteDatabase(":memory:")
        self.bind_ctx = self.database.bind_ctx([HueyInflight])
        self.bind_ctx.__enter__()
        self.database.create_tables([HueyInflight])

        self.huey = MagicMock()
        self.huey.name = "secobserve"
        self.huey._stats = MagicMock()

    def tearDown(self) -> None:
        self.database.drop_tables([HueyInflight])
        self.bind_ctx.__exit__(None, None, None)
        self.database.close()

    def test_stale_entries_of_own_queue_are_deleted(self) -> None:
        HueyInflight.create(task_id="task_1", queue="secobserve", task="module.Task_1", started=1000.0)
        HueyInflight.create(task_id="task_2", queue="secobserve", task="module.Task_2", started=2000.0)
        HueyInflight.create(task_id="task_3", queue="other_queue", task="module.Task_3", started=3000.0)

        with patch(f"{MODULE}.huey", self.huey):
            call_command(COMMAND)

        remaining = [entry.task_id for entry in HueyInflight.select()]
        self.assertEqual(["task_3"], remaining)

    def test_no_entries_is_not_an_error(self) -> None:
        with patch(f"{MODULE}.huey", self.huey):
            call_command(COMMAND)

        self.assertEqual(0, HueyInflight.select().count())

    def test_nothing_is_deleted_when_statistics_are_disabled(self) -> None:
        HueyInflight.create(task_id="task_1", queue="secobserve", task="module.Task_1", started=1000.0)
        self.huey._stats = None

        with patch(f"{MODULE}.huey", self.huey):
            call_command(COMMAND)

        self.assertEqual(1, HueyInflight.select().count())


class TestFlushStalePeriodicTasks(TestCase):
    """The command also resets periodic tasks that a killed container left at "Running".

    so_periodic_task() writes the entry before the task runs, so nothing updates it when the task
    never finishes. The entry would be reported as running forever and would keep the endpoint to
    run the task manually answering 409.
    """

    def setUp(self) -> None:
        self.huey = MagicMock()
        self.huey.name = "secobserve"
        self.huey._stats = None

    def _periodic_task(self, task: str, status: str) -> Periodic_Task:
        return Periodic_Task.objects.create(
            task=task,
            start_time=timezone.now() - timedelta(days=1),
            status=status,
            duration=None if status == Status.STATUS_RUNNING else 1000,
        )

    def test_running_tasks_are_reset(self) -> None:
        running = self._periodic_task("Import observations", Status.STATUS_RUNNING)

        with patch(f"{MODULE}.huey", self.huey):
            call_command(COMMAND)

        running.refresh_from_db()
        self.assertEqual(Status.STATUS_FAILURE, running.status)
        self.assertEqual(STALE_MESSAGE, running.message)

    def test_finished_tasks_are_left_alone(self) -> None:
        success = self._periodic_task("Housekeeping", Status.STATUS_SUCCESS)
        failure = self._periodic_task("Import EPSS and cvss-bt", Status.STATUS_FAILURE)

        with patch(f"{MODULE}.huey", self.huey):
            call_command(COMMAND)

        success.refresh_from_db()
        failure.refresh_from_db()
        self.assertEqual(Status.STATUS_SUCCESS, success.status)
        self.assertEqual("", success.message)
        self.assertEqual(Status.STATUS_FAILURE, failure.status)
        self.assertEqual("", failure.message)
