from typing import Optional

from huey.contrib.djhuey import on_commit_task

from application.access_control.models import User
from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation_Log
from application.notifications.services.product_notification import (
    get_users_for_product_notification,
)
from application.notifications.services.send_notifications_base import (
    send_email_notification,
)
from application.notifications.services.tasks import handle_task_exception
from application.notifications.types import Product_Notification_Type


@on_commit_task()
def send_assessment_approval_notification(observation_log: Observation_Log) -> None:
    try:
        settings = Settings.load()
        if not settings.email_from:
            return

        first_line = f'Assessment for observation "{observation_log.observation.title}" needs approval'

        for user in _get_approvers_to_notify(observation_log):
            _send_assessment_email(user, observation_log, first_line)
    except Exception as e:
        handle_task_exception(e)
        raise


@on_commit_task()
def send_assessment_approval_receipt_notification(observation_log: Observation_Log) -> None:
    try:
        settings = Settings.load()
        if not settings.email_from:
            return

        author = _get_author_to_notify(observation_log)
        if not author:
            return

        first_line = (
            f'Assessment for observation "{observation_log.observation.title}" '
            f"has been {observation_log.assessment_status.lower()}"
        )

        _send_assessment_email(author, observation_log, first_line)
    except Exception as e:
        handle_task_exception(e)
        raise


def _send_assessment_email(user: User, observation_log: Observation_Log, first_line: str) -> None:
    send_email_notification(
        user.email,
        first_line,
        "email_assessment_approval.tpl",
        observation=observation_log.observation,
        observation_log=observation_log,
        observation_log_url=f"{get_base_url_frontend()}#/observation_logs/{observation_log.pk}/show",
        first_line=first_line,
        first_name=f" {user.first_name}" if user.first_name else f" {user.full_name}",
    )


def _get_approvers_to_notify(observation_log: Observation_Log) -> set[User]:
    users = get_users_for_product_notification(
        observation_log.observation.product, Product_Notification_Type.ASSESSMENT_TO_BE_REVIEWED
    )

    return {
        user
        for user in users
        if user != observation_log.user
        and user_has_permission(observation_log.observation.product, Permissions.Observation_Log_Approval, user)
    }


def _get_author_to_notify(observation_log: Observation_Log) -> Optional[User]:
    users = get_users_for_product_notification(
        observation_log.observation.product, Product_Notification_Type.ASSESSMENT_APPROVAL_RECEIPT
    )

    return next((user for user in users if user == observation_log.user), None)
