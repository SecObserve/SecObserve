from datetime import date
from typing import Optional

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.core.models import Observation, Observation_Log
from application.core.types import Assessment_Status
from application.notifications.services.send_notifications_observation import (
    send_observation_notification,
)
from application.notifications.services.send_notifications_observation_title import (
    send_observation_title_notification,
)


def create_observation_log(  # pylint: disable=too-many-arguments
    *,
    observation: Observation,
    severity: str,
    status: str,
    priority: Optional[int] = None,
    comment: str,
    vex_justification: str,
    assessment_status: str,
    risk_acceptance_expiry_date: Optional[date],
) -> Observation_Log:
    observation_log = Observation_Log(
        observation=observation,
        user=_get_user(),
        severity=severity,
        status=status,
        priority=priority,
        comment=comment,
        vex_justification=vex_justification,
        assessment_status=assessment_status,
        general_rule=observation.general_rule,
        product_rule=observation.product_rule,
        vex_statement=observation.vex_statement,
        risk_acceptance_expiry_date=risk_acceptance_expiry_date,
    )
    observation_log.save()

    observation.last_observation_log = observation_log.created
    observation.save()

    observation.product.last_observation_change = observation_log.created
    observation.product.save()

    if assessment_status in (
        Assessment_Status.ASSESSMENT_STATUS_APPROVED,
        Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        Assessment_Status.ASSESSMENT_STATUS_REMOVED,
    ):
        send_observation_notification(observation)
        send_observation_title_notification(observation)

    return observation_log


# Needed because create_observation_log is called from a background task
def _get_user() -> Optional[User]:
    user = get_current_user()
    if not user:
        user = User.objects.filter(is_superuser=True).first()
    return user
