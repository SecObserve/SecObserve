from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError

from application.core.models import Observation
from application.vex.models import VEX_Document, VEX_Statement
from application.vex.services.vex_engine import write_observation_log_no_vex_statement


@receiver(pre_delete, sender=VEX_Statement)
def vex_statement_pre_delete(  # pylint: disable=unused-argument
    sender: Any, instance: VEX_Statement, **kwargs: Any
) -> None:
    # sender is needed according to Django documentation
    observations = Observation.objects.filter(vex_statement=instance)
    for observation in observations:
        write_observation_log_no_vex_statement(observation, instance)


@receiver(pre_save, sender=VEX_Document)
@receiver(pre_save, sender=VEX_Statement)
def vex_pre_save(  # pylint: disable=unused-argument
    sender: Any, instance: VEX_Document | VEX_Statement, **kwargs: Any
) -> None:
    # sender is needed according to Django documentation
    # Documents and statements come from uploaded VEX files, which are validated here against the columns.
    # Uniqueness is left to the parsers, which replace an existing document before creating it.
    try:
        instance.full_clean(validate_unique=False)
    except DjangoValidationError as e:
        if isinstance(instance, VEX_Document):
            label = f"VEX document {instance.document_id}"
        else:
            label = f"VEX statement for {instance.vulnerability_id}"
        messages = [f"{field}: {' '.join(errors)}" for field, errors in e.message_dict.items()]
        raise ValidationError(f"{label}: {' / '.join(messages)}") from e
