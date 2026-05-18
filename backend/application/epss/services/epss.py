import gzip
import re
from datetime import datetime

import requests
from django.core.paginator import Paginator
from django.db import connection

from application.core.models import Observation
from application.core.types import Status
from application.epss.models import EPSS_Score, EPSS_Status


def import_epss() -> str:
    response = requests.get(
        "https://epss.cyentia.com/epss_scores-current.csv.gz",
        timeout=60,
        stream=True,
    )
    response.raise_for_status()
    extracted_data = gzip.decompress(response.content)

    scores_by_cve: dict[str, EPSS_Score] = {}
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
                scores_by_cve[elements[0]] = EPSS_Score(
                    cve=elements[0],
                    epss_score=elements[1],
                    epss_percentile=elements[2],
                )

    _upsert_epss_scores(list(scores_by_cve.values()))

    return f"Imported {len(scores_by_cve)} EPSS scores."


def _upsert_epss_scores(scores: list[EPSS_Score]) -> None:
    if not scores:
        return

    update_fields = ["epss_score", "epss_percentile"]
    if connection.features.supports_update_conflicts_with_target:
        EPSS_Score.objects.bulk_create(
            scores,
            batch_size=1000,
            update_conflicts=True,
            update_fields=update_fields,
            unique_fields=["cve"],
        )
        return

    if connection.features.supports_update_conflicts:
        EPSS_Score.objects.bulk_create(
            scores,
            batch_size=1000,
            update_conflicts=True,
            update_fields=update_fields,
        )
        return

    _bulk_update_or_create_epss_scores(scores, update_fields)


def _bulk_update_or_create_epss_scores(scores: list[EPSS_Score], update_fields: list[str]) -> None:
    for score_batch in _chunks(scores, 1000):
        cves = [score.cve for score in score_batch]
        existing_scores = {score.cve: score for score in EPSS_Score.objects.filter(cve__in=cves)}
        scores_to_update = []
        scores_to_create = []

        for score in score_batch:
            if existing_score := existing_scores.get(score.cve):
                existing_score.epss_score = score.epss_score
                existing_score.epss_percentile = score.epss_percentile
                scores_to_update.append(existing_score)
            else:
                scores_to_create.append(score)

        if scores_to_update:
            EPSS_Score.objects.bulk_update(scores_to_update, update_fields)
        if scores_to_create:
            EPSS_Score.objects.bulk_create(scores_to_create, ignore_conflicts=True)


def _chunks(scores: list[EPSS_Score], chunk_size: int) -> list[list[EPSS_Score]]:
    return [scores[index : index + chunk_size] for index in range(0, len(scores), chunk_size)]


def epss_apply_observations() -> str:
    num_observations = 0

    observations = (
        Observation.objects.filter(vulnerability_id__startswith="CVE-")
        .exclude(current_status=Status.STATUS_RESOLVED)
        .order_by("id")
    )

    paginator = Paginator(observations, 1000)

    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        updates = []

        for observation in page.object_list:
            if apply_epss(observation):
                updates.append(observation)
                num_observations += 1

        Observation.objects.bulk_update(updates, ["epss_score", "epss_percentile"])

    return f"Applied EPSS scores to {num_observations} observations."


def apply_epss(observation: Observation) -> bool:
    if observation.vulnerability_id.startswith("CVE-"):
        try:
            epss_score = EPSS_Score.objects.get(cve=observation.vulnerability_id)
        except EPSS_Score.DoesNotExist:
            return False

        new_epss_score = round(epss_score.epss_score * 100, 3) if epss_score.epss_score else None
        new_epss_percentile = round(epss_score.epss_percentile * 100, 3) if epss_score.epss_percentile else None
        if observation.epss_score != new_epss_score or observation.epss_percentile != new_epss_percentile:
            observation.epss_score = new_epss_score
            observation.epss_percentile = new_epss_percentile
            return True

    return False
