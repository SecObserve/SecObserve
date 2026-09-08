import logging
from typing import Optional

from django.db import transaction

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.commons.models import Settings
from application.commons.services.functions import get_base_url_frontend
from application.core.models import (
    Observation_Log,
    Product,
    Product_Authorization_Group_Member,
)
from application.core.queries.assessment import (
    assessment_approvers_configured,
    get_effective_assessment_approvers,
)
from application.core.queries.product_member import (
    get_highest_role_of_product_authorization_group_members_for_user,
    get_product_member,
)
from application.core.types import Assessment_Status
from application.notifications.models import Notification, Notification_Recipient
from application.notifications.services.send_notifications import (
    _get_notification_ms_teams_webhook,
    _get_notification_slack_webhook,
)
from application.notifications.services.send_notifications_base import (
    is_msteams_v2,
    send_email_notification,
    send_msteams_notification,
    send_slack_notification,
)

logger = logging.getLogger("secobserve.notifications")


def get_eligible_assessment_approval_recipients(observation_log: Observation_Log) -> list[User]:
    """Return the active designated users who can approve this assessment."""
    product = observation_log.observation.product
    approver_user_ids, approver_group_ids = get_effective_assessment_approvers(product)
    candidate_user_ids = set(approver_user_ids)
    if approver_group_ids:
        candidate_user_ids.update(
            User.objects.filter(authorization_groups__id__in=approver_group_ids).values_list("id", flat=True)
        )

    if observation_log.user_id:
        candidate_user_ids.discard(observation_log.user_id)

    candidates = User.objects.filter(id__in=candidate_user_ids, is_active=True).order_by("id")
    return [
        user
        for user in candidates
        if _is_eligible_designated_approver(product, user, approver_user_ids, approver_group_ids)
    ]


def send_assessment_approval_request_notification(
    observation_log: Observation_Log,
    *,
    send_external: bool = True,
) -> Optional[Notification]:
    """Create one targeted notification for a pending designated-approval assessment."""
    if (
        observation_log.assessment_status != Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        or not assessment_approvers_configured(observation_log.observation.product)
    ):
        return None

    observation = observation_log.observation
    first_line = f'Assessment for observation "{observation.title}" needs approval'
    author_name = _get_user_name(observation_log.user)
    message = f"{author_name} submitted an assessment for approval."
    with transaction.atomic():
        notification, created = Notification.objects.get_or_create(
            type=Notification.TYPE_ASSESSMENT_REQUEST,
            observation_log=observation_log,
            defaults={
                "name": first_line,
                "message": message,
                "product": observation.product,
                "observation": observation,
                "user": observation_log.user,
            },
        )
        if not created:
            return notification

        recipients = get_eligible_assessment_approval_recipients(observation_log)
        _create_notification_recipients(notification, recipients)
    if not recipients:
        logger.warning(
            "Assessment approval request %s has no eligible designated recipients",
            observation_log.pk,
        )

    if send_external:
        _send_assessment_approval_notifications(
            observation_log=observation_log,
            recipients=recipients,
            first_line=first_line,
            message=message,
        )

    return notification


def send_assessment_approval_result_notification(observation_log: Observation_Log) -> Optional[Notification]:
    """Close a pending request and notify its author about the terminal outcome."""
    observation = observation_log.observation
    outcome = observation_log.assessment_status
    first_line = f'Assessment for observation "{observation.title}" was {outcome.lower()}'
    actor_name = _get_user_name(observation_log.approval_user)
    message = f"{actor_name} marked the assessment as {outcome}."
    if observation_log.rejection_remark:
        message += f" Remark: {observation_log.rejection_remark}"

    with transaction.atomic():
        request_notification = (
            Notification.objects.select_for_update()
            .filter(
                type=Notification.TYPE_ASSESSMENT_REQUEST,
                observation_log=observation_log,
            )
            .first()
        )
        if not request_notification:
            return None

        notification, created = Notification.objects.get_or_create(
            type=Notification.TYPE_ASSESSMENT_RESULT,
            observation_log=observation_log,
            defaults={
                "name": first_line,
                "message": message,
                "product": observation.product,
                "observation": observation,
                "user": observation_log.approval_user,
            },
        )
        request_notification.delete()
        if not created:
            return notification

        recipients = [observation_log.user] if observation_log.user and observation_log.user.is_active else []
        _create_notification_recipients(notification, recipients)
    _send_assessment_approval_notifications(
        observation_log=observation_log,
        recipients=recipients,
        first_line=first_line,
        message=message,
    )
    return notification


def _create_notification_recipients(notification: Notification, recipients: list[User]) -> None:
    Notification_Recipient.objects.bulk_create(
        [Notification_Recipient(notification=notification, user=recipient) for recipient in recipients],
        ignore_conflicts=True,
    )


def _send_assessment_approval_notifications(
    *,
    observation_log: Observation_Log,
    recipients: list[User],
    first_line: str,
    message: str,
) -> None:
    settings = Settings.load()
    assessment_url = f"{get_base_url_frontend()}#/observation_logs/{observation_log.pk}/show"

    if settings.email_from:
        for recipient in recipients:
            if recipient.email:
                first_name = f" {recipient.first_name}" if recipient.first_name else ""
                send_email_notification(
                    recipient.email,
                    first_line,
                    "email_assessment_approval.tpl",
                    assessment_url=assessment_url,
                    first_line=first_line,
                    first_name=first_name,
                    message=message,
                    observation_log=observation_log,
                )

    product = observation_log.observation.product
    notification_ms_teams_webhook = _get_notification_ms_teams_webhook(product)
    if notification_ms_teams_webhook:
        template = (
            "msteams_v2_assessment_approval.tpl"
            if is_msteams_v2(notification_ms_teams_webhook)
            else "msteams_assessment_approval.tpl"
        )
        send_msteams_notification(
            notification_ms_teams_webhook,
            template,
            assessment_url=assessment_url,
            first_line=first_line,
            message=message,
            observation_log=observation_log,
        )

    notification_slack_webhook = _get_notification_slack_webhook(product)
    if notification_slack_webhook:
        send_slack_notification(
            notification_slack_webhook,
            "slack_assessment_approval.tpl",
            assessment_url=assessment_url,
            first_line=first_line,
            message=message,
            observation_log=observation_log,
        )


def _get_user_name(user: Optional[User]) -> str:
    if not user:
        return "SecObserve"
    return user.full_name or user.username


def _is_eligible_designated_approver(
    product: Product,
    user: User,
    approver_user_ids: set[int],
    approver_group_ids: set[int],
) -> bool:
    if user.is_superuser:
        return True

    product_member = get_product_member(product, user)
    highest_role = product_member.role if product_member else 0
    if product.product_group:
        product_group_member = get_product_member(product.product_group, user)
        if product_group_member:
            highest_role = max(highest_role, product_group_member.role)
    highest_role = max(
        highest_role,
        get_highest_role_of_product_authorization_group_members_for_user(product, user),
    )

    if highest_role < Roles.Writer:
        return False
    if highest_role == Roles.Owner or user.pk in approver_user_ids:
        return True

    product_ids = [product.pk]
    if product.product_group_id:
        product_ids.append(product.product_group_id)
    return Product_Authorization_Group_Member.objects.filter(
        product_id__in=product_ids,
        authorization_group_id__in=approver_group_ids,
        authorization_group__users=user,
        role__gte=Roles.Writer,
    ).exists()
