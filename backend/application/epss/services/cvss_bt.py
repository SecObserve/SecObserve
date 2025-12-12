import csv
import logging
from typing import Optional

import requests
from cvss import CVSS3, CVSS4
from cvss.exceptions import CVSSError
from django.core.paginator import Paginator
from django.utils import timezone

from application.commons.models import Settings
from application.core.models import Observation
from application.core.services.observation import get_current_severity
from application.core.types import Severity, Status
from application.epss.models import Exploit_Information
from application.epss.queries.exploit_information import get_exploit_information_by_cve

logger = logging.getLogger("secobserve.epss")


def import_cvss_bt() -> str:
    response = requests.get(  # nosec B113
        # This is a false positive, there is a timeout of 5 minutes
        "https://raw.githubusercontent.com/t0sche/cvss-bt/refs/heads/main/cvss-bt.csv",
        timeout=5 * 60,
        stream=True,
    )
    response.raise_for_status()

    line = (line.decode("utf-8") for line in response.iter_lines())
    reader = csv.reader(line, delimiter=",", quotechar='"')

    first_row = True
    counter = 0
    exploit_information_list = []
    num_exploit_informations = 0

    settings = Settings.load()

    for row in reader:
        if first_row:
            if not _check_first_row(row):
                return "Error: First row of cvss-bt CSV is not valid."

            Exploit_Information.objects.all().delete()

            first_row = False
            continue

        if len(row) != 17:
            logger.warning("Row doesn't have 17 elements: %s", row)
            continue

        cve = row[0]
        cve_year = _get_year_from_cve(cve)
        if cve_year is None:
            continue
        current_year = timezone.now().year
        if cve_year <= current_year - settings.exploit_information_max_age_years:
            continue

        exploit_information = Exploit_Information(
            cve=cve,
            base_cvss_vector=row[7],
            cisa_kev=row[11].lower() == "true",
            vulncheck_kev=row[12].lower() == "true",
            exploitdb=row[13].lower() == "true",
            metasploit=row[14].lower() == "true",
            nuclei=row[15].lower() == "true",
            poc_github=row[16].lower() == "true",
        )
        num_exploit_informations += 1
        exploit_information_list.append(exploit_information)
        counter += 1
        if counter == 1000:
            Exploit_Information.objects.bulk_create(exploit_information_list)
            counter = 0
            exploit_information_list = []

    if exploit_information_list:
        Exploit_Information.objects.bulk_create(exploit_information_list)

    num_observations = apply_exploit_information_observations(settings)

    return (
        f"Imported {num_exploit_informations} exploit information entries.\n"
        + f"Applied exploit information to {num_observations} observations."
    )


def _check_first_row(row: list[str]) -> bool:
    if len(row) != 17:
        logger.error("First row doesn't have 17 elements: %s", row)
        return False

    errors = []
    if row[0] != "cve":
        errors.append("First element of first row is not 'cve'")
    if row[7] != "base_vector":
        errors.append("Eigth element of first row is not 'base_vector'")
    if row[11] != "cisa_kev":
        errors.append("Twelfth element of first row is not 'cisa_kev'")
    if row[12] != "vulncheck_kev":
        errors.append("Thirteenth element of first row is not 'vulncheck_kev'")
    if row[13] != "exploitdb":
        errors.append("Fourteenth element of first row is not 'exploitdb'")
    if row[14] != "metasploit":
        errors.append("Fifteenth element of first row is not 'metasploit'")
    if row[15] != "nuclei":
        errors.append("Sixteenth element of first row is not 'nuclei'")
    if row[16] != "poc_github":
        errors.append("Seventeenth element of first row is not 'poc_github'")

    if errors:
        logger.error("%s: %s", ", ".join(errors), row)
        return False

    return True


def _get_year_from_cve(cve: str) -> Optional[int]:
    if not cve.startswith("CVE-"):
        return None
    cve_parts = cve.split("-")
    if len(cve_parts) != 3:
        return None
    cve_year = cve.split("-")[1]
    if not cve_year.isdigit():
        return None
    return int(cve_year)


def apply_exploit_information_observations(settings: Settings) -> int:
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
            if apply_exploit_information(observation, settings):
                updates.append(observation)
                num_observations += 1

        Observation.objects.bulk_update(
            updates,
            [
                "cvss3_score",
                "cvss3_vector",
                "cvss4_score",
                "cvss4_vector",
                "cve_found_in",
                "current_severity",
            ],
        )

    return num_observations


def apply_exploit_information(observation: Observation, settings: Settings) -> bool:
    if not observation.vulnerability_id.startswith("CVE-"):
        return False

    if settings.feature_exploit_information:  # pylint: disable=no-else-return
        # else shall stay for clarity and just in case a return would be forgotten
        exploit_information = get_exploit_information_by_cve(observation.vulnerability_id)
        if not exploit_information:
            return False

        cvss3_vector_before = observation.cvss3_vector
        cvss4_vector_before = observation.cvss4_vector
        cve_found_in_before = observation.cve_found_in

        if not observation.cvss3_vector and exploit_information.base_cvss_vector.startswith("CVSS:3"):
            try:
                cvss = CVSS3(exploit_information.base_cvss_vector)
                observation.cvss3_vector = exploit_information.base_cvss_vector
                observation.cvss3_score = cvss.base_score
            except CVSSError:
                pass

        if not observation.cvss4_vector and exploit_information.base_cvss_vector.startswith("CVSS:4"):
            try:
                cvss = CVSS4(exploit_information.base_cvss_vector)
                observation.cvss4_vector = exploit_information.base_cvss_vector
                observation.cvss4_score = cvss.base_score
            except CVSSError:
                pass

        _add_cve_found_in(observation, exploit_information)

        if (
            observation.cvss3_vector != cvss3_vector_before  # pylint: disable=too-many-boolean-expressions
            or observation.cvss4_vector != cvss4_vector_before
            or observation.cve_found_in != cve_found_in_before
            or (
                (observation.cvss3_vector or observation.cvss4_vector)
                and observation.current_severity == Severity.SEVERITY_UNKNOWN
            )
        ):
            observation.current_severity = get_current_severity(observation)
            return True

        return False
    else:
        if observation.cve_found_in:
            observation.cve_found_in = ""
            return True

        return False


def _add_cve_found_in(observation: Observation, exploit_information: Exploit_Information) -> None:
    cve_found_in = []
    if exploit_information.cisa_kev:
        cve_found_in.append("CISA KEV")
    if exploit_information.exploitdb:
        cve_found_in.append("Exploit-DB")
    if exploit_information.metasploit:
        cve_found_in.append("Metasploit")
    if exploit_information.nuclei:
        cve_found_in.append("Nuclei")
    if exploit_information.poc_github:
        cve_found_in.append("PoC GitHub")
    if exploit_information.vulncheck_kev:
        cve_found_in.append("VulnCheck KEV")
    observation.cve_found_in = ", ".join(cve_found_in)
