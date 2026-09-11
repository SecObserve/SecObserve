from huey.contrib.djhuey import on_commit_task

from application.access_control.models import User
from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Product
from application.notifications.services.product_notification import (
    get_users_for_product_notification,
)
from application.notifications.services.send_notifications_base import (
    send_email_notification,
)
from application.notifications.services.tasks import handle_task_exception
from application.notifications.types import Product_Notification_Type
from application.rules.models import Rule
from application.rules.types import Rule_Status


@on_commit_task()
def send_product_rule_approval_notification(rule: Rule) -> None:
    try:
        # General rules have no product, they cannot be notified per product
        product = rule.product
        if not product or rule.approval_status != Rule_Status.RULE_STATUS_NEEDS_APPROVAL:
            return

        settings = Settings.load()
        if not settings.email_from:
            return

        first_line = f'Product rule "{rule.name}" needs approval'
        rule_url = f"{get_base_url_frontend()}#/product_rules/{rule.pk}/show"

        for user in _get_approvers_to_notify(rule, product):
            send_email_notification(
                user.email,
                first_line,
                "email_product_rule.tpl",
                rule=rule,
                rule_url=rule_url,
                first_line=first_line,
                first_name=f" {user.first_name}" if user.first_name else f" {user.full_name}",
            )
    except Exception as e:
        handle_task_exception(e)
        raise


def _get_approvers_to_notify(rule: Rule, product: Product) -> set[User]:
    users = get_users_for_product_notification(product, Product_Notification_Type.PRODUCT_RULE_TO_BE_REVIEWED)

    return {
        user
        for user in users
        if user != rule.user and user_has_permission(product, Permissions.Product_Rule_Approval, user)
    }
