from unittest.mock import MagicMock, patch

import peewee
from django.core.management import call_command
from django.test import TestCase
from huey.contrib.stats import HueyInflight

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
