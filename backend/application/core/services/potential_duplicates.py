import logging
from collections import defaultdict
from collections.abc import Iterable, Iterator
from itertools import combinations
from typing import NamedTuple, Optional

from huey.contrib.djhuey import lock_task, on_commit_task

from application.core.models import (
    Branch,
    Observation,
    Potential_Duplicate,
    Product,
    Service,
)
from application.core.types import Status
from application.notifications.services.tasks import handle_task_exception

logger = logging.getLogger("secobserve.core")

BULK_BATCH_SIZE = 1000


class Observation_Data(NamedTuple):
    pk: int
    title: str
    origin_component_name: str
    origin_source_file: str
    origin_source_line_start: Optional[int]
    scanner: str


# The lock serializes all recalculations, so that concurrent imports cannot write
# potential duplicates for the same observations at the same time. If the lock cannot be
# acquired, Huey retries the task later. The retries have to be high enough to bridge
# the recalculations of the other tasks waiting for the lock.
@on_commit_task(retries=5, retry_delay=60)
@lock_task("find_potential_duplicates_lock")
def find_potential_duplicates(product: Product, branch: Optional[Branch], service: Optional[Service]) -> None:
    try:
        _find_potential_duplicates(product, branch, service)
    except Exception as e:
        handle_task_exception(e)


def _find_potential_duplicates(product: Product, branch: Optional[Branch], service: Optional[Service]) -> None:
    observations = _get_active_observations(product, branch, service)
    potential_duplicates = _get_potential_duplicates(observations)

    _write_potential_duplicates(product, branch, service, potential_duplicates)
    _set_has_potential_duplicates(
        product, branch, service, {observation_id for observation_id, _ in potential_duplicates}
    )

    logger.info(
        "Potential duplicates for product %s / branch %s / service %s: "
        "%s active observations, %s potential duplicates",
        product.pk,
        branch.pk if branch else None,
        service.pk if service else None,
        len(observations),
        len(potential_duplicates),
    )


def _get_active_observations(
    product: Product, branch: Optional[Branch], service: Optional[Service]
) -> list[Observation_Data]:
    # Only active observations can be potential duplicates of each other, so the
    # database can filter out everything else. Only the fields needed for matching
    # are read to avoid instantiating the full observations.
    return [
        Observation_Data(*row)
        for row in Observation.objects.filter(
            product=product,
            branch=branch,
            origin_service=service,
            current_status__in=Status.STATUS_ACTIVE,
        )
        .values_list(
            "pk",
            "title",
            "origin_component_name",
            "origin_source_file",
            "origin_source_line_start",
            "scanner",
        )
        .iterator(chunk_size=BULK_BATCH_SIZE)
    ]


def _get_potential_duplicates(observations: list[Observation_Data]) -> dict[tuple[int, int], str]:
    """Return the type of the potential duplicate per pair of observation ids, both ways.

    Observations are grouped by the attributes they need to have in common, so that only
    the observations within a group have to be compared with each other.
    """
    observations_by_title: dict[str, list[int]] = defaultdict(list)
    observations_by_source: dict[tuple[str, int], list[tuple[int, str]]] = defaultdict(list)

    for observation in observations:
        if observation.origin_component_name:
            observations_by_title[observation.title].append(observation.pk)
        if observation.origin_source_file and observation.origin_source_line_start is not None:
            observations_by_source[(observation.origin_source_file, observation.origin_source_line_start)].append(
                (observation.pk, observation.scanner)
            )

    potential_duplicates: dict[tuple[int, int], str] = {}

    for observation_ids in observations_by_title.values():
        for observation_id_1, observation_id_2 in combinations(observation_ids, 2):
            potential_duplicates[(observation_id_1, observation_id_2)] = (
                Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT
            )
            potential_duplicates[(observation_id_2, observation_id_1)] = (
                Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT
            )

    # Source is checked after component, because it takes precedence
    for observations_with_scanner in observations_by_source.values():
        for (observation_id_1, scanner_1), (observation_id_2, scanner_2) in combinations(observations_with_scanner, 2):
            if scanner_1 != scanner_2:
                potential_duplicates[(observation_id_1, observation_id_2)] = (
                    Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE
                )
                potential_duplicates[(observation_id_2, observation_id_1)] = (
                    Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE
                )

    return potential_duplicates


def _write_potential_duplicates(
    product: Product,
    branch: Optional[Branch],
    service: Optional[Service],
    potential_duplicates: dict[tuple[int, int], str],
) -> None:
    Potential_Duplicate.objects.filter(
        observation__product=product,
        observation__branch=branch,
        observation__origin_service=service,
    ).delete()

    Potential_Duplicate.objects.bulk_create(
        [
            Potential_Duplicate(
                observation_id=observation_id,
                potential_duplicate_observation_id=potential_duplicate_observation_id,
                type=potential_duplicate_type,
            )
            for (
                observation_id,
                potential_duplicate_observation_id,
            ), potential_duplicate_type in potential_duplicates.items()
        ],
        batch_size=BULK_BATCH_SIZE,
    )


def _set_has_potential_duplicates(
    product: Product,
    branch: Optional[Branch],
    service: Optional[Service],
    observation_ids_with_duplicates: set[int],
) -> None:
    # Observations that are not active are not in observation_ids_with_duplicates,
    # but their flag has to be reset as well.
    observation_ids_with_flag = set(
        Observation.objects.filter(
            product=product,
            branch=branch,
            origin_service=service,
            has_potential_duplicates=True,
        ).values_list("pk", flat=True)
    )

    for observation_ids in _batches(observation_ids_with_duplicates - observation_ids_with_flag):
        Observation.objects.filter(pk__in=observation_ids).update(has_potential_duplicates=True)

    for observation_ids in _batches(observation_ids_with_flag - observation_ids_with_duplicates):
        Observation.objects.filter(pk__in=observation_ids).update(has_potential_duplicates=False)

    # The observations are updated without save(), so the product flag that is
    # normally set in set_product_flags() has to be set here. Like there, it is only
    # ever set to True, housekeeping resets it.
    if observation_ids_with_duplicates:
        Product.objects.filter(pk=product.pk, has_potential_duplicates=False).update(has_potential_duplicates=True)


def _batches(observation_ids: Iterable[int]) -> Iterator[list[int]]:
    batch: list[int] = []
    for observation_id in observation_ids:
        batch.append(observation_id)
        if len(batch) == BULK_BATCH_SIZE:
            yield batch
            batch = []
    if batch:
        yield batch


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
