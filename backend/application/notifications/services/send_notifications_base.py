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

# Host suffixes for Microsoft Teams "Workflows" (Power Automate) webhook trigger
# URLs, used only as a fallback to the "/workflows/" path check below:
#   current: <env>.environment.api.powerplatform.com
#   legacy:  prod-NN.<region>.logic.azure.com   (HTTP-trigger URLs, retired 2025-11-30)
# Legacy Office 365 "Incoming Webhook" connectors are on *.webhook.office.com and
# take a MessageCard instead; they are detected by the absence of these signals.
_MSTEAMS_WORKFLOW_HOST_SUFFIXES = (
    ".environment.api.powerplatform.com",
    ".logic.azure.com",
)


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
    if not _validate_webhook_url(webhook):
        return

    # Workflows webhooks need an Adaptive Card; legacy connectors keep the
    # MessageCard template the caller passed in.
    is_workflow = _is_msteams_workflow_webhook(webhook)
    if is_workflow:
        template = _get_msteams_workflow_template(template)

    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        try:
            request_kwargs: dict[str, Any] = {
                "method": "POST",
                "url": webhook,
                "data": notification_message,
                "allow_redirects": False,
                "timeout": 60,
            }
            if is_workflow:
                # Power Automate only parses the body as JSON when told to; the
                # legacy connector accepts it without an explicit content type.
                request_kwargs["headers"] = {"Content-Type": "application/json"}
            response = requests.request(**request_kwargs)
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


def _is_msteams_workflow_webhook(webhook: str) -> bool:
    split_url = urlsplit(webhook)
    # Primary, format-stable signal: both the current and legacy trigger URLs
    # carry ".../workflows/<id>/triggers/manual/paths/invoke" in their path.
    # Checking split_url.path (not the raw URL) keeps the query string out of it.
    if "/workflows/" in split_url.path.lower():
        return True
    # Host fallback in case Microsoft changes the path. urlsplit().hostname is
    # already lower-cased and port-stripped (so an explicit :443 is ignored).
    hostname = (split_url.hostname or "").lower()
    return hostname.endswith(_MSTEAMS_WORKFLOW_HOST_SUFFIXES)


def _get_msteams_workflow_template(template: str) -> str:
    # Map a MessageCard template to its Adaptive Card sibling, e.g.
    # "msteams_observation.tpl" -> "msteams_observation_workflow.tpl".
    if template.endswith(".tpl"):
        return f"{template[:-len('.tpl')]}_workflow.tpl"
    return f"{template}_workflow"


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
