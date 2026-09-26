import logging
from typing import Any

from django.core.management.base import BaseCommand
from huey.contrib.djhuey import HUEY as huey
from huey.contrib.stats import HueyInflight

from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status

logger = logging.getLogger("secobserve.background_tasks")

STALE_MESSAGE = "Task did not finish, the container was restarted while it was running"


class Command(BaseCommand):
    help = (
        "Reset what an ungraceful shutdown left behind: periodic tasks that are still marked as "
        "running, and in-flight entries of the Huey statistics."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        self._flush_periodic_tasks()
        self._flush_inflight()

    def _flush_periodic_tasks(self) -> None:
        # so_periodic_task() writes the entry before the task runs and updates it afterwards, so a
        # task that was killed leaves it at "Running" forever. Nothing resets it: the entry is
        # reported as running for days, and the endpoint to run a task manually answers 409 for it
        # as long as it is there.
        stale = Periodic_Task.objects.filter(status=Status.STATUS_RUNNING).update(
            status=Status.STATUS_FAILURE, message=STALE_MESSAGE
        )
        logger.info("Reset %s periodic tasks that were still marked as running", stale)

    def _flush_inflight(self) -> None:
        # The consumer and the web server share one container and there is only one backend
        # container per pod, so nothing of this queue can legitimately be in flight during startup.
        # Entries still present are leftovers of tasks that never emitted a terminal signal, for
        # example because the container was killed while they were executing. Neither the huey
        # consumer nor the statistics themselves clean them up, so they would be reported as
        # running for hours by the background task statistics.
        if getattr(huey, "_stats", None) is None:
            logger.info("Huey statistics are not enabled, no in-flight entries to flush")
            return

        # Since peewee 4, Model.delete() uses a custom descriptor instead of @classmethod,
        # which pylint cannot resolve and therefore reports a missing `cls` argument.
        deleted = (
            HueyInflight.delete()  # pylint: disable=no-value-for-parameter
            .where(HueyInflight.queue == huey.name)
            .execute()
        )
        logger.info("Flushed %s stale in-flight entries of queue %s", deleted, huey.name)
