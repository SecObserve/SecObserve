import logging
import traceback
from datetime import datetime, timedelta
from typing import Any, Optional

from huey.contrib.djhuey import on_commit_task

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.commons.services.functions import get_classname
from application.commons.services.log_message import format_log_message
from application.core.models import Product
from application.notifications.models import Notification
from application.notifications.services.send_notifications_base import (
    _get_email_to_addresses,
    _get_first_name,
    is_msteams_v2,
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
)

logger = logging.getLogger("secobserve.notifications")


LAST_EXCEPTIONS: dict[str, datetime] = {}


@on_commit_task()
def send_email_notification_background(notification_email_to: str, subject: str, template: str, **kwargs: Any) -> None:
    try:
        send_email_notification(notification_email_to, subject, template, **kwargs)
    except Exception as e:
        logger.error(
            format_log_message(
                message=f"Error while sending email to {notification_email_to}",
                exception=e,
            )
        )


@on_commit_task()
def send_msteams_notification_background(webhook: str, template: str, **kwargs: Any) -> None:
    try:
        send_msteams_notification(webhook, template, **kwargs)
    except Exception as e:
        logger.error(
            format_log_message(
                message=f"Error while calling MS Teams webhook {webhook}",
                exception=e,
            )
        )


@on_commit_task()
def send_slack_notification_background(webhook: str, template: str, **kwargs: Any) -> None:
    try:
        send_slack_notification(webhook, template, **kwargs)
    except Exception as e:
        logger.error(
            format_log_message(
                message=f"Error while calling Slack webhook {webhook}",
                exception=e,
            )
        )


def send_exception_notification(exception: Exception) -> None:
    settings = Settings.load()

    if _ratelimit_exception(exception):
        email_to_adresses = _get_email_to_addresses(settings.exception_email_to)
        if email_to_adresses and settings.email_from:
            for notification_email_to in email_to_adresses:
                first_name = _get_first_name(notification_email_to)
                send_email_notification_background(
                    notification_email_to,
                    f'Exception "{get_classname(exception)}" has occured',
                    "email_exception.tpl",
                    exception_class=get_classname(exception),
                    exception_message=str(exception),
                    exception_trace=_get_stack_trace(exception, False),
                    date_time=datetime.now(),
                    first_name=first_name,
                )

        if settings.exception_ms_teams_webhook:
            template = (
                "msteams_v2_exception.tpl"
                if is_msteams_v2(settings.exception_ms_teams_webhook)
                else "msteams_exception.tpl"
            )
            send_msteams_notification_background(
                settings.exception_ms_teams_webhook,
                template,
                exception_class=get_classname(exception),
                exception_message=str(exception),
                exception_trace=_get_stack_trace(exception, True),
                date_time=datetime.now(),
            )

        if settings.exception_slack_webhook:
            send_slack_notification_background(
                settings.exception_slack_webhook,
                "slack_exception.tpl",
                exception_class=get_classname(exception),
                exception_message=str(exception),
                exception_trace=_get_stack_trace(exception, True),
                date_time=datetime.now(),
            )

        Notification.objects.create(
            name=f'Exception "{get_classname(exception)}" has occured',
            message=str(exception),
            user=get_current_user(),
            type=Notification.TYPE_EXCEPTION,
        )


def send_task_exception_notification(
    function: Optional[str],
    arguments: Optional[dict],
    user: Optional[User],
    exception: Exception,
    product: Optional[Product] = None,
) -> None:
    settings = Settings.load()

    if _ratelimit_exception(exception, function, arguments):
        email_to_adresses = _get_email_to_addresses(settings.exception_email_to)
        if email_to_adresses and settings.email_from:
            for notification_email_to in email_to_adresses:
                first_name = _get_first_name(notification_email_to)
                send_email_notification_background(
                    notification_email_to,
                    f'Exception "{get_classname(exception)}" has occured in background task',
                    "email_task_exception.tpl",
                    function=function,
                    arguments=str(arguments),
                    user=user,
                    exception_class=get_classname(exception),
                    exception_message=str(exception),
                    exception_trace=_get_stack_trace(exception, False),
                    date_time=datetime.now(),
                    first_name=first_name,
                )

        if settings.exception_ms_teams_webhook:
            template = (
                "msteams_v2_task_exception.tpl"
                if is_msteams_v2(settings.exception_ms_teams_webhook)
                else "msteams_task_exception.tpl"
            )
            send_msteams_notification_background(
                settings.exception_ms_teams_webhook,
                template,
                function=function,
                arguments=str(arguments),
                user=user,
                exception_class=get_classname(exception),
                exception_message=str(exception),
                exception_trace=_get_stack_trace(exception, True),
                date_time=datetime.now(),
            )

        if settings.exception_slack_webhook:
            send_slack_notification_background(
                settings.exception_slack_webhook,
                "slack_task_exception.tpl",
                function=function,
                arguments=str(arguments),
                user=user,
                exception_class=get_classname(exception),
                exception_message=str(exception),
                exception_trace=_get_stack_trace(exception, True),
                date_time=datetime.now(),
            )

        observation = None

        if arguments:
            if not product:
                product = arguments.get("product")

            observation = arguments.get("observation")
            if observation and not product:
                product = observation.product

        Notification.objects.create(
            name=f'Exception "{get_classname(exception)}" has occured',
            message=str(exception),
            function=str(function),
            arguments=_get_arguments_string(arguments),
            product=product,
            observation=observation,
            user=user,
            type=Notification.TYPE_TASK,
        )


def _ratelimit_exception(exception: Exception, function: str = None, arguments: dict = None) -> bool:
    settings = Settings.load()

    key = get_classname(exception) + "/" + str(exception) + "/" + str(function) + "/" + _get_arguments_string(arguments)
    now = datetime.now()

    if key in LAST_EXCEPTIONS:
        last_datetime = LAST_EXCEPTIONS[key]
        difference: timedelta = now - last_datetime
        if difference.total_seconds() >= settings.exception_rate_limit:
            LAST_EXCEPTIONS[key] = now
            return True

        return False

    LAST_EXCEPTIONS[key] = now
    return True


def _get_stack_trace(exc: Exception, format_as_code: bool) -> str:
    delimiter = ""
    stack_trace = delimiter.join(traceback.format_tb(exc.__traceback__))

    if stack_trace and format_as_code:
        stack_trace = f"```\n{stack_trace}\n```"

    return stack_trace


def _get_arguments_string(arguments: Optional[dict]) -> str:
    if arguments:
        return str(arguments)
    return ""
