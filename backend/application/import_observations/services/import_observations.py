import os
from dataclasses import dataclass
from typing import Optional, Tuple

from django.core.files.base import File
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from application.commons.models import Settings
from application.commons.services.functions import clip_fields
from application.core.models import (
    Branch,
    Evidence,
    Observation,
    Product,
    Reference,
    Service,
)
from application.core.queries.observation import (
    get_observations_for_vulnerability_check,
)
from application.core.services.observation import (
    get_current_severity,
    get_current_status,
    get_identity_hash,
    normalize_observation_fields,
)
from application.core.services.observation_log import create_observation_log
from application.core.services.potential_duplicates import find_potential_duplicates
from application.core.services.product import set_repository_default_branch
from application.core.services.risk_acceptance_expiry import (
    calculate_risk_acceptance_expiry_date,
)
from application.core.services.security_gate import check_security_gate
from application.core.types import Assessment_Status, Status
from application.epss.services.cvss_bt import apply_exploit_information
from application.epss.services.epss import apply_epss
from application.import_observations.exceptions import ParserError
from application.import_observations.models import (
    Api_Configuration,
    Parser,
    Vulnerability_Check,
)
from application.import_observations.parsers.base_parser import (
    BaseAPIParser,
    BaseFileParser,
)
from application.import_observations.services.parser_detector import (
    detect_parser,
    instanciate_parser,
)
from application.issue_tracker.services.issue_tracker import (
    push_observations_to_issue_tracker,
)
from application.licenses.models import (
    License_Component,
    License_Component_Evidence,
)
from application.licenses.services.concluded_license import ConcludeLicenseApplicator
from application.licenses.services.license_component import (
    prepare_license_component,
    set_effective_license,
)
from application.licenses.services.license_policy import apply_license_policy_product
from application.licenses.services.spdx_license_cache import SPDXLicenseCache
from application.licenses.types import NO_LICENSE_INFORMATION
from application.rules.services.rule_engine import Rule_Engine
from application.vex.services.vex_engine import VEX_Engine


SBOM_BULK_BATCH_SIZE = 100


@dataclass
class ImportParameters:
    product: Product
    branch: Optional[Branch]
    service: Optional[Service]
    parser: Parser
    filename: str
    api_configuration_name: str
    docker_image_name_tag: str
    endpoint_url: str
    kubernetes_cluster: str
    imported_observations: list[Observation]


@dataclass
class FileUploadParameters:
    product: Product
    branch: Optional[Branch]
    file: File
    service_name: str
    docker_image_name_tag: str
    endpoint_url: str
    kubernetes_cluster: str
    suppress_licenses: bool
    sbom: bool


@dataclass
class ApiImportParameters:
    api_configuration: Api_Configuration
    branch: Optional[Branch]
    service_name: str
    docker_image_name_tag: str
    endpoint_url: str
    kubernetes_cluster: str


def file_upload_observations(
    file_upload_parameters: FileUploadParameters,
) -> Tuple[int, int, int, int, int, int]:

    settings = Settings.load()
    parser, parser_instance, data = detect_parser(file_upload_parameters.file)
    filename = os.path.basename(file_upload_parameters.file.name) if file_upload_parameters.file.name else ""

    numbers_observations: Tuple[int, int, int] = 0, 0, 0
    new_observations = None
    updated_observations = None
    resolved_observations = None

    scanner = ""

    service = None
    if file_upload_parameters.service_name:
        service = Service.objects.get_or_create(
            product=file_upload_parameters.product, name=file_upload_parameters.service_name
        )[0]

    if not file_upload_parameters.sbom:
        imported_observations, scanner = parser_instance.get_observations(
            data, file_upload_parameters.product, file_upload_parameters.branch
        )

        import_parameters = ImportParameters(
            product=file_upload_parameters.product,
            branch=file_upload_parameters.branch,
            service=service,
            parser=parser,
            filename=filename,
            api_configuration_name="",
            docker_image_name_tag=file_upload_parameters.docker_image_name_tag,
            endpoint_url=file_upload_parameters.endpoint_url,
            kubernetes_cluster=file_upload_parameters.kubernetes_cluster,
            imported_observations=imported_observations,
        )

        numbers_observations = _process_data(import_parameters, settings)
        new_observations = numbers_observations[0]
        updated_observations = numbers_observations[1]
        resolved_observations = numbers_observations[2]
    else:
        if not isinstance(parser_instance, BaseFileParser) or not parser_instance.sbom():
            raise ValidationError(f"{parser.name} is not a SBOM parser")

    vulnerability_check, _ = Vulnerability_Check.objects.update_or_create(
        product=file_upload_parameters.product,
        branch=file_upload_parameters.branch,
        service=service,
        filename=filename,
        api_configuration_name="",
        defaults={
            "last_import_observations_new": new_observations,
            "last_import_observations_updated": updated_observations,
            "last_import_observations_resolved": resolved_observations,
            "last_import_licenses_new": None,
            "last_import_licenses_updated": None,
            "last_import_licenses_deleted": None,
            "scanner": scanner,
        },
    )

    numbers_license_components = (0, 0, 0)
    if settings.feature_license_management and (
        not file_upload_parameters.suppress_licenses or file_upload_parameters.sbom
    ):
        imported_license_components, scanner = parser_instance.get_license_components(data)
        numbers_license_components = process_license_components(
            imported_license_components, scanner, vulnerability_check
        )

    return (
        numbers_observations[0],
        numbers_observations[1],
        numbers_observations[2],
        numbers_license_components[0],
        numbers_license_components[1],
        numbers_license_components[2],
    )


def api_import_observations(
    api_import_parameters: ApiImportParameters,
) -> Tuple[int, int, int]:
    parser_instance = instanciate_parser(api_import_parameters.api_configuration.parser)

    if not isinstance(parser_instance, BaseAPIParser):
        raise ParserError(f"{api_import_parameters.api_configuration.parser.name} isn't an API parser")

    format_valid, errors, data = parser_instance.check_connection(api_import_parameters.api_configuration)
    if not format_valid:
        raise ValidationError("Connection couldn't be established: " + " / ".join(errors))

    imported_observations, scanner = parser_instance.get_observations(
        data,
        api_import_parameters.api_configuration.product,
        api_import_parameters.branch,
    )

    service = None
    if api_import_parameters.service_name:
        service = Service.objects.get_or_create(
            product=api_import_parameters.api_configuration.product, name=api_import_parameters.service_name
        )[0]

    import_parameters = ImportParameters(
        product=api_import_parameters.api_configuration.product,
        branch=api_import_parameters.branch,
        service=service,
        parser=api_import_parameters.api_configuration.parser,
        filename="",
        api_configuration_name=api_import_parameters.api_configuration.name,
        docker_image_name_tag=api_import_parameters.docker_image_name_tag,
        endpoint_url=api_import_parameters.endpoint_url,
        kubernetes_cluster=api_import_parameters.kubernetes_cluster,
        imported_observations=imported_observations,
    )

    numbers: Tuple[int, int, int] = _process_data(import_parameters, Settings.load())

    Vulnerability_Check.objects.update_or_create(
        product=import_parameters.product,
        branch=import_parameters.branch,
        service=service,
        filename="",
        api_configuration_name=import_parameters.api_configuration_name,
        defaults={
            "last_import_observations_new": numbers[0],
            "last_import_observations_updated": numbers[1],
            "last_import_observations_resolved": numbers[2],
            "scanner": scanner,
        },
    )

    return numbers[0], numbers[1], numbers[2]


def api_check_connection(
    api_configuration: Api_Configuration,
) -> Tuple[bool, list[str]]:
    parser_instance = instanciate_parser(api_configuration.parser)

    if not isinstance(parser_instance, BaseAPIParser):
        return False, [f"{api_configuration.parser.name} isn't an API parser"]

    format_valid, errors, _ = parser_instance.check_connection(api_configuration)

    return format_valid, errors


def _process_data(import_parameters: ImportParameters, settings: Settings) -> Tuple[int, int, int]:
    observations_new = 0
    observations_updated = 0

    rule_engine = Rule_Engine(product=import_parameters.product)
    vex_engine = VEX_Engine(import_parameters.product, import_parameters.branch)

    # Read current observations for the same vulnerability check, to find updated and resolved observations
    observations_before: dict[str, Observation] = {}
    for observation_before_for_dict in get_observations_for_vulnerability_check(
        import_parameters.product,
        import_parameters.branch,
        import_parameters.service,
        import_parameters.filename,
        import_parameters.api_configuration_name,
    ):
        observations_before[observation_before_for_dict.identity_hash] = observation_before_for_dict

    observations_this_run: set[str] = set()
    vulnerability_check_observations: set[Observation] = set()

    for imported_observation in import_parameters.imported_observations:
        # Set additional data in newly uploaded observation
        _prepare_imported_observation(
            import_parameters,
            imported_observation,
        )
        normalize_observation_fields(imported_observation)
        clip_fields("core", "Observation", imported_observation)
        imported_observation.identity_hash = get_identity_hash(imported_observation)

        # Only process observation if it hasn't been processed in this run before
        if imported_observation.identity_hash not in observations_this_run:
            # Check if new observation is already there in the same check
            observation_before = observations_before.get(imported_observation.identity_hash)
            if observation_before:
                _process_current_observation(imported_observation, observation_before, settings)

                rule_engine.apply_rules_for_observation(observation_before)
                vex_engine.apply_vex_statements_for_observation(observation_before)

                if observation_before.current_status == _get_initial_status(observation_before.product):
                    observations_updated += 1

                # Remove observation from list of current observations because it is still part of the check
                observations_before.pop(observation_before.identity_hash)
                # Add identity_hash to set of observations in this run to detect duplicates in this run
                observations_this_run.add(observation_before.identity_hash)
                vulnerability_check_observations.add(observation_before)
            else:
                _process_new_observation(imported_observation, settings)

                rule_engine.apply_rules_for_observation(imported_observation)
                vex_engine.apply_vex_statements_for_observation(imported_observation)

                if imported_observation.current_status == _get_initial_status(imported_observation.product):
                    observations_new += 1

                # Add identity_hash to set of observations in this run to detect duplicates in this run
                observations_this_run.add(imported_observation.identity_hash)
                vulnerability_check_observations.add(imported_observation)

    observations_resolved = _resolve_unimported_observations(observations_before)
    vulnerability_check_observations.update(observations_resolved)
    if import_parameters.branch == import_parameters.product.repository_default_branch:
        check_security_gate(import_parameters.product)
    set_repository_default_branch(import_parameters.product)
    if import_parameters.branch:
        import_parameters.branch.last_import = timezone.now()
        import_parameters.branch.save()
    push_observations_to_issue_tracker(import_parameters.product, vulnerability_check_observations)
    find_potential_duplicates(import_parameters.product, import_parameters.branch, import_parameters.service)

    return observations_new, observations_updated, len(observations_resolved)


def process_license_components(  # pylint: disable=too-many-statements disable=too-many-locals
    license_components: list[License_Component],
    scanner: str,
    vulnerability_check: Vulnerability_Check,
) -> Tuple[int, int, int]:
    existing_components = License_Component.objects.filter(
        product=vulnerability_check.product,
        branch=vulnerability_check.branch,
        upload_filename=vulnerability_check.filename,
    ).select_related("effective_spdx_license")

    existing_component: Optional[License_Component] = None
    existing_components_dict: dict[str, License_Component] = {}
    existing_component_ids: list[int] = []
    for existing_component in existing_components:
        existing_components_dict[existing_component.identity_hash] = existing_component
        existing_component_ids.append(existing_component.pk)

    License_Component_Evidence.objects.filter(license_component__in=existing_component_ids).delete()

    components_new = []
    components_updated = []

    spdx_cache = SPDXLicenseCache()
    concluded_license_applicator = ConcludeLicenseApplicator(vulnerability_check.product)

    license_component_evidences = []
    processed_hashes = set()

    for unsaved_component in license_components:
        prepare_license_component(unsaved_component, spdx_cache)

        if unsaved_component.identity_hash in processed_hashes:
            continue

        existing_component = existing_components_dict.get(unsaved_component.identity_hash)
        if existing_component:
            effective_spdx_license_before = existing_component.effective_spdx_license
            effective_non_spdx_license_before = existing_component.effective_non_spdx_license
            effective_license_expression_before = existing_component.effective_license_expression
            effective_multiple_licenses_before = existing_component.effective_multiple_licenses
            evaluation_result_before = existing_component.evaluation_result
            existing_component.component_purl = unsaved_component.component_purl
            existing_component.component_purl_type = unsaved_component.component_purl_type
            existing_component.component_cpe = unsaved_component.component_cpe
            existing_component.component_dependencies = unsaved_component.component_dependencies
            existing_component.component_cyclonedx_bom_link = unsaved_component.component_cyclonedx_bom_link
            existing_component.imported_declared_license_name = unsaved_component.imported_declared_license_name
            existing_component.imported_declared_spdx_license = unsaved_component.imported_declared_spdx_license
            existing_component.imported_declared_non_spdx_license = unsaved_component.imported_declared_non_spdx_license
            existing_component.imported_declared_license_expression = (
                unsaved_component.imported_declared_license_expression
            )
            existing_component.imported_declared_multiple_licenses = (
                unsaved_component.imported_declared_multiple_licenses
            )
            existing_component.imported_concluded_license_name = unsaved_component.imported_concluded_license_name
            existing_component.imported_concluded_spdx_license = unsaved_component.imported_concluded_spdx_license
            existing_component.imported_concluded_non_spdx_license = (
                unsaved_component.imported_concluded_non_spdx_license
            )
            existing_component.imported_concluded_license_expression = (
                unsaved_component.imported_concluded_license_expression
            )
            existing_component.imported_concluded_multiple_licenses = (
                unsaved_component.imported_concluded_multiple_licenses
            )

            existing_component.import_last_seen = timezone.now()
            if (
                effective_spdx_license_before != existing_component.effective_spdx_license
                or effective_non_spdx_license_before != existing_component.effective_non_spdx_license
                or effective_license_expression_before != existing_component.effective_license_expression
                or effective_multiple_licenses_before != existing_component.effective_multiple_licenses
                or evaluation_result_before != existing_component.evaluation_result
            ):
                existing_component.last_change = timezone.now()

            set_effective_license(existing_component)
            if (
                not existing_component.manual_concluded_license_name
                or existing_component.manual_concluded_license_name == NO_LICENSE_INFORMATION
            ):
                concluded_license_applicator.apply_concluded_license(existing_component)
                set_effective_license(existing_component)

            clip_fields("licenses", "License_Component", existing_component)
            components_updated.append(existing_component)

            license_component_evidences += _process_license_evidences(unsaved_component, existing_component)

            existing_components_dict.pop(unsaved_component.identity_hash)
        else:
            unsaved_component.product = vulnerability_check.product
            unsaved_component.branch = vulnerability_check.branch
            unsaved_component.origin_service = vulnerability_check.service
            unsaved_component.upload_filename = vulnerability_check.filename

            unsaved_component.import_last_seen = timezone.now()
            unsaved_component.last_change = timezone.now()

            set_effective_license(unsaved_component)
            concluded_license_applicator.apply_concluded_license(unsaved_component)
            set_effective_license(unsaved_component)

            clip_fields("licenses", "License_Component", unsaved_component)
            components_new.append(unsaved_component)

        processed_hashes.add(unsaved_component.identity_hash)

    License_Component.objects.bulk_update(
        components_updated,
        [
            "component_purl",
            "component_purl_type",
            "component_cpe",
            "component_dependencies",
            "component_cyclonedx_bom_link",
            "imported_declared_license_name",
            "imported_declared_spdx_license",
            "imported_declared_license_expression",
            "imported_declared_non_spdx_license",
            "imported_declared_multiple_licenses",
            "imported_concluded_license_name",
            "imported_concluded_spdx_license",
            "imported_concluded_license_expression",
            "imported_concluded_non_spdx_license",
            "imported_concluded_multiple_licenses",
            "manual_concluded_license_name",
            "manual_concluded_spdx_license",
            "manual_concluded_license_expression",
            "manual_concluded_non_spdx_license",
            "manual_concluded_comment",
            "effective_license_name",
            "effective_spdx_license",
            "effective_license_expression",
            "effective_non_spdx_license",
            "effective_multiple_licenses",
            "evaluation_result",
            "numerical_evaluation_result",
            "import_last_seen",
            "last_change",
        ],
        SBOM_BULK_BATCH_SIZE,
    )

    inserted_components = License_Component.objects.bulk_create(components_new, SBOM_BULK_BATCH_SIZE)
    for inserted_component in inserted_components:
        license_component_evidences += _process_license_evidences(inserted_component, inserted_component)

    License_Component_Evidence.objects.bulk_create(license_component_evidences, SBOM_BULK_BATCH_SIZE)

    components_deleted = len(existing_components_dict)
    license_component_ids: list[int] = []
    for existing_component in existing_components_dict.values():
        license_component_ids.append(existing_component.pk)
    License_Component.objects.filter(pk__in=license_component_ids).delete()

    if len(components_new) == 0 and len(components_updated) == 0 and components_deleted == 0:
        vulnerability_check.last_import_licenses_new = None
        vulnerability_check.last_import_licenses_updated = None
        vulnerability_check.last_import_licenses_deleted = None
    else:
        vulnerability_check.last_import_licenses_new = len(components_new)
        vulnerability_check.last_import_licenses_updated = len(components_updated)
        vulnerability_check.last_import_licenses_deleted = components_deleted

    if scanner:
        vulnerability_check.scanner = scanner
    vulnerability_check.save()

    apply_license_policy_product(spdx_cache, vulnerability_check.product, vulnerability_check.branch)

    return len(components_new), len(components_updated), components_deleted


def _process_license_evidences(
    source_component: License_Component, target_component: License_Component
) -> list[License_Component_Evidence]:
    license_component_evidences = []

    if source_component.unsaved_evidences:
        for unsaved_evidence in source_component.unsaved_evidences:
            evidence = License_Component_Evidence(
                license_component=target_component,
                name=unsaved_evidence[0],
                evidence=unsaved_evidence[1],
            )
            clip_fields("licenses", "License_Component_Evidence", evidence)
            license_component_evidences.append(evidence)

    return license_component_evidences


def _prepare_imported_observation(import_parameters: ImportParameters, imported_observation: Observation) -> None:
    imported_observation.product = import_parameters.product
    imported_observation.branch = import_parameters.branch
    imported_observation.parser = import_parameters.parser
    if not imported_observation.scanner:
        imported_observation.scanner = import_parameters.parser.name
    imported_observation.upload_filename = import_parameters.filename
    imported_observation.api_configuration_name = import_parameters.api_configuration_name
    imported_observation.import_last_seen = timezone.now()
    imported_observation.origin_service = import_parameters.service
    if import_parameters.service:
        imported_observation.origin_service_name = import_parameters.service.name
    if import_parameters.docker_image_name_tag:
        imported_observation.origin_docker_image_name_tag = import_parameters.docker_image_name_tag
    if import_parameters.endpoint_url:
        imported_observation.origin_endpoint_url = import_parameters.endpoint_url
    if import_parameters.kubernetes_cluster:
        imported_observation.origin_kubernetes_cluster = import_parameters.kubernetes_cluster


def _process_current_observation(
    imported_observation: Observation, observation_before: Observation, settings: Settings
) -> None:
    # Set data in the current observation from the new observation
    observation_before.title = imported_observation.title
    observation_before.description = imported_observation.description
    observation_before.recommendation = imported_observation.recommendation
    observation_before.scanner_observation_id = imported_observation.scanner_observation_id
    observation_before.vulnerability_id = imported_observation.vulnerability_id
    observation_before.vulnerability_id_aliases = imported_observation.vulnerability_id_aliases
    observation_before.cvss3_score = imported_observation.cvss3_score
    observation_before.cvss3_vector = imported_observation.cvss3_vector
    observation_before.cvss4_score = imported_observation.cvss4_score
    observation_before.cvss4_vector = imported_observation.cvss4_vector
    observation_before.cwe = imported_observation.cwe
    observation_before.found = imported_observation.found
    observation_before.scanner = imported_observation.scanner

    observation_before.origin_component_dependencies = imported_observation.origin_component_dependencies

    previous_severity = observation_before.current_severity
    observation_before.parser_severity = imported_observation.parser_severity
    observation_before.current_severity = get_current_severity(observation_before)

    previous_status = observation_before.current_status
    if imported_observation.parser_status:
        observation_before.parser_status = imported_observation.parser_status
    else:
        # Reopen the current observation if it is resolved,
        # leave the status as is otherwise.
        if observation_before.parser_status == Status.STATUS_RESOLVED:
            observation_before.parser_status = _get_initial_status(observation_before.product)
    observation_before.current_status = get_current_status(observation_before)

    if observation_before.current_status == Status.STATUS_RISK_ACCEPTED:
        if previous_status != Status.STATUS_RISK_ACCEPTED:
            observation_before.risk_acceptance_expiry_date = calculate_risk_acceptance_expiry_date(
                observation_before.product
            )
    else:
        observation_before.risk_acceptance_expiry_date = None

    apply_epss(observation_before)
    apply_exploit_information(observation_before, settings)
    observation_before.import_last_seen = timezone.now()
    observation_before.save()

    observation_before.references.all().delete()
    if imported_observation.unsaved_references:
        for unsaved_reference in imported_observation.unsaved_references:
            reference = Reference(
                observation=observation_before,
                url=unsaved_reference,
            )
            clip_fields("core", "Reference", reference)
            reference.save()

    observation_before.evidences.all().delete()
    if imported_observation.unsaved_evidences:
        for unsaved_evidence in imported_observation.unsaved_evidences:
            evidence = Evidence(
                observation=observation_before,
                name=unsaved_evidence[0],
                evidence=unsaved_evidence[1],
            )
            clip_fields("core", "Evidence", evidence)
            evidence.save()

            # Write observation log if status or severity has been changed
    if previous_status != observation_before.current_status or previous_severity != observation_before.current_severity:
        status = observation_before.current_status if previous_status != observation_before.current_status else ""
        severity = (
            observation_before.current_severity if previous_severity != observation_before.current_severity else ""
        )

        create_observation_log(
            observation=observation_before,
            severity=severity,
            status=status,
            comment="Updated by parser",
            vex_justification="",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
            risk_acceptance_expiry_date=observation_before.risk_acceptance_expiry_date,
        )


def _process_new_observation(imported_observation: Observation, settings: Settings) -> None:
    imported_observation.current_severity = get_current_severity(imported_observation)

    if not imported_observation.parser_status:
        imported_observation.parser_status = _get_initial_status(imported_observation.product)

    imported_observation.current_status = get_current_status(imported_observation)

    imported_observation.risk_acceptance_expiry_date = (
        calculate_risk_acceptance_expiry_date(imported_observation.product)
        if imported_observation.current_status == Status.STATUS_RISK_ACCEPTED
        else None
    )

    # Observation has not been imported before, so it is a new one
    apply_epss(imported_observation)
    apply_exploit_information(imported_observation, settings)
    imported_observation.save()

    if imported_observation.unsaved_references:
        for unsaved_reference in imported_observation.unsaved_references:
            reference = Reference(
                observation=imported_observation,
                url=unsaved_reference,
            )
            clip_fields("core", "Reference", reference)
            reference.save()

    if imported_observation.unsaved_evidences:
        for unsaved_evidence in imported_observation.unsaved_evidences:
            evidence = Evidence(
                observation=imported_observation,
                name=unsaved_evidence[0],
                evidence=unsaved_evidence[1],
            )
            clip_fields("core", "Evidence", evidence)
            evidence.save()

    create_observation_log(
        observation=imported_observation,
        severity=imported_observation.current_severity,
        status=imported_observation.current_status,
        comment="Set by parser",
        vex_justification="",
        assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        risk_acceptance_expiry_date=imported_observation.risk_acceptance_expiry_date,
    )


def _resolve_unimported_observations(
    observations_before: dict[str, Observation],
) -> set[Observation]:
    # All observations that are still in observations_before are not in the imported scan
    # and seem to have been resolved.
    observations_resolved: set[Observation] = set()
    for observation in observations_before.values():
        old_status = get_current_status(observation)

        observation.parser_status = Status.STATUS_RESOLVED
        observation.save()

        new_status = get_current_status(observation)
        if old_status != new_status:
            if old_status == Status.STATUS_OPEN:
                observations_resolved.add(observation)

            observation.current_status = new_status
            create_observation_log(
                observation=observation,
                severity="",
                status=observation.current_status,
                comment="Observation not found in latest scan",
                vex_justification="",
                assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
                risk_acceptance_expiry_date=None,
            )

    return observations_resolved


def _get_new_observations_in_review(product: Product) -> bool:
    if product.product_group and product.product_group.new_observations_in_review:
        return True
    return product.new_observations_in_review


def _get_initial_status(product: Product) -> str:
    if _get_new_observations_in_review(product):
        return Status.STATUS_IN_REVIEW
    return Status.STATUS_OPEN
