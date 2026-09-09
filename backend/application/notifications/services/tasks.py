import inspect
import logging
from typing import Any

from application.access_control.models import User
from application.commons.services.log_message import format_log_message
from application.core.models import Product
from application.notifications.services.send_notifications_exception import (
    send_task_exception_notification,
)

logger = logging.getLogger("secobserve.tasks")


def handle_task_exception(e: Exception, user: User = None, product: Product = None) -> None:
    """
    Logs the exception and sends an exception notification. The caller has to re-raise the
    exception, so that Huey marks the background task as failed and logs the traceback. The
    traceback is not logged here, it would be logged a second time by Huey.

    A task that catches the exception per item to continue with the remaining ones has to
    log the traceback itself with logger.exception() and mark the task as failed when it
    has finished.
    """
    data: dict[str, Any] = {}
    function = None
    arguments = None
    current_frame = inspect.currentframe()
    if current_frame:
        frame = current_frame.f_back
        if frame:
            function = frame.f_code.co_name
            args, _, _, values = inspect.getargvalues(frame)
            arguments = {}
            for arg in args:
                arguments[arg] = values[arg]

            data["function"] = function
            data["arguments"] = arguments

    logger.error(
        format_log_message(
            message="Error while executing background task",
            data=data,
            exception=e,
            username=user.username if user else None,
        )
    )

    send_task_exception_notification(function=function, arguments=arguments, user=user, exception=e, product=product)
