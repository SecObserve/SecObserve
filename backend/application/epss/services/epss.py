import gzip
import re
from collections.abc import Iterator
from datetime import datetime
from typing import Optional

import requests

from application.core.models import Observation
from application.core.types import Status
from application.epss.models import EPSS_Score, EPSS_Status
from application.epss.queries.epss_score import get_epss_scores_by_cves

BATCH_SIZE = 1000


def batched_cve_observations(batch_size: int = BATCH_SIZE) -> Iterator[list[Observation]]:
    """Unresolved observations with a CVE, in batches.

    Keyset pagination instead of a paginator: with hundreds of thousands of observations, the
    growing OFFSET of a paginator makes the last pages far more expensive than the first ones.
    """
    observations = (
        Observation.objects.filter(vulnerability_id__startswith="CVE-")
        .exclude(current_status=Status.STATUS_RESOLVED)
        .order_by("id")
    )

    last_id = 0
    while True:
        batch = list(observations.filter(id__gt=last_id)[:batch_size])
        if not batch:
            return
        yield batch
        last_id = batch[-1].pk


def import_epss() -> str:
    response = requests.get(
        "https://epss.cyentia.com/epss_scores-current.csv.gz",
        timeout=60,
        stream=True,
    )
    response.raise_for_status()
    extracted_data = gzip.decompress(response.content)

    EPSS_Score.objects.all().delete()

    counter = 0
    scores = []
    num_epss_scores = 0
    for line in extracted_data.split(b"\n"):
        decoded_line = line.decode()

        if decoded_line.startswith("#"):
            epss_date = re.search(r"(\d{4}-\d{2}-\d{2})", decoded_line)
            if epss_date:
                epss_status = EPSS_Status.load()
                epss_status.score_date = datetime.strptime(epss_date.group(0), "%Y-%m-%d")
                epss_status.save()

        if decoded_line.startswith("CVE"):
            elements = decoded_line.split(",")
            if len(elements) == 3:
                scores.append(
                    EPSS_Score(
                        cve=elements[0],
                        epss_score=elements[1],
                        epss_percentile=elements[2],
                    )
                )
                num_epss_scores += 1
                counter += 1
            if counter == 1000:
                EPSS_Score.objects.bulk_create(scores)
                counter = 0
                scores = []
    if scores:
        EPSS_Score.objects.bulk_create(scores)

    return f"Imported {num_epss_scores} EPSS scores."


def epss_apply_observations() -> str:
    num_observations = 0

    for observations in batched_cve_observations():
        epss_scores = get_epss_scores_by_cves(observation.vulnerability_id for observation in observations)
        updates = [observation for observation in observations if apply_epss(observation, epss_scores)]

        Observation.objects.bulk_update(updates, ["epss_score", "epss_percentile"])
        num_observations += len(updates)

    return f"Applied EPSS scores to {num_observations} observations."


def apply_epss(observation: Observation, epss_scores: Optional[dict[str, EPSS_Score]] = None) -> bool:
    if observation.vulnerability_id.startswith("CVE-"):
        if epss_scores is None:
            try:
                epss_score: Optional[EPSS_Score] = EPSS_Score.objects.get(cve=observation.vulnerability_id)
            except EPSS_Score.DoesNotExist:
                return False
        else:
            epss_score = epss_scores.get(observation.vulnerability_id)
        if not epss_score:
            return False

        new_epss_score = round(epss_score.epss_score * 100, 3) if epss_score.epss_score else None
        new_epss_percentile = round(epss_score.epss_percentile * 100, 3) if epss_score.epss_percentile else None
        if observation.epss_score != new_epss_score or observation.epss_percentile != new_epss_percentile:
            observation.epss_score = new_epss_score
            observation.epss_percentile = new_epss_percentile
            return True

    return False
