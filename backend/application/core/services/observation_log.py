from datetime import date
from typing import Optional

from application.access_control.models import User
from application.access_control.services.current_user import get_current_user
from application.core.models import Observation, Observation_Log


def create_observation_log(
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

    return observation_log


# Needed because create_observation_log is called from a background task
def _get_user() -> Optional[User]:
    user = get_current_user()
    if not user:
        user = User.objects.filter(is_superuser=True).first()
    return user
