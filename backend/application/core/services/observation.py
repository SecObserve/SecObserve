import hashlib
import re
from decimal import Decimal
from urllib.parse import urlparse

from cvss import CVSS3, CVSS4
from packageurl import PackageURL

from application.core.models import Observation
from application.core.types import Severity, Status

VERSION_REGEX = r"(?:\s|^)+(?:\d+:)?v?(\d+[\.\d]*)"  # NOSONAR
VERSION_REGEX_COMPILED = re.compile(VERSION_REGEX)
# The regex will never be used on an empty string


def get_identity_hash(observation: Observation) -> str:
    hash_string = _get_string_to_hash(observation)
    return hashlib.sha256(hash_string.casefold().encode("utf-8").strip()).hexdigest()


def _get_string_to_hash(observation: Observation) -> str:  # pylint: disable=too-many-branches
    hash_string = observation.title

    if observation.origin_component_name_version:
        hash_string += observation.origin_component_name_version
    else:
        if observation.origin_component_name:
            hash_string += observation.origin_component_name
        if observation.origin_component_version:
            hash_string += observation.origin_component_version

    if observation.origin_docker_image_name:
        hash_string += observation.origin_docker_image_name
    elif observation.origin_docker_image_name_tag:
        hash_string += observation.origin_docker_image_name_tag

    if observation.origin_endpoint_url:
        hash_string += observation.origin_endpoint_url

    if observation.origin_service_name:
        hash_string += observation.origin_service_name

    if observation.origin_source_file:
        hash_string += observation.origin_source_file
    if observation.origin_source_line_start:
        hash_string += str(observation.origin_source_line_start)
    if observation.origin_source_line_end:
        hash_string += str(observation.origin_source_line_end)
    if observation.origin_source_file_link:
        hash_string += observation.origin_source_file_link

    if observation.origin_cloud_provider:
        hash_string += observation.origin_cloud_provider
    if observation.origin_cloud_account_subscription_project:
        hash_string += observation.origin_cloud_account_subscription_project
    if observation.origin_cloud_resource:
        hash_string += observation.origin_cloud_resource

    if observation.origin_kubernetes_cluster:
        hash_string += observation.origin_kubernetes_cluster
    if observation.origin_kubernetes_namespace:
        hash_string += observation.origin_kubernetes_namespace
    if observation.origin_kubernetes_resource_type:
        hash_string += observation.origin_kubernetes_resource_type
    if observation.origin_kubernetes_resource_name:
        hash_string += observation.origin_kubernetes_resource_name

    return hash_string


def get_current_severity(observation: Observation) -> str:
    if observation.cvss3_vector:
        observation.cvss3_score = CVSS3(observation.cvss3_vector).base_score

    if observation.cvss4_vector:
        observation.cvss4_score = CVSS4(observation.cvss4_vector).base_score

    if observation.assessment_severity:
        return observation.assessment_severity

    if observation.rule_severity:
        return observation.rule_severity

    if observation.parser_severity and observation.parser_severity != Severity.SEVERITY_UNKNOWN:
        return observation.parser_severity

    if observation.cvss4_score is not None:
        return get_cvss_severity(observation.cvss4_score)

    if observation.cvss3_score is not None:
        return get_cvss_severity(observation.cvss3_score)

    return Severity.SEVERITY_UNKNOWN


def get_cvss_severity(cvss_score: Decimal) -> str:
    if cvss_score is None:
        return Severity.SEVERITY_UNKNOWN

    if cvss_score >= 9:
        return Severity.SEVERITY_CRITICAL

    if cvss_score >= 7:
        return Severity.SEVERITY_HIGH

    if cvss_score >= 4:
        return Severity.SEVERITY_MEDIUM

    if cvss_score >= 0.1:
        return Severity.SEVERITY_LOW

    return Severity.SEVERITY_NONE


def get_current_status(observation: Observation) -> str:
    if observation.parser_status == Status.STATUS_RESOLVED:
        return observation.parser_status

    if observation.assessment_status:
        return observation.assessment_status

    if observation.rule_status:
        return observation.rule_status

    if observation.vex_status:
        return observation.vex_status

    if observation.parser_status:
        return observation.parser_status

    return Status.STATUS_OPEN


def get_current_vex_justification(observation: Observation) -> str:
    if observation.assessment_vex_justification:
        return observation.assessment_vex_justification

    if observation.rule_vex_justification:
        return observation.rule_vex_justification

    if observation.vex_vex_justification:
        return observation.vex_vex_justification

    if observation.parser_vex_justification:
        return observation.parser_vex_justification

    return ""


def normalize_observation_fields(observation: Observation) -> None:
    _normalize_origin_component(observation)
    _normalize_origin_docker(observation)
    _normalize_origin_endpoint(observation)
    _normalize_origin_cloud(observation)
    _normalize_origin_kubernetes(observation)

    _normalize_severity(observation)
    _normalize_status(observation)
    _normalize_vex_justification(observation)

    _normalize_description(observation)
    _normalize_vulnerability_ids(observation)
    _normalize_cvss_vectors(observation)

    _normalize_update_impact_score_and_fix_available(observation)

    if observation.recommendation is None:
        observation.recommendation = ""
    if observation.scanner_observation_id is None:
        observation.scanner_observation_id = ""
    if observation.origin_service_name is None:
        observation.origin_service_name = ""
    if observation.origin_source_file is None:
        observation.origin_source_file = ""
    if observation.origin_source_file_link is None:
        observation.origin_source_file_link = ""
    if observation.scanner is None:
        observation.scanner = ""
    if observation.api_configuration_name is None:
        observation.api_configuration_name = ""
    if observation.upload_filename is None:
        observation.upload_filename = ""
    if observation.issue_tracker_issue_id is None:
        observation.issue_tracker_issue_id = ""
    if observation.issue_tracker_jira_initial_status is None:
        observation.issue_tracker_jira_initial_status = ""


def _normalize_vulnerability_ids(observation: Observation) -> None:
    if observation.vulnerability_id is None:
        observation.vulnerability_id = ""
    if observation.vulnerability_id_aliases is None:
        observation.vulnerability_id_aliases = ""


def _normalize_cvss_vectors(observation: Observation) -> None:
    if observation.cvss3_vector is None:
        observation.cvss3_vector = ""
    if observation.cvss4_vector is None:
        observation.cvss4_vector = ""
    if observation.cve_found_in is None:
        observation.cve_found_in = ""


def _normalize_description(observation: Observation) -> None:
    if observation.description is None:
        observation.description = ""
    else:
        # Newlines at the end of the description are removed
        while observation.description.endswith("\n"):
            observation.description = observation.description[:-1]

        # \u0000 can lead to SQL exceptions
        observation.description = observation.description.replace("\u0000", "REDACTED_NULL")


def _normalize_origin_component(observation: Observation) -> None:  # pylint: disable=too-many-branches
    if not observation.origin_component_name_version:
        if observation.origin_component_name and observation.origin_component_version:
            observation.origin_component_name_version = (
                observation.origin_component_name + ":" + observation.origin_component_version
            )
        elif observation.origin_component_name:
            observation.origin_component_name_version = observation.origin_component_name
    else:
        component_parts = observation.origin_component_name_version.split(":")
        if len(component_parts) == 3:
            if component_parts[0] == observation.origin_component_name:
                observation.origin_component_version = f"{component_parts[1]}:{component_parts[2]}"
            else:
                observation.origin_component_name = f"{component_parts[0]}:{component_parts[1]}"
                observation.origin_component_version = component_parts[2]
        elif len(component_parts) == 2:
            observation.origin_component_name = component_parts[0]
            observation.origin_component_version = component_parts[1]
        elif len(component_parts) == 1:
            observation.origin_component_name = observation.origin_component_name_version
            observation.origin_component_version = ""

    if observation.origin_component_name_version is None:
        observation.origin_component_name_version = ""
    if observation.origin_component_name is None:
        observation.origin_component_name = ""
    if observation.origin_component_version is None:
        observation.origin_component_version = ""
    if observation.origin_component_purl is None:
        observation.origin_component_purl = ""
    if observation.origin_component_cpe is None:
        observation.origin_component_cpe = ""
    if observation.origin_component_cyclonedx_bom_link is None:
        observation.origin_component_cyclonedx_bom_link = ""
    if observation.origin_component_dependencies is None:
        observation.origin_component_dependencies = ""

    if observation.origin_component_purl:
        try:
            purl = PackageURL.from_string(observation.origin_component_purl)
            observation.origin_component_purl_type = purl.type
        except ValueError:
            observation.origin_component_purl = ""
            observation.origin_component_purl_type = ""

    if observation.origin_component_purl_type is None:
        observation.origin_component_purl_type = ""


def _normalize_origin_docker(observation: Observation) -> None:
    if not observation.origin_docker_image_name_tag:
        _normalize_origin_docker_image_name(observation)
    else:
        _normalize_origin_docker_image_name_tag(observation)

    if observation.origin_docker_image_name_tag:
        origin_docker_image_name_tag_parts = observation.origin_docker_image_name_tag.split("/")
        observation.origin_docker_image_name_tag_short = origin_docker_image_name_tag_parts[
            len(origin_docker_image_name_tag_parts) - 1
        ].strip()
    else:
        observation.origin_docker_image_name_tag_short = ""

    if observation.origin_docker_image_name_tag is None:
        observation.origin_docker_image_name_tag = ""
    if observation.origin_docker_image_name is None:
        observation.origin_docker_image_name = ""
    if observation.origin_docker_image_tag is None:
        observation.origin_docker_image_tag = ""
    if observation.origin_docker_image_digest is None:
        observation.origin_docker_image_digest = ""


def _normalize_origin_docker_image_name(observation: Observation) -> None:
    if observation.origin_docker_image_name and not observation.origin_docker_image_tag:
        docker_image_parts = observation.origin_docker_image_name.split(":")
        if len(docker_image_parts) == 2:
            observation.origin_docker_image_name = docker_image_parts[0]
            observation.origin_docker_image_tag = docker_image_parts[1]

    if observation.origin_docker_image_name and observation.origin_docker_image_tag:
        observation.origin_docker_image_name_tag = (
            observation.origin_docker_image_name + ":" + observation.origin_docker_image_tag
        )
    else:
        observation.origin_docker_image_name_tag = observation.origin_docker_image_name


def _normalize_origin_docker_image_name_tag(observation: Observation) -> None:
    docker_image_parts = observation.origin_docker_image_name_tag.split(":")
    if len(docker_image_parts) == 2:
        observation.origin_docker_image_name = docker_image_parts[0]
        observation.origin_docker_image_tag = docker_image_parts[1]
    else:
        observation.origin_docker_image_name = observation.origin_docker_image_name_tag


def _normalize_origin_endpoint(observation: Observation) -> None:
    if observation.origin_endpoint_url:
        parse_result = urlparse(observation.origin_endpoint_url)
        observation.origin_endpoint_scheme = parse_result.scheme
        observation.origin_endpoint_hostname = str(parse_result.hostname)
        observation.origin_endpoint_port = parse_result.port
        observation.origin_endpoint_path = parse_result.path
        observation.origin_endpoint_params = parse_result.params
        observation.origin_endpoint_query = parse_result.query
        observation.origin_endpoint_fragment = parse_result.fragment
    else:
        observation.origin_endpoint_scheme = ""
        observation.origin_endpoint_hostname = ""
        observation.origin_endpoint_port = None
        observation.origin_endpoint_path = ""
        observation.origin_endpoint_params = ""
        observation.origin_endpoint_query = ""
        observation.origin_endpoint_fragment = ""

    if observation.origin_endpoint_url is None:
        observation.origin_endpoint_url = ""
    if observation.origin_endpoint_scheme is None:
        observation.origin_endpoint_scheme = ""
    if observation.origin_endpoint_hostname is None:
        observation.origin_endpoint_hostname = ""
    if observation.origin_endpoint_path is None:
        observation.origin_endpoint_path = ""
    if observation.origin_endpoint_params is None:
        observation.origin_endpoint_params = ""
    if observation.origin_endpoint_query is None:
        observation.origin_endpoint_query = ""
    if observation.origin_endpoint_fragment is None:
        observation.origin_endpoint_fragment = ""


def _normalize_origin_cloud(observation: Observation) -> None:
    if observation.origin_cloud_provider is None:
        observation.origin_cloud_provider = ""
    if observation.origin_cloud_account_subscription_project is None:
        observation.origin_cloud_account_subscription_project = ""
    if observation.origin_cloud_resource is None:
        observation.origin_cloud_resource = ""
    if observation.origin_cloud_resource_type is None:
        observation.origin_cloud_resource_type = ""

    observation.origin_cloud_qualified_resource = ""
    if observation.origin_cloud_account_subscription_project:
        observation.origin_cloud_qualified_resource = (
            (observation.origin_cloud_account_subscription_project[:119] + "...")
            if len(observation.origin_cloud_account_subscription_project) > 122
            else observation.origin_cloud_account_subscription_project
        )
    if observation.origin_cloud_account_subscription_project and observation.origin_cloud_resource:
        observation.origin_cloud_qualified_resource += " / "
    if observation.origin_cloud_resource:
        observation.origin_cloud_qualified_resource += (
            (observation.origin_cloud_resource[:119] + "...")
            if len(observation.origin_cloud_resource) > 122
            else observation.origin_cloud_resource
        )


def _normalize_origin_kubernetes(observation: Observation) -> None:
    if observation.origin_kubernetes_cluster is None:
        observation.origin_kubernetes_cluster = ""
    if observation.origin_kubernetes_namespace is None:
        observation.origin_kubernetes_namespace = ""
    if observation.origin_kubernetes_resource_type is None:
        observation.origin_kubernetes_resource_type = ""
    if observation.origin_kubernetes_resource_name is None:
        observation.origin_kubernetes_resource_name = ""

    observation.origin_kubernetes_qualified_resource = ""
    if observation.origin_kubernetes_cluster:
        observation.origin_kubernetes_qualified_resource = (
            (observation.origin_kubernetes_cluster[:50] + "...")
            if len(observation.origin_kubernetes_cluster) > 53
            else observation.origin_kubernetes_cluster
        )
    if observation.origin_kubernetes_namespace:
        if observation.origin_kubernetes_qualified_resource:
            observation.origin_kubernetes_qualified_resource += " / "
        observation.origin_kubernetes_qualified_resource += (
            (observation.origin_kubernetes_namespace[:50] + "...")
            if len(observation.origin_kubernetes_namespace) > 53
            else observation.origin_kubernetes_namespace
        )
    if observation.origin_kubernetes_resource_name:
        if observation.origin_kubernetes_qualified_resource:
            observation.origin_kubernetes_qualified_resource += " / "
        observation.origin_kubernetes_qualified_resource += (
            (observation.origin_kubernetes_resource_name[:140] + "...")
            if len(observation.origin_kubernetes_resource_name) > 143
            else observation.origin_kubernetes_resource_name
        )


def _normalize_severity(observation: Observation) -> None:
    if observation.current_severity is None:
        observation.current_severity = ""
    if observation.assessment_severity is None:
        observation.assessment_severity = ""
    if observation.rule_severity is None:
        observation.rule_severity = ""
    if observation.parser_severity is None:
        observation.parser_severity = ""
    if (
        observation.parser_severity
        and (
            observation.parser_severity,
            observation.parser_severity,
        )
        not in Severity.SEVERITY_CHOICES
    ):
        observation.parser_severity = Severity.SEVERITY_UNKNOWN

    observation.current_severity = get_current_severity(observation)

    observation.numerical_severity = Severity.NUMERICAL_SEVERITIES.get(
        observation.current_severity, Severity.SEVERITY_UNKNOWN
    )


def _normalize_status(observation: Observation) -> None:
    if observation.current_status is None:
        observation.current_status = ""
    if observation.assessment_status is None:
        observation.assessment_status = ""
    if observation.rule_status is None:
        observation.rule_status = ""
    if observation.parser_status is None:
        observation.parser_status = ""
    if observation.vex_status is None:
        observation.vex_status = ""

    observation.current_status = get_current_status(observation)


def _normalize_vex_justification(observation: Observation) -> None:
    if observation.current_vex_justification is None:
        observation.current_vex_justification = ""
    if observation.assessment_vex_justification is None:
        observation.assessment_vex_justification = ""
    if observation.rule_vex_justification is None:
        observation.rule_vex_justification = ""
    if observation.parser_vex_justification is None:
        observation.parser_vex_justification = ""
    if observation.vex_vex_justification is None:
        observation.vex_vex_justification = ""

    observation.current_vex_justification = get_current_vex_justification(observation)


def _normalize_update_impact_score_and_fix_available(observation: Observation) -> None:
    observation.fix_available = None
    observation.update_impact_score = None

    if not observation.origin_component_name:
        return

    observation.fix_available = False

    recommendation_matches = (
        re.findall(VERSION_REGEX_COMPILED, observation.recommendation) if observation.recommendation else None
    )
    component_matches = (
        re.findall(VERSION_REGEX_COMPILED, observation.origin_component_version)
        if observation.origin_component_version
        else None
    )

    observation.fix_available = bool(recommendation_matches)

    if not recommendation_matches or not component_matches:
        return

    observation.fix_available = True

    recommendation_version = None
    if len(recommendation_matches) == 1:
        recommendation_version = _parse_version(recommendation_matches[0])
    else:
        component_name = re.sub(r":\d+", "", observation.origin_component_name)
        search_prefix = rf"(?:Upgrade (?:\S+:)?{component_name} to version)"
        match = re.findall(rf"{search_prefix}{VERSION_REGEX}", observation.recommendation)
        if match:
            recommendation_version = _parse_version(match[0])

    if recommendation_version:
        component_version = _parse_version(component_matches[0])
        major_diff = max(recommendation_version[0] - component_version[0], 0)
        minor_diff = max(recommendation_version[1] - component_version[1], 0)
        patch_diff = max(recommendation_version[2] - component_version[2], 0)

        if major_diff > 0:
            observation.update_impact_score = major_diff * 100
        elif minor_diff > 0:
            observation.update_impact_score = minor_diff * 10
        else:
            observation.update_impact_score = patch_diff


def _parse_version(version: str) -> tuple[int, ...]:
    parts = version.split(".")[:3]
    # Filter out empty strings
    parts = [part for part in parts if part]
    rettuple = tuple(map(int, parts))
    for _ in range(3 - len(rettuple)):
        rettuple += (0,)
    return rettuple


def set_product_flags(observation: Observation) -> None:
    product_changed = False

    if observation.origin_cloud_qualified_resource and not observation.product.has_cloud_resource:
        observation.product.has_cloud_resource = True
        product_changed = True

    if observation.origin_component_name_version and not observation.product.has_component:
        observation.product.has_component = True
        product_changed = True

    if observation.origin_docker_image_name_tag and not observation.product.has_docker_image:
        observation.product.has_docker_image = True
        product_changed = True

    if observation.origin_endpoint_url and not observation.product.has_endpoint:
        observation.product.has_endpoint = True
        product_changed = True

    if observation.origin_kubernetes_qualified_resource and not observation.product.has_kubernetes_resource:
        observation.product.has_kubernetes_resource = True
        product_changed = True

    if observation.origin_source_file and not observation.product.has_source:
        observation.product.has_source = True
        product_changed = True

    if observation.has_potential_duplicates and not observation.product.has_potential_duplicates:
        observation.product.has_potential_duplicates = True
        product_changed = True

    if product_changed:
        observation.product.save()
