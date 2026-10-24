from datetime import date

from application.core.models import Observation
from application.core.services.assessment import remove_assessment, save_assessment
from application.core.services.risk_acceptance_expiry import EXPIRY_STATUSES
from application.core.types import Status


def expire_risk_acceptances() -> str:
    observations = Observation.objects.filter(
        current_status__in=EXPIRY_STATUSES,
        risk_acceptance_expiry_date__lte=date.today(),
    )
    for observation in observations:
        comment = (
            "Risk acceptance has expired."
            if observation.current_status == Status.STATUS_RISK_ACCEPTED
            else "Not affected assessment has expired."
        )
        assessment_removed = remove_assessment(observation, comment)
        if not assessment_removed:
            observation.parser_status = Status.STATUS_OPEN
            observation.save()
            save_assessment(
                observation=observation,
                new_severity="",
                new_status=Status.STATUS_OPEN,
                new_priority=None,
                new_priority_changed=False,
                comment=comment,
                new_vex_justification="",
                new_vex_remediations=None,
                new_risk_acceptance_expiry_date=None,
            )

    return f"Expired assessments for {observations.count()} observations."
