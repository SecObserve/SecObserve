from typing import Optional

from django.db.models.query import QuerySet
from huey.contrib.djhuey import db_task

from application.core.models import Branch, Observation, Potential_Duplicate, Product
from application.core.types import Status
from application.notifications.services.tasks import handle_task_exception


@db_task()
def find_potential_duplicates(product: Product, branch: Optional[Branch], service: Optional[str]) -> None:
    try:
        if not service:
            service = ""

        observations = Observation.objects.filter(
            product=product,
            branch=branch,
            origin_service_name=service,
        )

        for observation in observations:
            _handle_observation(observation, observations)
    except Exception as e:
        handle_task_exception(e)


def _handle_observation(observation: Observation, observations: QuerySet[Observation]) -> None:
    Potential_Duplicate.objects.filter(observation=observation).delete()
    initial_has_potential_duplicates = observation.has_potential_duplicates
    observation.has_potential_duplicates = False
    if observation.current_status in Status.STATUS_ACTIVE:
        for potential_duplicate_observation in observations:
            if (
                observation != potential_duplicate_observation
                and potential_duplicate_observation.current_status in Status.STATUS_ACTIVE
            ):
                potential_duplicate_type = None
                if (
                    observation.origin_component_name
                    and potential_duplicate_observation.origin_component_name
                    and observation.title == potential_duplicate_observation.title
                ):
                    potential_duplicate_type = Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT
                if (
                    observation.origin_source_file
                    and observation.origin_source_line_start
                    and observation.origin_source_file == potential_duplicate_observation.origin_source_file
                    and observation.origin_source_line_start == potential_duplicate_observation.origin_source_line_start
                    and observation.scanner != potential_duplicate_observation.scanner
                ):
                    potential_duplicate_type = Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE
                if potential_duplicate_type:
                    Potential_Duplicate.objects.update_or_create(
                        observation=observation,
                        potential_duplicate_observation=potential_duplicate_observation,
                        defaults={"type": potential_duplicate_type},
                    )
                    observation.has_potential_duplicates = True
    if observation.has_potential_duplicates != initial_has_potential_duplicates:
        observation.save()


def set_potential_duplicate_both_ways(observation: Observation) -> None:
    set_potential_duplicate(observation)

    potential_duplicate_observations = Potential_Duplicate.objects.filter(potential_duplicate_observation=observation)
    for potential_duplicate_observation in potential_duplicate_observations:
        set_potential_duplicate(potential_duplicate_observation.observation)


def set_potential_duplicate(observation: Observation) -> None:
    initial_has_potential_duplicates = observation.has_potential_duplicates

    if observation.current_status in Status.STATUS_ACTIVE:
        open_potential_duplicates = Potential_Duplicate.objects.filter(
            observation=observation,
            potential_duplicate_observation__current_status__in=Status.STATUS_ACTIVE,
        ).count()
        if open_potential_duplicates == 0:
            observation.has_potential_duplicates = False
        else:
            observation.has_potential_duplicates = True
    else:
        observation.has_potential_duplicates = False

    if initial_has_potential_duplicates != observation.has_potential_duplicates:
        observation.save()
