import logging
from collections import defaultdict
from collections.abc import Iterator
from itertools import batched, combinations
from typing import NamedTuple, Optional

from django.db import transaction
from django.db.models.query import QuerySet
from huey.contrib.djhuey import on_commit_task

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


class DuplicateCandidate(NamedTuple):
    """An active observation, reduced to the fields that are needed to match duplicates."""

    id: int
    title: str
    origin_component_name: str
    origin_source_file: str
    origin_source_line_start: Optional[int]
    scanner: str


# Type of the potential duplicate per pair of observation ids, lower id first
DuplicateTypes = dict[tuple[int, int], str]


# The lock serializes all recalculations, so that concurrent imports cannot write
# potential duplicates for the same observations at the same time. If the lock cannot be
# acquired, Huey retries the task later. The retries have to be high enough to bridge
# the recalculations of the other tasks waiting for the lock.
@on_commit_task()
def find_potential_duplicates(product: Product, branch: Optional[Branch], service: Optional[Service]) -> None:
    try:
        observations = Observation.objects.filter(product=product, branch=branch, origin_service=service)

        candidates = _get_duplicate_candidates(observations)
        duplicate_types = _match_duplicate_candidates(candidates)

        # Deleted rows, new rows and the flags of a recalculation have to be consistent,
        # and a failed recalculation must not leave the potential duplicates of the
        # product / branch / service deleted.
        with transaction.atomic():
            _write_potential_duplicates(observations, duplicate_types)
            _set_has_potential_duplicates(observations, product, duplicate_types)

        logger.debug(
            "Potential duplicates for product %s / branch %s / service %s: %s candidates, %s pairs",
            product.pk,
            branch.pk if branch else None,
            service.pk if service else None,
            len(candidates),
            len(duplicate_types),
        )
    except Exception as e:
        handle_task_exception(e)


def _get_duplicate_candidates(observations: QuerySet[Observation]) -> list[DuplicateCandidate]:
    # Only active observations can be duplicates of each other, and only the fields that
    # are needed for matching are read, to keep this cheap for products with many
    # observations.
    rows = observations.filter(current_status__in=Status.STATUS_ACTIVE).values(
        "id",
        "title",
        "origin_component_name",
        "origin_source_file",
        "origin_source_line_start",
        "scanner",
    )
    return [DuplicateCandidate(**row) for row in rows.iterator(chunk_size=BULK_BATCH_SIZE)]


def _match_duplicate_candidates(candidates: list[DuplicateCandidate]) -> DuplicateTypes:
    duplicate_types: DuplicateTypes = {}

    for id_pair in _match_by_component(candidates):
        duplicate_types[id_pair] = Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT

    # Source is matched last, because its type takes precedence over Component
    for id_pair in _match_by_source(candidates):
        duplicate_types[id_pair] = Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE

    return duplicate_types


def _match_by_component(candidates: list[DuplicateCandidate]) -> Iterator[tuple[int, int]]:
    """Observations with the same title, if both of them have a component."""
    candidates_by_title: dict[str, list[DuplicateCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.origin_component_name:
            candidates_by_title[candidate.title].append(candidate)

    for candidates_with_same_title in candidates_by_title.values():
        for candidate_1, candidate_2 in combinations(candidates_with_same_title, 2):
            yield _get_id_pair(candidate_1, candidate_2)


def _match_by_source(candidates: list[DuplicateCandidate]) -> Iterator[tuple[int, int]]:
    """Observations from different scanners for the same line in the same source file."""
    candidates_by_source: dict[tuple[str, int], list[DuplicateCandidate]] = defaultdict(list)
    for candidate in candidates:
        if candidate.origin_source_file and candidate.origin_source_line_start is not None:
            source = (candidate.origin_source_file, candidate.origin_source_line_start)
            candidates_by_source[source].append(candidate)

    for candidates_with_same_source in candidates_by_source.values():
        for candidate_1, candidate_2 in combinations(candidates_with_same_source, 2):
            if candidate_1.scanner != candidate_2.scanner:
                yield _get_id_pair(candidate_1, candidate_2)


def _get_id_pair(candidate_1: DuplicateCandidate, candidate_2: DuplicateCandidate) -> tuple[int, int]:
    # The lower id always comes first, so that both matching rules describe the same pair
    # of observations with the same key
    return (min(candidate_1.id, candidate_2.id), max(candidate_1.id, candidate_2.id))


def _write_potential_duplicates(observations: QuerySet[Observation], duplicate_types: DuplicateTypes) -> None:
    Potential_Duplicate.objects.filter(observation__in=observations).delete()

    potential_duplicates = []
    for (observation_id_1, observation_id_2), duplicate_type in duplicate_types.items():
        # Every pair is stored in both directions
        potential_duplicates.append(
            Potential_Duplicate(
                observation_id=observation_id_1,
                potential_duplicate_observation_id=observation_id_2,
                type=duplicate_type,
            )
        )
        potential_duplicates.append(
            Potential_Duplicate(
                observation_id=observation_id_2,
                potential_duplicate_observation_id=observation_id_1,
                type=duplicate_type,
            )
        )

    Potential_Duplicate.objects.bulk_create(potential_duplicates, batch_size=BULK_BATCH_SIZE)


def _set_has_potential_duplicates(
    observations: QuerySet[Observation], product: Product, duplicate_types: DuplicateTypes
) -> None:
    observation_ids_with_duplicates: set[int] = set()
    for observation_id_1, observation_id_2 in duplicate_types:
        observation_ids_with_duplicates.add(observation_id_1)
        observation_ids_with_duplicates.add(observation_id_2)

    # This also contains observations that are not active anymore, their flag has to be
    # reset as well.
    flagged_observation_ids = set(observations.filter(has_potential_duplicates=True).values_list("id", flat=True))

    _update_has_potential_duplicates(observation_ids_with_duplicates - flagged_observation_ids, True)
    _update_has_potential_duplicates(flagged_observation_ids - observation_ids_with_duplicates, False)

    # The observations are updated without save(), so the product flag that would be set
    # in set_product_flags() has to be set here. As there, it is only ever set to True,
    # housekeeping resets it.
    if observation_ids_with_duplicates:
        Product.objects.filter(pk=product.pk, has_potential_duplicates=False).update(has_potential_duplicates=True)


def _update_has_potential_duplicates(observation_ids: set[int], has_potential_duplicates: bool) -> None:
    # Batched to stay below the parameter limits of the databases
    for observation_ids_batch in batched(observation_ids, BULK_BATCH_SIZE):
        Observation.objects.filter(id__in=observation_ids_batch).update(
            has_potential_duplicates=has_potential_duplicates
        )


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
