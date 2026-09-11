from huey.contrib.djhuey import on_commit_task

from application.access_control.models import User
from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import Observation
from application.notifications.services.product_notification import (
    get_users_for_product_notification,
)
from application.notifications.services.send_notifications_base import (
    send_email_notification,
)
from application.notifications.services.tasks import handle_task_exception
from application.notifications.types import Product_Notification_Type


@on_commit_task()
def send_observation_review_notification(observation: Observation) -> None:
    try:
        settings = Settings.load()
        if not settings.email_from:
            return

        first_line = f'Observation "{observation.title}" has been set to "In review"'
        observation_url = f"{get_base_url_frontend()}#/observations/{observation.pk}/show"

        for user in _get_reviewers_to_notify(observation):
            print(vars(user))


        for user in _get_reviewers_to_notify(observation):
            send_email_notification(
                user.email,
                first_line,
                "email_observation.tpl",
                observation=observation,
                observation_url=observation_url,
                first_line=first_line,
                first_name=f" {user.first_name}" if user.first_name else f" {user.full_name}",
            )
    except Exception as e:
        handle_task_exception(e)
        raise


def _get_reviewers_to_notify(observation: Observation) -> set[User]:
    users = get_users_for_product_notification(
        observation.product, Product_Notification_Type.OBSERVATION_TO_BE_REVIEWED
    )

    return {
        user for user in users if user_has_permission(observation.product, Permissions.Observation_Assessment, user)
    }
