import logging
from typing import Any

from django.core.management.base import BaseCommand
from huey.contrib.djhuey import HUEY as huey
from huey.contrib.stats import HueyInflight

logger = logging.getLogger("secobserve.background_tasks")


class Command(BaseCommand):
    help = "Delete stale in-flight entries of the Huey statistics, left over from an ungraceful shutdown."

    def handle(self, *args: Any, **options: Any) -> None:
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
