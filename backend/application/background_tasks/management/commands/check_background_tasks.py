from datetime import UTC, datetime, timedelta
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
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


class Command(BaseCommand):
    help = (
        "Exit with an error when a task of this queue has been running for longer than "
        "HUEY_TASK_MAX_RUNTIME_HOURS. Used as liveness probe of the Huey consumer, whose health check "
        "only restarts worker threads that died, not the ones that are blocked forever."
    )
    requires_system_checks: list[str] = []

    def handle(self, *args: Any, **options: Any) -> None:
        # Fail fast instead of hanging on a dead database connection like the tasks this looks for
        connection_params = _bounded_connection_params(connection.vendor)
        connection.settings_dict["OPTIONS"].update(connection_params)

        max_hours = settings.HUEY_TASK_MAX_RUNTIME_HOURS
        cutoff = timezone.now() - timedelta(hours=max_hours)
        stale = [
            f'Periodic task "{periodic_task.task}" is running since {_format(periodic_task.start_time)}'
            for periodic_task in Periodic_Task.objects.filter(
                status=Status.STATUS_RUNNING, start_time__lt=cutoff
            ).order_by("start_time")
        ]

        stats = getattr(huey, "_stats", None)
        if stats is not None:
            stats.db.connect_params.update(connection_params)
            stale += [
                f"Task {inflight.task} ({inflight.task_id}) is running since "
                f"{_format(datetime.fromtimestamp(inflight.started, UTC))}"
                for inflight in HueyInflight.select()
                .where(HueyInflight.queue == huey.name, HueyInflight.started < cutoff.timestamp())
                .order_by(HueyInflight.started)
            ]

        if stale:
            raise CommandError(
                f"Tasks running for longer than HUEY_TASK_MAX_RUNTIME_HOURS ({max_hours}):\n" + "\n".join(stale)
            )


def _format(start: datetime) -> str:
    return start.isoformat(timespec="seconds")
