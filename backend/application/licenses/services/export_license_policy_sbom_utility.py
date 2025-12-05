import logging
from dataclasses import dataclass
from typing import Optional

from application.commons.services.export import object_to_json
from application.licenses.models import License, License_Policy
from application.licenses.services.license_policy import (
    LicensePolicyEvaluationResult,
    get_license_evaluation_results_for_license_policy,
)
from application.licenses.types import License_Policy_Evaluation_Result

logger = logging.getLogger("secobserve.licenses")


class USAGE_POLICY:
    POLICY_ALLOW = "allow"
    POLICY_DENY = "deny"
    POLICY_NEEDS_REVIEW = "needs-review"


@dataclass
class License_Policy_Export_Item:
    id: str
    name: str
    family: str
    reference: str
    osi: bool
    deprecated: bool
    usagePolicy: str
    annotationRefs: list[str]
    notes: Optional[list[str]]


@dataclass
class License_Policy_Export:
    policies: list[License_Policy_Export_Item]


def export_license_policy_sbom_utility(license_policy: License_Policy) -> str:
    return object_to_json(_create_license_policy_export(license_policy))


def _create_license_policy_export(license_policy: License_Policy) -> License_Policy_Export:
    license_policy_export = License_Policy_Export(policies=[])

    license_evaluation_results: dict[str, LicensePolicyEvaluationResult] = {}

    if license_policy.parent:
        get_license_evaluation_results_for_license_policy(license_policy.parent, True, license_evaluation_results)

    get_license_evaluation_results_for_license_policy(license_policy, False, license_evaluation_results)

    license_ids = set()
    for license_string in license_evaluation_results:
        if license_string.startswith("spdx_"):
            license_ids.add(license_string.replace("spdx_", ""))

    spdx_licenses = License.objects.filter(spdx_id__in=license_ids)
    spdx_license_dict = {license.spdx_id: license for license in spdx_licenses}

    for license_string, evaluation_result in license_evaluation_results.items():
        license_id = license_string.replace("spdx_", "") if license_string.startswith("spdx_") else ""
        if license_id:
            spdx_license = spdx_license_dict.get(license_id)
            if spdx_license:
                license_name = spdx_license.name
                reference = spdx_license.reference
                osi = spdx_license.is_osi_approved if spdx_license.is_osi_approved is not None else False
                deprecated = spdx_license.is_deprecated if spdx_license.is_deprecated is not None else False
            else:
                logger.warning("SPDX license %s not found in database.", license_id)
                continue
        else:
            license_name = license_string.replace("expression_", "") if license_string.startswith("expression_") else ""
            if not license_name:
                license_name = license_string.replace("non_spdx_", "") if license_string.startswith("non_spdx_") else ""
            reference = ""
            osi = False
            deprecated = False

        family = license_id if license_id else license_name
        # replace everything that is not a letter, number or dash with a dash
        family = "".join(char if char.isalnum() or char == "-" else "-" for char in family)
        notes = [evaluation_result.comment] if evaluation_result.comment else None
        usagePolicy = _get_usage_policy(evaluation_result)
        annotationRefs = [evaluation_result.evaluation_result.upper()]

        license_policy_export_item = License_Policy_Export_Item(
            id=license_id,
            name=license_name,
            family=family,
            reference=reference,
            osi=osi,
            deprecated=deprecated,
            usagePolicy=usagePolicy,
            annotationRefs=annotationRefs,
            notes=notes,
        )
        license_policy_export.policies.append(license_policy_export_item)

    return license_policy_export


def _get_usage_policy(evaluation_result: LicensePolicyEvaluationResult) -> str:
    if evaluation_result.evaluation_result == License_Policy_Evaluation_Result.RESULT_ALLOWED:
        usagePolicy = USAGE_POLICY.POLICY_ALLOW
    elif evaluation_result.evaluation_result == License_Policy_Evaluation_Result.RESULT_FORBIDDEN:
        usagePolicy = USAGE_POLICY.POLICY_DENY
    elif evaluation_result.evaluation_result == License_Policy_Evaluation_Result.RESULT_REVIEW_REQUIRED:
        usagePolicy = USAGE_POLICY.POLICY_NEEDS_REVIEW
    elif evaluation_result.evaluation_result == License_Policy_Evaluation_Result.RESULT_UNKNOWN:
        usagePolicy = USAGE_POLICY.POLICY_NEEDS_REVIEW
    elif evaluation_result.evaluation_result == License_Policy_Evaluation_Result.RESULT_IGNORED:
        usagePolicy = USAGE_POLICY.POLICY_ALLOW
    else:
        usagePolicy = USAGE_POLICY.POLICY_NEEDS_REVIEW
    return usagePolicy
