from application.core.models import Observation
from application.core.queries.observation import get_current_modifying_observation_log
from application.vex.services.csaf_generator_helpers import (
    get_product_or_relationship_id,
    map_status,
)
from application.vex.types import CSAF_Status, CSAFRemediation, CSAFVulnerability


def set_remediation(vulnerability: CSAFVulnerability, observation: Observation) -> None:
    vex_status = map_status(observation.current_status)
    if vex_status == CSAF_Status.CSAF_STATUS_AFFECTED:
        product_or_relationship_id = get_product_or_relationship_id(observation)

        observation_log = get_current_modifying_observation_log(observation)
        if observation_log and observation_log.vex_remediations:
            for remediation in observation_log.vex_remediations:
                category = remediation["category"]
                details = remediation["text"]

                found = _check_and_append_remediation(vulnerability, product_or_relationship_id, category, details)

                if not found:
                    remediation = CSAFRemediation(
                        category=category,
                        details=details,
                        product_ids=[product_or_relationship_id],
                    )
                    vulnerability.remediations.append(remediation)
        else:
            category = "mitigation" if observation.recommendation else "none_available"
            details = observation.recommendation if observation.recommendation else "No remediation available"

            found = _check_and_append_none_available(vulnerability, product_or_relationship_id, category)

            found = _check_and_append_mitigation(found, vulnerability, product_or_relationship_id, category, details)

            if not found:
                remediation = CSAFRemediation(
                    category=category,
                    details=details,
                    product_ids=[product_or_relationship_id],
                )
                vulnerability.remediations.append(remediation)

            # remove "none_available" remediation if mitigation is available
            if category == "mitigation":
                for remediation in vulnerability.remediations:
                    if (
                        remediation.category == "none_available"
                        and product_or_relationship_id in remediation.product_ids
                    ):
                        remediation.product_ids.remove(product_or_relationship_id)

            # remove remediations without product_ids
            remediations = []
            for remediation in vulnerability.remediations:
                if remediation.product_ids:
                    remediations.append(remediation)
            vulnerability.remediations = remediations


def _check_and_append_remediation(
    vulnerability: CSAFVulnerability,
    product_or_relationship_id: str,
    category: str,
    details: str,
) -> bool:
    for remediation in vulnerability.remediations:
        if remediation.category == category and remediation.details == details:
            if product_or_relationship_id not in remediation.product_ids:
                remediation.product_ids.append(product_or_relationship_id)
            return True

    return False


def _check_and_append_none_available(
    vulnerability: CSAFVulnerability, product_or_relationship_id: str, category: str
) -> bool:
    found = False

    if category == "none_available":
        for remediation in vulnerability.remediations:
            if product_or_relationship_id in remediation.product_ids:
                found = True
                break

        if not found:
            for remediation in vulnerability.remediations:
                if (
                    remediation.category == "none_available"
                    and product_or_relationship_id not in remediation.product_ids
                ):
                    remediation.product_ids.append(product_or_relationship_id)
                    found = True
                    break

    return found


def _check_and_append_mitigation(
    found: bool,
    vulnerability: CSAFVulnerability,
    product_or_relationship_id: str,
    category: str,
    details: str,
) -> bool:
    if category == "mitigation":
        for remediation in vulnerability.remediations:
            if remediation.category == category and remediation.details == details:
                if product_or_relationship_id not in remediation.product_ids:
                    remediation.product_ids.append(product_or_relationship_id)
                found = True
                break

    return found
