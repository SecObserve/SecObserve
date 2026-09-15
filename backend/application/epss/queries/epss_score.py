from collections.abc import Iterable
from itertools import batched

from application.epss.models import EPSS_Score

BATCH_SIZE = 1000


def get_epss_scores_by_cves(cves: Iterable[str]) -> dict[str, EPSS_Score]:
    """The EPSS scores of many CVEs in one query per batch, instead of one query per CVE."""
    epss_scores: dict[str, EPSS_Score] = {}
    # Batched to stay below the parameter limits of the databases
    for cves_batch in batched(set(cves), BATCH_SIZE):
        epss_scores.update(EPSS_Score.objects.in_bulk(cves_batch, field_name="cve"))
    return epss_scores
