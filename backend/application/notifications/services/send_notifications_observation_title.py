from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation
from application.core.types import Severity, Status
from application.notifications.models import Notification, Observation_Title_Notified
from application.notifications.services.send_notifications import (
    _get_email_to_addresses,
    _get_first_name,
)
from application.notifications.services.send_notifications_base import (
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
)


def send_observation_title_notification(observation: Observation) -> None:
    settings = Settings.load()

    observation_title_notification_min_severity = settings.observation_title_notification_min_severity
    observation_title_notification_numerical_min_severity = (
        Severity.NUMERICAL_SEVERITIES.get(observation_title_notification_min_severity)
        if observation_title_notification_min_severity
        else None
    )
    observation_title_notification_statuses = settings.observation_title_notification_statuses
    observation_title_notification_min_priority = settings.observation_title_notification_min_priority
    observation_title_notification_parser_type = settings.observation_title_notification_parser_type

    if (
        (  # pylint: disable=too-many-boolean-expressions
            observation_title_notification_numerical_min_severity
            or observation_title_notification_statuses
            or observation_title_notification_min_priority
            or observation_title_notification_parser_type
        )
        and (
            not observation_title_notification_numerical_min_severity
            or observation.numerical_severity <= observation_title_notification_numerical_min_severity
        )
        and (
            (
                observation_title_notification_statuses
                and observation.current_status in observation_title_notification_statuses
            )
            or (not observation_title_notification_statuses and observation.current_status in Status.STATUS_ACTIVE)
        )
        and (
            not observation_title_notification_min_priority
            or not observation.current_priority
            or observation.current_priority <= observation_title_notification_min_priority
        )
        and (
            not observation_title_notification_parser_type
            or observation.parser.type == observation_title_notification_parser_type
        )
    ):
        try:
            observation_title_notified = Observation_Title_Notified.objects.get(title=observation.title)
            new_notification = False
        except Observation_Title_Notified.DoesNotExist:
            observation_title_notified = Observation_Title_Notified(title=observation.title)
            new_notification = True

        if (
            observation.current_severity != observation_title_notified.severity
            or observation.current_status != observation_title_notified.status
            or observation.current_priority != observation_title_notified.priority
        ):
            first_line = (
                f'New notification for observation title "{observation.title}"'
                if new_notification
                else f'Change in observation title "{observation.title}"'
            )

            url = (
                get_base_url_frontend()
                + '#/observations?filter={"current_status":["Open","Affected","In+review"],"title":"'
                + observation.title
                + '"}'
            )

            _send_observation_title_notifications(settings, observation, first_line, url)

            observation_title_notified.severity = observation.current_severity
            observation_title_notified.status = observation.current_status
            observation_title_notified.priority = observation.current_priority
            observation_title_notified.save()
    else:
        try:
            observation_title_notified = Observation_Title_Notified.objects.get(title=observation.title)
        except Observation_Title_Notified.DoesNotExist:
            return

        first_line = f'Observation title "{observation.title}" fell out of notifications'

        url = get_base_url_frontend() + '#/observations?filter={"title":"' + observation.title + '"}'

        _send_observation_title_notifications(settings, observation, first_line, url)

        observation_title_notified.delete()


def _send_observation_title_notifications(
    settings: Settings, observation: Observation, first_line: str, url: str
) -> None:
    email_to_addresses = _get_email_to_addresses(settings.observation_title_notification_email_to)
    if email_to_addresses and settings.email_from:
        for email_to_address in email_to_addresses:
            first_name = _get_first_name(email_to_address)
            send_email_notification(
                email_to_address,
                first_line,
                "email_observation_title.tpl",
                observation=observation,
                url=url,
                first_line=first_line,
                first_name=first_name,
            )

    if settings.observation_title_notification_ms_teams_webhook:
        send_msteams_notification(
            settings.observation_title_notification_ms_teams_webhook,
            "msteams_observation_title.tpl",
            observation=observation,
            url=url,
            first_line=first_line,
        )

    if settings.observation_title_notification_slack_webhook:
        send_slack_notification(
            settings.observation_title_notification_slack_webhook,
            "slack_observation_title.tpl",
            observation=observation,
            url=url,
            first_line=first_line,
        )

    Notification.objects.create(
        name=first_line,
        user=get_current_user(),
        type=Notification.TYPE_OBSERVATION_TITLE,
    )
