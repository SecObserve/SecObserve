from datetime import date
from typing import Optional

from django.db.models.query import QuerySet
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions
from application.core.models import (
    Observation,
    Observation_Log,
    Potential_Duplicate,
    Product,
)
from application.core.queries.observation import get_current_observation_log
from application.core.services.assessment import assessment_approval, save_assessment
from application.core.services.potential_duplicates import (
    set_potential_duplicate,
    set_potential_duplicate_both_ways,
)
from application.core.services.security_gate import check_security_gate
from application.core.types import Assessment_Status, Status


def observations_bulk_assessment(
    *,
    product: Optional[Product],
    new_severity: str,
    new_status: str,
    comment: str,
    observation_ids: list[int],
    new_vex_justification: str,
    new_risk_acceptance_expiry_date: Optional[date],
) -> None:
    observations = _check_observations(product, observation_ids)
    for observation in observations:
        save_assessment(
            observation=observation,
            new_severity=new_severity,
            new_status=new_status,
            comment=comment,
            new_vex_justification=new_vex_justification,
            new_risk_acceptance_expiry_date=new_risk_acceptance_expiry_date,
        )


def observations_bulk_delete(product: Product, observation_ids: list[int]) -> None:
    observations = _check_observations(product, observation_ids)
    issue_ids: list[str] = []
    for observation in observations:
        issue_ids.append(observation.issue_tracker_issue_id)

    observations.delete()

    check_security_gate(product)
    product.last_observation_change = timezone.now()
    product.save()


def observations_bulk_mark_duplicates(
    product: Product,
    observation_id: int,
    potential_duplicate_ids: list[int],
) -> None:
    try:
        observation = Observation.objects.get(pk=observation_id)
        if observation.product != product:
            raise ValidationError(f"Observation {observation.pk} does not belong to product {product.pk}")
    except Observation.DoesNotExist:
        raise ValidationError("Observation does not exist")  # pylint: disable=raise-missing-from
        # The DoesNotExist exception itself is not relevant and must not be re-raised

    observation_ids = []
    for potential_duplicate_id in potential_duplicate_ids:
        potential_duplicate = Potential_Duplicate.objects.get(id=potential_duplicate_id)
        observation_ids.append(potential_duplicate.potential_duplicate_observation.id)
    duplicates = _check_observations(product, observation_ids)

    if potential_duplicate.type == Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT:
        comment = f"Duplicate of {observation.origin_component_name_version}"
    elif potential_duplicate.type == Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE:
        comment = f"Duplicate of {observation.title} from scanner {observation.scanner}"
    else:
        raise ValidationError("Invalid potential duplicate type")

    for duplicate in duplicates:
        duplicate.has_potential_duplicates = False
        save_assessment(
            observation=duplicate,
            new_severity=None,
            new_status=Status.STATUS_DUPLICATE,
            comment=comment,
            new_vex_justification="",
            new_risk_acceptance_expiry_date=None,
        )

    set_potential_duplicate(observation)


def _check_observations(product: Optional[Product], observation_ids: list[int]) -> QuerySet[Observation]:
    observations = Observation.objects.filter(id__in=observation_ids)
    if len(observations) != len(observation_ids):
        raise ValidationError("Some observations do not exist")

    for observation in observations:
        if product:
            if observation.product != product:
                raise ValidationError(f"Observation {observation.pk} does not belong to product {product.pk}")
        else:
            if not user_has_permission(observation, Permissions.Observation_Assessment):
                raise ValidationError(f"First observation without assessment permission: {observation}")

        current_observation_log = get_current_observation_log(observation)
        if (
            current_observation_log
            and current_observation_log.assessment_status == Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL
        ):
            raise ValidationError("Cannot create new assessment while last assessment still needs approval")

    return observations


def observation_logs_bulk_approval(
    assessment_status: str,
    approval_remark: str,
    observation_log_ids: list[int],
) -> None:
    observation_logs = _check_observation_logs(None, observation_log_ids)
    for observation_log in observation_logs:
        assessment_approval(observation_log, assessment_status, approval_remark)
        set_potential_duplicate_both_ways(observation_log.observation)


def _check_observation_logs(product: Optional[Product], observation_log_ids: list[int]) -> QuerySet[Observation_Log]:
    observation_logs = Observation_Log.objects.filter(id__in=observation_log_ids)
    if len(observation_logs) != len(observation_log_ids):
        raise ValidationError("Some observation logs do not exist")

    for observation_log in observation_logs:
        if product:
            if observation_log.observation.product != product:
                raise ValidationError(f"Observation log {observation_log.pk} does not belong to product {product.pk}")
        else:
            if not user_has_permission(observation_log, Permissions.Observation_Log_Approval):
                raise ValidationError(f"First observation log without approval permission: {observation_log.pk}")
            if observation_log.assessment_status != Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL:
                raise ValidationError(f"First observation log that does not need approval: {observation_log.pk}")
            if get_current_user() == observation_log.user:
                raise ValidationError(
                    f"First observation log where user cannot approve their own assessment: {observation_log.pk}"
                )

    return observation_logs
