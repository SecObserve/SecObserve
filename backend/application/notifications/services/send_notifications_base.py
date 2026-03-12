import logging
from typing import Any, Optional

import environ
import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from huey.contrib.djhuey import db_task, task

from application.commons.models import Settings
from application.commons.services.log_message import format_log_message

logger = logging.getLogger("secobserve.notifications")


@db_task()
def send_email_notification(notification_email_to: str, subject: str, template: str, **kwargs: Any) -> None:
    settings = Settings.load()
    notification_message = _create_notification_message(template, **kwargs)
    env = environ.Env()
    if (env("EMAIL_HOST", default="") or env("EMAIL_PORT", default="")) and notification_message:
        try:
            send_mail(
                subject=subject,
                message=notification_message,
                from_email=settings.email_from,
                recipient_list=[notification_email_to],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(
                format_log_message(
                    message=f"Error while sending email to {notification_email_to}",
                    exception=e,
                )
            )


@task()
def send_msteams_notification(webhook: str, template: str, **kwargs: Any) -> None:
    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        notification_message = notification_message.replace("&quot;", '\\"')
        try:
            response = requests.request(
                method="POST",
                url=webhook,
                data=notification_message,
                timeout=60,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(
                format_log_message(
                    message=f"Error while calling MS Teams webhook {webhook}",
                    exception=e,
                )
            )


@task()
def send_slack_notification(webhook: str, template: str, **kwargs: Any) -> None:
    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        notification_message = notification_message.replace("&#x27;", "\\'")
        notification_message = notification_message.replace("&quot;", '\\"')
        try:
            response = requests.request(
                method="POST",
                url=webhook,
                data=notification_message,
                timeout=60,
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(
                format_log_message(
                    message=f"Error while calling Slack webhook {webhook}",
                    exception=e,
                )
            )


def _create_notification_message(template: str, **kwargs: Any) -> Optional[str]:
    try:
        return render_to_string(template, kwargs)
    except Exception as e:
        logger.error(
            format_log_message(
                message=f"Error while rendering template {template}",
                exception=e,
            )
        )
        return None
