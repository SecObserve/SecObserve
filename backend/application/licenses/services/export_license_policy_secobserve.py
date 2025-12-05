import json
from dataclasses import dataclass
from typing import Optional

import yaml

from application.commons.services.export import object_to_json
from application.commons.services.functions import get_comma_separated_as_list
from application.licenses.models import License_Policy
from application.licenses.services.license_policy import (
    LicensePolicyEvaluationResult,
    get_license_evaluation_results_for_license_policy,
)


@dataclass
class License_Policy_Export_Item:
    evaluation_result: str
    from_parent: bool
    spdx_license: Optional[str] = None
    license_expression: Optional[str] = None
    non_spdx_license: Optional[str] = None
    license_group: Optional[str] = None
    comment: Optional[str] = None


@dataclass
class License_Policy_Export:
    name: str
    description: str
    items: list[License_Policy_Export_Item]
    ignore_component_types: list[str]
    parent: Optional[str] = None


def export_license_policy_secobserve_yaml(license_policy: License_Policy) -> str:
    return yaml.dump(json.loads(export_license_policy_secobserve_json(license_policy)))


def export_license_policy_secobserve_json(license_policy: License_Policy) -> str:
    return object_to_json(_create_license_policy_export(license_policy))


def _create_license_policy_export(license_policy: License_Policy) -> License_Policy_Export:
    license_policy_export = License_Policy_Export(
        name=license_policy.name,
        description=license_policy.description,
        items=[],
        ignore_component_types=get_comma_separated_as_list(license_policy.ignore_component_types),
    )
    if license_policy.parent:
        license_policy_export.parent = license_policy.parent.name

    license_evaluation_results: dict[str, LicensePolicyEvaluationResult] = {}

    if license_policy.parent:
        get_license_evaluation_results_for_license_policy(license_policy.parent, True, license_evaluation_results)

    get_license_evaluation_results_for_license_policy(license_policy, False, license_evaluation_results)

    for license_string, evaluation_result in license_evaluation_results.items():
        license_policy_export_item = License_Policy_Export_Item(
            evaluation_result=evaluation_result.evaluation_result,
            from_parent=evaluation_result.from_parent,
            license_group=evaluation_result.license_group_name,
            comment=evaluation_result.comment,
        )
        if license_string.startswith("spdx_"):
            license_policy_export_item.spdx_license = license_string.replace("spdx_", "")
        elif license_string.startswith("expression_"):
            license_policy_export_item.license_expression = license_string.replace("expression_", "")
        elif license_string.startswith("non_spdx_"):
            license_policy_export_item.non_spdx_license = license_string.replace("non_spdx_", "")
        else:
            continue

        license_policy_export.items.append(license_policy_export_item)

    return license_policy_export
