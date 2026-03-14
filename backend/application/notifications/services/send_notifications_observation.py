from typing import Optional

from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation, Product
from application.core.types import Severity, Status
from application.notifications.models import Notification, Observation_Notified
from application.notifications.services.send_notifications import (
    _get_email_to_addresses,
    _get_first_name,
    _get_notification_email_to,
    _get_notification_ms_teams_webhook,
    _get_notification_slack_webhook,
)
from application.notifications.services.send_notifications_base import (
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
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
        and (
            (observation_notification_statuses and observation.current_status in observation_notification_statuses)
            or (not observation_notification_statuses and observation.current_status in Status.STATUS_ACTIVE)
        )
        and (
            not observation_notification_min_priority
            or (observation.current_priority and observation.current_priority <= observation_notification_min_priority)
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
