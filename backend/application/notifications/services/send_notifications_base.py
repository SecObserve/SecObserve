import ipaddress
import logging
import socket
from typing import Any, Optional
from urllib.parse import urlsplit

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


def is_msteams_v2(webhook: str) -> bool:
    """Detect V1 (MessageCard) vs V2 (Power Automate) by URL. Legacy webhook.office.com = V1; everything else = V2."""
    try:
        hostname = urlsplit(webhook).hostname or ""
        return not hostname.endswith("webhook.office.com")
    except Exception:
        return True


@task()
def send_msteams_notification(webhook: str, template: str, **kwargs: Any) -> None:
    if not _validate_webhook_url(webhook):
        return
    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        headers = {"Content-Type": "application/json"} if is_msteams_v2(webhook) else {}
        try:
            response = requests.request(
                method="POST",
                url=webhook,
                data=notification_message,
                headers=headers,
                allow_redirects=False,
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
    if not _validate_webhook_url(webhook):
        return
    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        try:
            response = requests.request(
                method="POST",
                url=webhook,
                data=notification_message,
                allow_redirects=False,
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


def send_msteams_notification_test(webhook: str) -> None:
    if not _validate_webhook_url(webhook):
        raise ValueError(f"Invalid webhook URL: {webhook}")
    v2 = is_msteams_v2(webhook)
    template = "msteams_v2_test.tpl" if v2 else "msteams_test.tpl"
    notification_message = _create_notification_message(template)
    if notification_message:
        headers = {"Content-Type": "application/json"} if v2 else {}
        response = requests.request(
            method="POST",
            url=webhook,
            data=notification_message,
            headers=headers,
            allow_redirects=False,
            timeout=60,
        )
        response.raise_for_status()


def send_slack_notification_test(webhook: str) -> None:
    if not _validate_webhook_url(webhook):
        raise ValueError(f"Invalid webhook URL: {webhook}")
    notification_message = _create_notification_message("slack_test.tpl")
    if notification_message:
        response = requests.request(
            method="POST",
            url=webhook,
            data=notification_message,
            allow_redirects=False,
            timeout=60,
        )
        response.raise_for_status()


def _validate_webhook_url(webhook: str) -> bool:
    split_url = urlsplit(webhook)
    if split_url.scheme != "https" or not split_url.hostname:
        logger.error(
            format_log_message(
                message=f"Webhook URL must use https and a valid host: {webhook}",
            )
        )
        return False

    try:
        address_infos = socket.getaddrinfo(split_url.hostname, split_url.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        logger.error(
            format_log_message(
                message=f"Could not resolve webhook host: {webhook}",
                exception=e,
            )
        )
        return False

    for address_info in address_infos:
        ip_addr = ipaddress.ip_address(address_info[4][0])
        if (
            ip_addr.is_private  # pylint: disable=too-many-boolean-expressions
            or ip_addr.is_loopback
            or ip_addr.is_link_local
            or ip_addr.is_reserved
            or ip_addr.is_multicast
            or ip_addr.is_unspecified
        ):
            logger.error(
                format_log_message(
                    message=f"Webhook host resolves to a non-public address, refusing request: {webhook}",
                )
            )
            return False

    return True


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
