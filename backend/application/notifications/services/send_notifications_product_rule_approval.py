from typing import Optional

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
    send_user_notification,
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

        first_line = f'Product rule "{rule.name}" needs approval'

        for user in _get_approvers_to_notify(rule, product):
            _send_rule_notification(user, settings, rule, first_line)
    except Exception as e:
        handle_task_exception(e)
        raise


@on_commit_task()
def send_product_rule_approval_receipt_notification(rule: Rule) -> None:
    try:
        product = rule.product
        if not product or rule.approval_status not in (
            Rule_Status.RULE_STATUS_APPROVED,
            Rule_Status.RULE_STATUS_REJECTED,
        ):
            return

        settings = Settings.load()

        author = _get_author_to_notify(rule, product)
        if not author:
            return

        first_line = f'Product rule "{rule.name}" has been {rule.approval_status.lower()}'

        _send_rule_notification(author, settings, rule, first_line)
    except Exception as e:
        handle_task_exception(e)
        raise


def _send_rule_notification(user: User, settings: Settings, rule: Rule, first_line: str) -> None:
    send_user_notification(
        user,
        settings,
        first_line,
        "product_rule",
        rule=rule,
        rule_url=f"{get_base_url_frontend()}#/product_rules/{rule.pk}/show",
        first_line=first_line,
        first_name=f" {user.first_name}" if user.first_name else f" {user.full_name}",
    )


def _get_approvers_to_notify(rule: Rule, product: Product) -> set[User]:
    users = get_users_for_product_notification(product, Product_Notification_Type.PRODUCT_RULE_TO_BE_REVIEWED)

    return {
        user
        for user in users
        if user != rule.user and user_has_permission(product, Permissions.Product_Rule_Approval, user)
    }


def _get_author_to_notify(rule: Rule, product: Product) -> Optional[User]:
    users = get_users_for_product_notification(product, Product_Notification_Type.PRODUCT_RULE_APPROVAL_RECEIPT)

    return next((user for user in users if user == rule.user), None)
