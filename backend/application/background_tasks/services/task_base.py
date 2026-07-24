import functools
import inspect
import logging
import sys
from datetime import timedelta
from typing import Any, Callable

from django.utils import timezone
from huey.contrib.djhuey import HUEY as huey
from huey.contrib.djhuey import lock_task
from huey.contrib.stats import HueyStats, enable_stats
from peewee import SqliteDatabase

from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status
from application.commons.models import Settings
from application.commons.services.log_message import format_log_message
from application.notifications.services.send_notifications import (
    send_task_exception_notification,
)

logger = logging.getLogger("secobserve.background_tasks")


def enable_statistics() -> HueyStats:
    stats_db = SqliteDatabase("/var/lib/huey/huey_stats.db")
    return enable_stats(huey, stats_db)


enable_statistics()


def so_periodic_task(name: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        @lock_task(name)
        def wrapper() -> None:
            logger.info("--- %s - start ---", name)

            periodic_task = Periodic_Task(
                task=name,
                start_time=timezone.now(),
                status=Status.STATUS_RUNNING,
            )
            periodic_task.save()

            _delete_older_entries(name)

            try:
                message = func()

                periodic_task.status = Status.STATUS_SUCCESS
                periodic_task.duration = (timezone.now() - periodic_task.start_time) / timedelta(milliseconds=1)
                periodic_task.message = str(message) if message else ""
                periodic_task.save()
            except Exception as e:
                periodic_task.status = Status.STATUS_FAILURE
                periodic_task.duration = (timezone.now() - periodic_task.start_time) / timedelta(milliseconds=1)
                periodic_task.message = str(e)
                periodic_task.save()

                _handle_periodic_task_exception(e)
                raise

            logger.info("--- %s - finished ---", name)

        return wrapper

    return decorator


def _handle_periodic_task_exception(e: Exception) -> None:
    data: dict[str, Any] = {}
    function = None

    if sys.exc_info() and len(sys.exc_info()) >= 2 and sys.exc_info()[2]:
        frames = inspect.getinnerframes(sys.exc_info()[2])  # type: ignore[arg-type]
        if frames and len(frames) >= 2:
            function = frames[1].function
            data["function"] = function

    logger.error(
        format_log_message(
            message="Error while executing periodic background task",
            data=data,
            exception=e,
            username=None,
        )
    )

    send_task_exception_notification(function=function, arguments=None, user=None, exception=e, product=None)


def _delete_older_entries(name: str) -> None:
    settings = Settings.load()
    recent_task_ids = list(
        Periodic_Task.objects.filter(task=name)
        .order_by("-start_time")
        .values_list("id", flat=True)[: settings.periodic_task_max_entries]
    )
    Periodic_Task.objects.filter(task=name).exclude(id__in=recent_task_ids).delete()
