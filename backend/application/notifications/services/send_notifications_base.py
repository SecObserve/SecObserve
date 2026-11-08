import ipaddress
import logging
import socket
from collections.abc import Callable
from typing import Any, Optional
from urllib.parse import urlsplit

import environ
import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from requests.adapters import HTTPAdapter
from urllib3.exceptions import ConnectTimeoutError, LocationParseError
from urllib3.util import parse_url

from application.access_control.models import User
from application.access_control.queries.user import get_user_by_email
from application.commons.models import Settings
from application.commons.services.log_message import format_log_message
from application.core.models import Product

logger = logging.getLogger("secobserve.notifications")


def send_email_notification(notification_email_to: str, subject: str, template: str, **kwargs: Any) -> None:
    settings = Settings.load()
    notification_message = _create_notification_message(template, **kwargs)
    env = environ.Env()
    if (env("EMAIL_HOST", default="") or env("EMAIL_PORT", default="")) and notification_message:
        send_mail(
            subject=subject,
            message=notification_message,
            from_email=settings.email_from,
            recipient_list=[notification_email_to],
            fail_silently=False,
        )


def _is_msteams_v2(webhook: str) -> bool:
    """Detect V1 (MessageCard) vs V2 (Power Automate) by URL. Legacy webhook.office.com = V1; everything else = V2."""
    try:
        hostname = urlsplit(webhook).hostname or ""
        return not hostname.endswith("webhook.office.com")
    except Exception:
        return True


def get_msteams_template(webhook: str, name: str) -> str:
    """MS Teams templates come in two formats, the webhook URL decides which one is used."""
    return f"msteams_v2/{name}.tpl" if _is_msteams_v2(webhook) else f"msteams/{name}.tpl"


def send_msteams_notification(webhook: str, template: str, **kwargs: Any) -> None:
    addresses = _get_webhook_addresses(webhook)
    if not addresses:
        return
    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        headers = {"Content-Type": "application/json"} if _is_msteams_v2(webhook) else {}
        response = _post_webhook(webhook, addresses, notification_message, headers)
        response.raise_for_status()


def send_slack_notification(webhook: str, template: str, **kwargs: Any) -> None:
    addresses = _get_webhook_addresses(webhook)
    if not addresses:
        return
    notification_message = _create_notification_message(template, **kwargs)
    if notification_message:
        response = _post_webhook(webhook, addresses, notification_message, {})
        response.raise_for_status()


def send_user_notification(
    user: User,
    settings: Settings,
    subject: str,
    template_base: str,
    *,
    notified_email_addresses: Optional[set[str]] = None,
    notified_webhooks: Optional[set[str]] = None,
    **kwargs: Any,
) -> None:
    """
    Send one user specific notification to all channels the user has activated. The name of the
    template is derived from the channel and the given base, e.g. `email/observation.tpl` and
    `slack/observation.tpl` for the base `observation`.

    Channels that have already been notified through the shared destinations of the product are
    skipped, so that a user does not get the same notification twice.
    """
    if (
        user.notification_email_active
        and user.email
        and settings.email_from
        and (not notified_email_addresses or user.email.lower() not in notified_email_addresses)
    ):
        send_email_notification(user.email, subject, f"email/{template_base}.tpl", **kwargs)

    if (
        user.notification_ms_teams_active
        and user.notification_ms_teams_webhook
        and (not notified_webhooks or user.notification_ms_teams_webhook not in notified_webhooks)
    ):
        template = get_msteams_template(user.notification_ms_teams_webhook, template_base)
        _send_user_webhook_notification(
            send_msteams_notification, user, user.notification_ms_teams_webhook, template, **kwargs
        )

    if (
        user.notification_slack_active
        and user.notification_slack_webhook
        and (not notified_webhooks or user.notification_slack_webhook not in notified_webhooks)
    ):
        _send_user_webhook_notification(
            send_slack_notification, user, user.notification_slack_webhook, f"slack/{template_base}.tpl", **kwargs
        )


def _send_user_webhook_notification(
    send_notification: Callable[..., None], user: User, webhook: str, template: str, **kwargs: Any
) -> None:
    """
    Notifications are sent to many users in one go, so the webhook of one user must not be able to
    abort the notifications of all the other users.
    """
    try:
        send_notification(webhook, template, **kwargs)
    except Exception as e:
        logger.error(
            format_log_message(
                message=f"Error while sending notification to a webhook of user {user.username}",
                exception=e,
            )
        )


def send_msteams_notification_test(webhook: str) -> None:
    addresses = _get_webhook_addresses(webhook)
    if not addresses:
        raise ValueError(f"Invalid webhook URL: {webhook}")
    v2 = _is_msteams_v2(webhook)
    template = "msteams_v2/test.tpl" if v2 else "msteams/test.tpl"
    notification_message = _create_notification_message(template)
    if notification_message:
        headers = {"Content-Type": "application/json"} if v2 else {}
        response = _post_webhook(webhook, addresses, notification_message, headers)
        response.raise_for_status()


def send_slack_notification_test(webhook: str) -> None:
    addresses = _get_webhook_addresses(webhook)
    if not addresses:
        raise ValueError(f"Invalid webhook URL: {webhook}")
    notification_message = _create_notification_message("slack/test.tpl")
    if notification_message:
        response = _post_webhook(webhook, addresses, notification_message, {})
        response.raise_for_status()


def _get_webhook_addresses(webhook: str) -> list[str]:
    """
    Returns the addresses a webhook may be sent to, or an empty list if the URL must not be used. The URL is
    parsed like requests parses it and all addresses of the host have to be public. The request is then sent
    to these addresses with _post_webhook().
    """
    try:
        url = parse_url(webhook)
    except LocationParseError:
        url = None
    if not url or url.scheme != "https" or not url.host or url.auth:
        logger.error(
            format_log_message(
                message=f"Webhook URL must use https, a valid host and no user info: {webhook}",
            )
        )
        return []

    try:
        address_infos = socket.getaddrinfo(url.host.strip("[]"), url.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        logger.error(
            format_log_message(
                message=f"Could not resolve webhook host: {webhook}",
                exception=e,
            )
        )
        return []

    addresses = []
    for address_info in address_infos:
        ip_addr = ipaddress.ip_address(address_info[4][0])
        # is_global lets multicast and reserved ranges like the NAT64 prefix 64:ff9b::/96 pass
        if not ip_addr.is_global or ip_addr.is_reserved or ip_addr.is_multicast:
            logger.error(
                format_log_message(
                    message=f"Webhook host resolves to a non-public address, refusing request: {webhook}",
                )
            )
            return []
        addresses.append(str(ip_addr))

    return addresses


class _PinnedHostAdapter(HTTPAdapter):
    """Verifies the TLS certificate against the host name, while the URL contains the address to connect to."""

    def __init__(self, hostname: str) -> None:
        self.hostname = hostname
        super().__init__()

    def build_connection_pool_key_attributes(
        self, request: requests.PreparedRequest, verify: bool | str, cert: str | tuple[str, str] | None = None
    ) -> tuple[Any, Any]:
        host_params, typed_pool_kwargs = super().build_connection_pool_key_attributes(request, verify, cert)
        # urllib3 accepts these keys, the type stubs of requests only know the ones requests sets itself
        pool_kwargs: dict[str, Any] = dict(typed_pool_kwargs)
        if host_params["scheme"] == "https":
            pool_kwargs["server_hostname"] = self.hostname
            pool_kwargs["assert_hostname"] = self.hostname
        return host_params, pool_kwargs


def _post_webhook(webhook: str, addresses: list[str], data: str, headers: dict[str, str]) -> requests.Response:
    # A second DNS lookup by requests could return another address than the one that has been checked
    url = parse_url(webhook)
    host = url.host or ""
    host_header = f"{host}:{url.port}" if url.port else host
    with requests.Session() as session:
        session.mount("https://", _PinnedHostAdapter(host.strip("[]")))
        for i, address in enumerate(addresses):
            try:
                return session.request(
                    method="POST",
                    url=url._replace(host=f"[{address}]" if ":" in address else address).url,
                    data=data,
                    headers={**headers, "Host": host_header},
                    allow_redirects=False,
                    timeout=60,
                )
            except requests.ConnectionError as e:
                # Only a connection that could not be opened is retried, a request must not be sent twice
                reason = getattr(e.args[0], "reason", None) if e.args else None
                if i == len(addresses) - 1 or not isinstance(reason, ConnectTimeoutError):
                    raise
    raise ValueError(f"No address to send the webhook to: {webhook}")


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
