import hashlib
import logging
import os
from dataclasses import dataclass
from typing import Optional, Tuple

from django.core.files.base import File
from django.db import transaction
from django.db.models.functions import MD5
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
from application.core.services.assessment import (
    set_propagated_assessment_for_new_observation,
)
from application.core.services.observation import (
    get_current_severity,
    get_current_status,
    get_field_values,
    get_identity_hash,
    normalize_observation_fields,
    save_changed_fields,
)
from application.core.services.observation_log import create_observation_log
from application.core.services.potential_duplicates import find_potential_duplicates
from application.core.services.risk_acceptance_expiry import (
    calculate_risk_acceptance_expiry_date,
)
from application.core.services.security_gate import check_security_gate
from application.core.types import (
    Assessment_Status,
    Observation_Log_Comment,
    Status,
)
from application.epss.models import EPSS_Score, Exploit_Information
from application.epss.queries.epss_score import get_epss_scores_by_cves
from application.epss.queries.exploit_information import (
    get_exploit_information_by_cves,
)
from application.epss.services.cvss_bt import (
    apply_exploit_information,
    get_cvss_bt_vector,
    save_cvss_bt_observation_log,
)
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
from application.import_observations.services.import_license_components import (
    process_license_components,
)
from application.import_observations.services.parser_detector import (
    detect_parser,
    instanciate_parser,
)
from application.issue_tracker.services.issue_tracker import (
    push_observations_to_issue_tracker,
)
from application.notifications.services.webhook_events import (
    emit_import_event,
    emit_observation_event,
    get_subscribed_webhooks,
)
from application.notifications.types import Webhook_Event_Type
from application.rules.services.rule_engine import Rule_Engine
from application.vex.services.vex_engine import VEX_Engine

logger = logging.getLogger("secobserve.import_observations")


@dataclass
class ImportParameters:  # pylint: disable=too-many-instance-attributes
    product: Product
    branch: Optional[Branch]
    service: Optional[Service]
    parser: Parser
    filename: str
    api_configuration_name: str
    docker_image_name_tag: str
    endpoint_url: str
    kubernetes_cluster: str
    kubernetes_namespace: str
    kubernetes_resource_type: str
    kubernetes_resource_name: str
    imported_observations: list[Observation]


@dataclass
class FileUploadParameters:  # pylint: disable=too-many-instance-attributes
    product: Product
    branch: Optional[Branch]
    file: File
    service_name: str
    docker_image_name_tag: str
    endpoint_url: str
    kubernetes_cluster: str
    kubernetes_namespace: str
    kubernetes_resource_type: str
    kubernetes_resource_name: str
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
    kubernetes_namespace: str
    kubernetes_resource_type: str
    kubernetes_resource_name: str


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
            kubernetes_namespace=file_upload_parameters.kubernetes_namespace,
            kubernetes_resource_type=file_upload_parameters.kubernetes_resource_type,
            kubernetes_resource_name=file_upload_parameters.kubernetes_resource_name,
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
        kubernetes_namespace=api_import_parameters.kubernetes_namespace,
        kubernetes_resource_type=api_import_parameters.kubernetes_resource_type,
        kubernetes_resource_name=api_import_parameters.kubernetes_resource_name,
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


def _process_data(  # pylint: disable=too-many-statements disable=too-many-locals
    import_parameters: ImportParameters, settings: Settings
) -> Tuple[int, int, int]:
    observations_before_query = get_observations_for_vulnerability_check(
        import_parameters.product,
        import_parameters.branch,
        import_parameters.service,
        import_parameters.filename,
        import_parameters.api_configuration_name,
    )
    if not transaction.get_autocommit():
        # The import locks the product (with its change timestamp) and all these observations anyway. Lock them
        # first, the product before the observations by id, in the order of find_potential_duplicates and EPSS.
        Product.objects.select_for_update().filter(pk=import_parameters.product.pk).first()
        list(observations_before_query.select_for_update().order_by("pk").values_list("pk", flat=True))

    observations_new = 0
    observations_updated = 0

    rule_engine = Rule_Engine(product=import_parameters.product)
    vex_engine = VEX_Engine(import_parameters.product, import_parameters.branch)

    # Read current observations for the same vulnerability check, to find updated and resolved observations
    observations_before: dict[str, Observation] = {}
    for observation_before_for_dict in observations_before_query:
        # One product instance for all observations, it collects the change timestamp of all their logs
        observation_before_for_dict.product = import_parameters.product
        # The query filters by this branch, setting it saves reading it per observation, e.g. for Rego rules
        observation_before_for_dict.branch = import_parameters.branch
        observations_before[observation_before_for_dict.identity_hash] = observation_before_for_dict

    references_by_observation, evidences_by_observation = _get_references_and_evidences(
        list(observations_before.values())
    )

    # Only in a transaction, without one a crash could leave committed changes without a new change timestamp
    import_parameters.product.defer_observation_change = not transaction.get_autocommit()

    observations_this_run: set[str] = set()
    vulnerability_check_observations: set[Observation] = set()

    # EPSS scores and exploit information are read for every observation of the import, so they
    # are looked up in one query per batch instead of two queries per observation
    cves = [
        imported_observation.vulnerability_id
        for imported_observation in import_parameters.imported_observations
        if (imported_observation.vulnerability_id or "").startswith("CVE-")
    ]
    epss_scores = get_epss_scores_by_cves(cves)
    exploit_informations = get_exploit_information_by_cves(cves)
    created_webhooks = get_subscribed_webhooks(Webhook_Event_Type.OBSERVATION_CREATED, import_parameters.product)

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
                _process_current_observation(
                    imported_observation, observation_before, settings, epss_scores, exploit_informations
                )
                # Popped, because they aren't needed anymore, which frees the memory during a large import
                _update_references(
                    observation_before,
                    imported_observation.unsaved_references,
                    references_by_observation.pop(observation_before.pk, []),
                )
                _update_evidences(
                    observation_before,
                    imported_observation.unsaved_evidences,
                    evidences_by_observation.pop(observation_before.pk, []),
                )

                rule_engine.apply_rules_for_observation(observation_before)
                vex_engine.apply_vex_statements_for_observation(observation_before)

                if observation_before.current_status in Status.STATUS_ACTIVE:
                    observations_updated += 1

                # Remove observation from list of current observations because it is still part of the check,
                # with the identity_hash it has been found with, saving it might have changed its own identity_hash
                observations_before.pop(imported_observation.identity_hash)
                # Add identity_hash to set of observations in this run to detect duplicates in this run
                observations_this_run.add(imported_observation.identity_hash)
                vulnerability_check_observations.add(observation_before)
            else:
                if not _deduplicate_cross_scanner(imported_observation, settings):
                    _process_new_observation(imported_observation, settings, epss_scores, exploit_informations)

                    set_propagated_assessment_for_new_observation(imported_observation)

                    rule_engine.apply_rules_for_observation(imported_observation)
                    vex_engine.apply_vex_statements_for_observation(imported_observation)

                    if imported_observation.current_status in Status.STATUS_ACTIVE:
                        observations_new += 1
                        emit_observation_event(
                            Webhook_Event_Type.OBSERVATION_CREATED, imported_observation, created_webhooks
                        )

                    # Add identity_hash to set of observations in this run to detect duplicates in this run
                    observations_this_run.add(imported_observation.identity_hash)
                    vulnerability_check_observations.add(imported_observation)

    observations_resolved = _resolve_unimported_observations(observations_before)
    vulnerability_check_observations.update(observations_resolved)

    import_parameters.product.defer_observation_change = False
    if "last_observation_change" in import_parameters.product.get_dirty_fields():
        import_parameters.product.save(update_fields=["last_observation_change"])

    if (not import_parameters.branch and not import_parameters.product.repository_default_branch) or (
        import_parameters.branch and import_parameters.branch.is_default_branch
    ):
        check_security_gate(import_parameters.product)

    if import_parameters.branch:
        import_parameters.branch.last_import = timezone.now()
        import_parameters.branch.save()

    push_observations_to_issue_tracker(import_parameters.product, vulnerability_check_observations)
    find_potential_duplicates(import_parameters.product, import_parameters.branch, import_parameters.service)

    numbers = (observations_new, observations_updated, len(observations_resolved))
    emit_import_event(
        product=import_parameters.product,
        branch=import_parameters.branch,
        service=import_parameters.service,
        parser_name=import_parameters.parser.name,
        filename=import_parameters.filename,
        api_configuration_name=import_parameters.api_configuration_name,
        numbers=numbers,
    )

    return numbers


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
    if import_parameters.docker_image_name_tag:
        imported_observation.origin_docker_image_name_tag = import_parameters.docker_image_name_tag
    if import_parameters.endpoint_url:
        imported_observation.origin_endpoint_url = import_parameters.endpoint_url
    if import_parameters.kubernetes_cluster:
        imported_observation.origin_kubernetes_cluster = import_parameters.kubernetes_cluster
    if import_parameters.kubernetes_namespace:
        imported_observation.origin_kubernetes_namespace = import_parameters.kubernetes_namespace
    if import_parameters.kubernetes_resource_type:
        imported_observation.origin_kubernetes_resource_type = import_parameters.kubernetes_resource_type
    if import_parameters.kubernetes_resource_name:
        imported_observation.origin_kubernetes_resource_name = import_parameters.kubernetes_resource_name


def _process_current_observation(
    imported_observation: Observation,
    observation_before: Observation,
    settings: Settings,
    epss_scores: dict[str, EPSS_Score],
    exploit_informations: dict[str, Exploit_Information],
) -> None:
    values_before = get_field_values(observation_before)

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

    _update_origins(imported_observation, observation_before)

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

    observation_before.fix_available = imported_observation.fix_available
    observation_before.update_impact_score = imported_observation.update_impact_score

    apply_epss(observation_before, epss_scores)
    cvss3_vector_before = observation_before.cvss3_vector
    cvss4_vector_before = observation_before.cvss4_vector
    apply_exploit_information(observation_before, settings, exploit_informations)
    cvss_bt_vector = get_cvss_bt_vector(observation_before, cvss3_vector_before, cvss4_vector_before)
    observation_before.import_last_seen = timezone.now()

    # Write observation log if status or severity has been changed, it saves the observation as well
    if (
        previous_status == observation_before.current_status
        and previous_severity == observation_before.current_severity
    ):
        save_changed_fields(observation_before, values_before)
    else:
        status = observation_before.current_status if previous_status != observation_before.current_status else ""
        severity = (
            observation_before.current_severity if previous_severity != observation_before.current_severity else ""
        )

        create_observation_log(
            observation=observation_before,
            severity=severity,
            status=status,
            priority=None,
            priority_changed=False,
            comment=Observation_Log_Comment.COMMENT_UPDATED_BY_PARSER,
            vex_justification="",
            vex_remediations=None,
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
            risk_acceptance_expiry_date=observation_before.risk_acceptance_expiry_date,
            values_before=values_before,
        )

    # Without a vector from the parser, cvss-bt sets the stored vector again with every import
    if cvss_bt_vector and cvss_bt_vector not in (values_before["cvss3_vector"], values_before["cvss4_vector"]):
        # The log entry of the parser contains the changed severity
        save_cvss_bt_observation_log(observation_before, cvss_bt_vector, "")


def _update_origins(imported_observation: Observation, observation_before: Observation) -> None:
    # Only the fields of the origins that can change without changing the identity hash. The CycloneDX BOM link
    # is left out, because VEX statements are matched by it and it changes with every newly generated SBOM.
    observation_before.origin_component = imported_observation.origin_component
    observation_before.origin_component_type = imported_observation.origin_component_type
    observation_before.origin_component_purl = imported_observation.origin_component_purl
    observation_before.origin_component_purl_type = imported_observation.origin_component_purl_type
    observation_before.origin_component_cpe = imported_observation.origin_component_cpe
    observation_before.origin_component_dependencies = imported_observation.origin_component_dependencies
    observation_before.origin_component_url = imported_observation.origin_component_url

    observation_before.origin_docker_image_name_tag = imported_observation.origin_docker_image_name_tag
    observation_before.origin_docker_image_tag = imported_observation.origin_docker_image_tag
    observation_before.origin_docker_image_digest = imported_observation.origin_docker_image_digest

    observation_before.origin_cloud_resource_type = imported_observation.origin_cloud_resource_type


def _process_new_observation(
    imported_observation: Observation,
    settings: Settings,
    epss_scores: dict[str, EPSS_Score],
    exploit_informations: dict[str, Exploit_Information],
) -> None:
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
    apply_epss(imported_observation, epss_scores)
    cvss3_vector_before = imported_observation.cvss3_vector
    cvss4_vector_before = imported_observation.cvss4_vector
    severity_before = imported_observation.current_severity
    apply_exploit_information(imported_observation, settings, exploit_informations)
    imported_observation.save()

    # The observation has just been created, so there are no references and evidences to compare with
    Reference.objects.bulk_create(_build_references(imported_observation, imported_observation.unsaved_references))
    Evidence.objects.bulk_create(_build_evidences(imported_observation, imported_observation.unsaved_evidences))

    create_observation_log(
        observation=imported_observation,
        # The severity from the parser, a change by cvss-bt gets its own log entry
        severity=severity_before,
        status=imported_observation.current_status,
        priority=None,
        priority_changed=False,
        comment=Observation_Log_Comment.COMMENT_SET_BY_PARSER,
        vex_justification="",
        vex_remediations=None,
        assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
        risk_acceptance_expiry_date=imported_observation.risk_acceptance_expiry_date,
    )

    cvss_bt_vector = get_cvss_bt_vector(imported_observation, cvss3_vector_before, cvss4_vector_before)
    if cvss_bt_vector:
        severity = (
            imported_observation.current_severity if imported_observation.current_severity != severity_before else ""
        )
        save_cvss_bt_observation_log(imported_observation, cvss_bt_vector, severity)


def _get_references_and_evidences(
    observations: list[Observation],
) -> Tuple[dict[int, list[str]], dict[int, list[tuple[str, str]]]]:
    """
    Reads the references and evidences of all observations in one query each, instead of two queries per
    observation in _update_references and _update_evidences. Returns them by observation id.

    Only plain values are read, no model instances, to keep a large vulnerability check small in memory.
    The evidences carry the raw finding of the scanner, which is the largest column of an import,
    so only its hash is read.
    """
    references: dict[int, list[str]] = {}
    evidences: dict[int, list[tuple[str, str]]] = {}
    if not observations:
        return references, evidences

    observation_ids = [observation.pk for observation in observations]

    for observation_id, url in (
        Reference.objects.filter(observation_id__in=observation_ids).order_by("id").values_list("observation_id", "url")
    ):
        references.setdefault(observation_id, []).append(url)

    for observation_id, name, evidence_md5 in (
        Evidence.objects.filter(observation_id__in=observation_ids)
        .annotate(evidence_md5=MD5("evidence"))
        .order_by("id")
        .values_list("observation_id", "name", "evidence_md5")
    ):
        evidences.setdefault(observation_id, []).append((name, evidence_md5))

    return references, evidences


def _build_references(observation: Observation, unsaved_references: list[str]) -> list[Reference]:
    references = []
    for unsaved_reference in unsaved_references or []:
        reference = Reference(observation=observation, url=unsaved_reference)
        clip_fields("core", "Reference", reference)
        references.append(reference)
    return references


def _build_evidences(observation: Observation, unsaved_evidences: list[list[str]]) -> list[Evidence]:
    evidences = []
    for unsaved_evidence in unsaved_evidences or []:
        evidence = Evidence(observation=observation, name=unsaved_evidence[0], evidence=unsaved_evidence[1])
        clip_fields("core", "Evidence", evidence)
        evidences.append(evidence)
    return evidences


def _update_references(observation: Observation, unsaved_references: list[str], references_before: list[str]) -> None:
    """
    references_before are the URLs of the observation's references, read with _get_references_and_evidences.
    """
    references = _build_references(observation, unsaved_references)

    # A re-import of an unchanged observation finds the same references. Comparing them costs no
    # query, rewriting them is one query per reference, on every import of every observation.
    if [reference.url for reference in references] == references_before:
        return

    if references_before:
        Reference.objects.filter(observation=observation).delete()
    Reference.objects.bulk_create(references)


def _update_evidences(
    observation: Observation, unsaved_evidences: list[list[str]], evidences_before: list[tuple[str, str]]
) -> None:
    """
    evidences_before are the names and MD5 hashes of the observation's evidences,
    read with _get_references_and_evidences.
    """
    evidences = _build_evidences(observation, unsaved_evidences)

    # Same as for the references, but compared by the hash of the evidence. Should the database
    # hash an evidence differently, e.g. because of its character set, it is rewritten every time.
    if [(evidence.name, _md5(evidence.evidence)) for evidence in evidences] == evidences_before:
        return

    if evidences_before:
        Evidence.objects.filter(observation=observation).delete()
    Evidence.objects.bulk_create(evidences)


def _md5(value: str) -> str:
    # Same as the MD5 function of the database, only used to detect changes
    return hashlib.md5(value.encode("utf-8"), usedforsecurity=False).hexdigest()


def _deduplicate_cross_scanner(observation: Observation, settings: Settings) -> bool:
    if not settings.feature_cross_scanner_deduplication:
        return False

    duplicate_found = (
        Observation.objects.filter(
            product=observation.product,
            title=observation.title,
            branch=observation.branch,
            origin_service=observation.origin_service,
            origin_component_name_version=observation.origin_component_name_version,
            origin_docker_image_name_tag=observation.origin_docker_image_name_tag,
            origin_endpoint_url=observation.origin_endpoint_url,
            origin_source_file=observation.origin_source_file,
            origin_source_line_start=observation.origin_source_line_start,
            origin_source_line_end=observation.origin_source_line_end,
            origin_cloud_qualified_resource=observation.origin_cloud_qualified_resource,
            origin_kubernetes_qualified_resource=observation.origin_kubernetes_qualified_resource,
        )
        .exclude(scanner=observation.scanner)
        .exists()
    )

    if duplicate_found:
        logger.info("Cross scanner deduplication / Observation already saved: %s", observation.title)
        return True

    return False


def _resolve_unimported_observations(
    observations_before: dict[str, Observation],
) -> set[Observation]:
    # All observations that are still in observations_before are not in the imported scan
    # and seem to have been resolved.
    observations_resolved: set[Observation] = set()
    for observation in observations_before.values():
        # Resolved by an earlier import, there is nothing to change
        if observation.parser_status == Status.STATUS_RESOLVED:
            continue

        values_before = get_field_values(observation)
        old_status = get_current_status(observation)
        observation.parser_status = Status.STATUS_RESOLVED
        new_status = get_current_status(observation)

        if old_status == new_status:
            save_changed_fields(observation, values_before)
        else:
            if old_status in Status.STATUS_ACTIVE:
                observations_resolved.add(observation)

            observation.current_status = new_status
            # Saves the observation as well
            create_observation_log(
                observation=observation,
                severity="",
                status=observation.current_status,
                priority=None,
                priority_changed=False,
                comment=Observation_Log_Comment.COMMENT_NOT_FOUND_IN_LATEST_SCAN,
                vex_justification="",
                vex_remediations=None,
                assessment_status=Assessment_Status.ASSESSMENT_STATUS_AUTO_APPROVED,
                risk_acceptance_expiry_date=None,
                values_before=values_before,
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
