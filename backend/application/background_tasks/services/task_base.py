import functools
import inspect
import logging
import sys
from datetime import timedelta
from typing import Any, Callable, cast

from django.utils import timezone
from huey.contrib.djhuey import lock_task

from application.background_tasks.models import Periodic_Task
from application.background_tasks.types import Status
from application.commons.models import Settings
from application.commons.services.log_message import format_log_message
from application.notifications.services.send_notifications import (
    send_task_exception_notification,
)

logger = logging.getLogger("secobserve.background_tasks")

# max_length is typed as Optional, but it is always set for the CharField "message"
MESSAGE_MAX_LENGTH = cast(int, Periodic_Task._meta.get_field("message").max_length)

# Names of all periodic tasks, used to check that the registry is complete
PERIODIC_TASK_NAMES: set[str] = set()


def _truncate_message(message: str) -> str:
    if len(message) <= MESSAGE_MAX_LENGTH:
        return message
    return f"{message[:MESSAGE_MAX_LENGTH - 4]} ..."


def so_periodic_task(name: str) -> Callable:
    PERIODIC_TASK_NAMES.add(name)

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

            delete_older_task_entries(name)

            try:
                message = func()

                periodic_task.status = Status.STATUS_SUCCESS
                periodic_task.duration = (timezone.now() - periodic_task.start_time) / timedelta(milliseconds=1)
                periodic_task.message = _truncate_message(str(message)) if message else ""
                periodic_task.save()
            except Exception as e:
                periodic_task.status = Status.STATUS_FAILURE
                periodic_task.duration = (timezone.now() - periodic_task.start_time) / timedelta(milliseconds=1)
                periodic_task.message = _truncate_message(str(e))
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


def delete_older_task_entries(name: str) -> None:
    settings = Settings.load()
    recent_task_ids = list(
        Periodic_Task.objects.filter(task=name)
        .order_by("-start_time")
        .values_list("id", flat=True)[: settings.periodic_task_max_entries]
    )
    Periodic_Task.objects.filter(task=name).exclude(id__in=recent_task_ids).delete()
