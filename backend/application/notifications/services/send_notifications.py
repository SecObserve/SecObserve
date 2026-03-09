import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional

from application.access_control.models import User
from application.access_control.queries.user import get_user_by_email
from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend, get_classname
from application.core.models import Observation, Product
from application.core.types import Severity
from application.notifications.models import Notification, Observation_Notified
from application.notifications.services.send_notifications_base import (
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
)

logger = logging.getLogger("secobserve.notifications")


LAST_EXCEPTIONS: dict[str, datetime] = {}


def send_product_security_gate_notification(product: Product) -> None:
    settings = Settings.load()

    if product.security_gate_passed is None:
        security_gate_status = "None"
    elif product.security_gate_passed:
        security_gate_status = "Passed"
    else:
        security_gate_status = "Failed"

    notification_email_to = _get_notification_email_to(product)
    email_to_addresses = _get_email_to_addresses(notification_email_to)
    if email_to_addresses and settings.email_from:
        for email_to_address in email_to_addresses:
            first_name = _get_first_name(email_to_address)
            send_email_notification(
                email_to_address,
                f"Security gate for {product.name} has changed to {security_gate_status}",
                "email_product_security_gate.tpl",
                product=product,
                security_gate_status=security_gate_status,
                product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
                first_name=first_name,
            )

    notification_ms_teams_webhook = _get_notification_ms_teams_webhook(product)
    if notification_ms_teams_webhook:
        send_msteams_notification(
            notification_ms_teams_webhook,
            "msteams_product_security_gate.tpl",
            product=product,
            security_gate_status=security_gate_status,
            product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
        )

    notification_slack_webhook = _get_notification_slack_webhook(product)
    if notification_slack_webhook:
        send_slack_notification(
            notification_slack_webhook,
            "slack_product_security_gate.tpl",
            product=product,
            security_gate_status=security_gate_status,
            product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
        )

    Notification.objects.create(
        name=f"Security gate has changed to {security_gate_status}",
        product=product,
        user=get_current_user(),
        type=Notification.TYPE_SECURITY_GATE,
    )


def send_observation_notification(observation: Observation) -> None:
    observation_notification_min_severity = _get_observation_notification_min_severity(observation.product)
    observation_notification_numerical_min_severity = (
        Severity.NUMERICAL_SEVERITIES.get(observation_notification_min_severity)
        if observation_notification_min_severity
        else None
    )
    observation_notification_statuses = _get_observation_notification_statuses(observation.product)
    observation_notification_min_priority = _get_observation_notification_min_priority(observation.product)

    if (
        (  # pylint: disable=too-many-boolean-expressions
            observation_notification_numerical_min_severity
            or observation_notification_statuses
            or observation_notification_min_priority
        )
        and (
            not observation_notification_numerical_min_severity
            or observation.numerical_severity <= observation_notification_numerical_min_severity
        )
        and (not observation_notification_statuses or observation.current_status in observation_notification_statuses)
        and (
            not observation_notification_min_priority
            or not observation.current_priority
            or observation.current_priority <= observation_notification_min_priority
        )
    ):
        try:
            observation_notified = Observation_Notified.objects.get(observation=observation)
            new_notification = False
        except Observation_Notified.DoesNotExist:
            observation_notified = Observation_Notified(observation=observation)
            new_notification = True

        if (
            observation.current_severity != observation_notified.severity
            or observation.current_status != observation_notified.status
            or observation.current_priority != observation_notified.priority
        ):
            first_line = (
                f'New notification for observation "{observation.title}"'
                if new_notification
                else f'Change in observation "{observation.title}"'
            )

            _send_observation_notifications(observation, first_line)

            observation_notified.severity = observation.current_severity
            observation_notified.status = observation.current_status
            observation_notified.priority = observation.current_priority
            observation_notified.save()
    else:
        try:
            observation_notified = Observation_Notified.objects.get(observation=observation)
        except Observation_Notified.DoesNotExist:
            return

        first_line = f'Observation "{observation.title}" fell out of notifications'

        _send_observation_notifications(observation, first_line)

        observation_notified.delete()


def _send_observation_notifications(observation: Observation, first_line: str) -> None:
    settings = Settings.load()

    notification_email_to = _get_notification_email_to(observation.product)
    email_to_addresses = _get_email_to_addresses(notification_email_to)
    if email_to_addresses and settings.email_from:
        for email_to_address in email_to_addresses:
            first_name = _get_first_name(email_to_address)
            send_email_notification(
                email_to_address,
                first_line,
                "email_observation.tpl",
                observation=observation,
                observation_url=f"{get_base_url_frontend()}#/observations/{observation.pk}/show",
                first_line=first_line,
                first_name=first_name,
            )

    notification_ms_teams_webhook = _get_notification_ms_teams_webhook(observation.product)
    if notification_ms_teams_webhook:
        send_msteams_notification(
            notification_ms_teams_webhook,
            "msteams_observation.tpl",
            observation=observation,
            observation_url=f"{get_base_url_frontend()}#/observations/{observation.pk}/show",
            first_line=first_line,
        )

    notification_slack_webhook = _get_notification_slack_webhook(observation.product)
    if notification_slack_webhook:
        send_slack_notification(
            notification_slack_webhook,
            "slack_observation.tpl",
            observation=observation,
            observation_url=f"{get_base_url_frontend()}#/observations/{observation.pk}/show",
            first_line=first_line,
        )

    first_line = first_line.replace(f' "{observation.title}"', "")

    Notification.objects.create(
        name=first_line,
        product=observation.product,
        observation=observation,
        user=get_current_user(),
        type=Notification.TYPE_OBSERVATION,
    )


def send_exception_notification(exception: Exception) -> None:
    settings = Settings.load()

    if _ratelimit_exception(exception):
        email_to_adresses = _get_email_to_addresses(settings.exception_email_to)
        if email_to_adresses and settings.email_from:
            for notification_email_to in email_to_adresses:
                first_name = _get_first_name(notification_email_to)
                send_email_notification(
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
            send_msteams_notification(
                settings.exception_ms_teams_webhook,
                "msteams_exception.tpl",
                exception_class=get_classname(exception),
                exception_message=str(exception),
                exception_trace=_get_stack_trace(exception, True),
                date_time=datetime.now(),
            )

        if settings.exception_slack_webhook:
            send_slack_notification(
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
                send_email_notification(
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
            send_msteams_notification(
                settings.exception_ms_teams_webhook,
                "msteams_task_exception.tpl",
                function=function,
                arguments=str(arguments),
                user=user,
                exception_class=get_classname(exception),
                exception_message=str(exception),
                exception_trace=_get_stack_trace(exception, True),
                date_time=datetime.now(),
            )

        if settings.exception_slack_webhook:
            send_slack_notification(
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
        if difference.seconds >= settings.exception_rate_limit:
            LAST_EXCEPTIONS[key] = now
            return True

        return False

    LAST_EXCEPTIONS[key] = now
    return True


def _get_observation_notification_min_severity(product: Product) -> Optional[str]:
    if product.observation_notification_min_severity:
        return product.observation_notification_min_severity

    if product.product_group and product.product_group.observation_notification_min_severity:
        return product.product_group.observation_notification_min_severity

    return None


def _get_observation_notification_statuses(product: Product) -> Optional[str]:
    if product.observation_notification_statuses:
        return product.observation_notification_statuses

    if product.product_group and product.product_group.observation_notification_statuses:
        return product.product_group.observation_notification_statuses

    return None


def _get_observation_notification_min_priority(product: Product) -> Optional[int]:
    if product.observation_notification_min_priority:
        return product.observation_notification_min_priority

    if product.product_group and product.product_group.observation_notification_min_priority:
        return product.product_group.observation_notification_min_priority

    return None


def _get_notification_email_to(product: Product) -> Optional[str]:
    if product.notification_email_to:
        return product.notification_email_to

    if product.product_group and product.product_group.notification_email_to:
        return product.product_group.notification_email_to

    return None


def _get_notification_ms_teams_webhook(product: Product) -> Optional[str]:
    if product.notification_ms_teams_webhook:
        return product.notification_ms_teams_webhook

    if product.product_group and product.product_group.notification_ms_teams_webhook:
        return product.product_group.notification_ms_teams_webhook

    return None


def _get_notification_slack_webhook(product: Product) -> Optional[str]:
    if product.notification_slack_webhook:
        return product.notification_slack_webhook

    if product.product_group and product.product_group.notification_slack_webhook:
        return product.product_group.notification_slack_webhook

    return None


def _get_email_to_addresses(
    notification_email_to: Optional[str],
) -> Optional[list[str]]:
    if not notification_email_to:
        return None

    email_to_adresses = notification_email_to.split(",")
    return [item.strip() for item in email_to_adresses]


def _get_first_name(email: str) -> str:
    user = get_user_by_email(email)
    if user and user.first_name:
        return f" {user.first_name}"
    return ""


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
