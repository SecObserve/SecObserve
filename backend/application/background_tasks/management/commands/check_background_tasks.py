from datetime import UTC, datetime, timedelta
from typing import Any

import peewee
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connection
from django.utils import timezone
from huey.contrib.djhuey import HUEY as huey
from huey.contrib.stats import HueyInflight

from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status


def _bounded_connection_params(vendor: str) -> dict[str, Any]:
    # statement_timeout also bounds the time spent waiting for locks
    if vendor == "postgresql":
        return {"connect_timeout": 5, "options": "-c statement_timeout=10s"}
    if vendor == "mysql":
        return {"connect_timeout": 5, "read_timeout": 10}
    return {}


def _format(start: datetime) -> str:
    return start.isoformat(timespec="seconds")


class Command(BaseCommand):
    help = (
        "Exit with an error when a task of this queue has been running for longer than "
        "HUEY_TASK_MAX_RUNTIME_HOURS. Used as liveness probe of the Huey consumer, whose health check "
        "only restarts worker threads that died, not the ones that are blocked forever."
    )
    # Runs every few minutes as a probe, the system checks would only add to its runtime
    requires_system_checks: list[str] = []

    def handle(self, *args: Any, **options: Any) -> None:
        # Bounds the queries of this command. The statistics connection that opens while Django
        # starts is bounded by the connect timeout and the keepalive settings of the Huey database.
        connection_params = _bounded_connection_params(connection.vendor)
        connection.settings_dict["OPTIONS"].update(connection_params)
        stats = getattr(huey, "_stats", None)
        if stats is not None:
            stats.db.connect_params.update(connection_params)

        try:
            stale = self._stale_tasks(stats)
        except (OperationalError, peewee.OperationalError) as e:
            # A restart doesn't help while the database can't be reached
            self.stderr.write(f"Background tasks could not be checked: {e}")
            return

        if stale:
            raise CommandError(
                f"Tasks running for longer than HUEY_TASK_MAX_RUNTIME_HOURS "
                f"({settings.HUEY_TASK_MAX_RUNTIME_HOURS}):\n" + "\n".join(stale)
            )

    def _stale_tasks(self, stats: Any) -> list[str]:
        cutoff = timezone.now() - timedelta(hours=settings.HUEY_TASK_MAX_RUNTIME_HOURS)
        stale = [
            f'Periodic task "{periodic_task.task}" is running since {_format(periodic_task.start_time)}'
            for periodic_task in Periodic_Task.objects.filter(
                status=Status.STATUS_RUNNING, start_time__lt=cutoff
            ).order_by("start_time")
        ]
        if stats is not None:
            stale += [
                f"Task {inflight.task} ({inflight.task_id}) is running since "
                f"{_format(datetime.fromtimestamp(inflight.started, UTC))}"
                for inflight in HueyInflight.select()
                .where(HueyInflight.queue == huey.name, HueyInflight.started < cutoff.timestamp())
                .order_by(HueyInflight.started)
            ]
        return stale
