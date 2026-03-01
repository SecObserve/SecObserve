from datetime import date

from application.core.models import Observation
from application.core.services.assessment import remove_assessment, save_assessment
from application.core.types import Status


def expire_risk_acceptances() -> str:
    observations = Observation.objects.filter(
        current_status=Status.STATUS_RISK_ACCEPTED,
        risk_acceptance_expiry_date__lte=date.today(),
    )
    for observation in observations:
        assessment_removed = remove_assessment(observation, "Risk acceptance has expired.")
        if not assessment_removed:
            observation.parser_status = Status.STATUS_OPEN
            observation.save()
            save_assessment(
                observation=observation,
                new_severity="",
                new_status=Status.STATUS_OPEN,
                new_priority=None,
                comment="Risk acceptance has expired.",
                new_vex_justification="",
                new_risk_acceptance_expiry_date=None,
            )

    return f"Expired risk acceptances for {observations.count()} observations."
