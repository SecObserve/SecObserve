from huey.contrib.djhuey import on_commit_task

from application.access_control.services.current_user import get_current_user
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Product
from application.notifications.models import Notification
from application.notifications.services.product_notification import (
    get_users_for_product_notification,
)
from application.notifications.services.send_notifications_base import (
    _get_email_to_addresses,
    _get_first_name,
    _get_notification_email_to,
    _get_notification_ms_teams_webhook,
    _get_notification_slack_webhook,
    get_msteams_template,
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
    send_user_notification,
)
from application.notifications.services.tasks import handle_task_exception
from application.notifications.types import Product_Notification_Type


@on_commit_task()
def send_product_security_gate_notification(product: Product) -> None:
    try:
        settings = Settings.load()

        if product.security_gate_passed is None:
            security_gate_status = "None"
        elif product.security_gate_passed:
            security_gate_status = "Passed"
        else:
            security_gate_status = "Failed"

        notification_email_to = _get_notification_email_to(product)
        email_to_addresses = _get_email_to_addresses(notification_email_to)
        notified_email_addresses: set[str] = set()
        if email_to_addresses and settings.email_from:
            for email_to_address in email_to_addresses:
                first_name = _get_first_name(email_to_address)
                send_email_notification(
                    email_to_address,
                    f"Security gate for product {product.name} has changed to {security_gate_status}",
                    "email/product_security_gate.tpl",
                    product=product,
                    security_gate_status=security_gate_status,
                    product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
                    first_name=first_name,
                )
                notified_email_addresses.add(email_to_address.lower())

        notified_webhooks: set[str] = set()

        notification_ms_teams_webhook = _get_notification_ms_teams_webhook(product)
        if notification_ms_teams_webhook:
            template = get_msteams_template(notification_ms_teams_webhook, "product_security_gate")
            send_msteams_notification(
                notification_ms_teams_webhook,
                template,
                product=product,
                security_gate_status=security_gate_status,
                product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
            )
            notified_webhooks.add(notification_ms_teams_webhook)

        notification_slack_webhook = _get_notification_slack_webhook(product)
        if notification_slack_webhook:
            send_slack_notification(
                notification_slack_webhook,
                "slack/product_security_gate.tpl",
                product=product,
                security_gate_status=security_gate_status,
                product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
            )
            notified_webhooks.add(notification_slack_webhook)

        users = get_users_for_product_notification(product, Product_Notification_Type.SECURITY_GATE_CHANGED)
        for user in users:
            send_user_notification(
                user,
                settings,
                f"Security gate for product {product.name} has changed to {security_gate_status}",
                "product_security_gate",
                notified_email_addresses=notified_email_addresses,
                notified_webhooks=notified_webhooks,
                product=product,
                security_gate_status=security_gate_status,
                product_url=f"{get_base_url_frontend()}#/products/{product.id}/show",
                first_name=f" {user.first_name}" if user.first_name else f" {user.full_name}",
            )

        Notification.objects.create(
            name=f"Security gate has changed to {security_gate_status}",
            product=product,
            user=get_current_user(),
            type=Notification.TYPE_SECURITY_GATE,
        )
    except Exception as e:
        handle_task_exception(e)
        raise
