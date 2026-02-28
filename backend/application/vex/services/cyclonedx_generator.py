import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from cyclonedx.model.bom import Bom, Property
from cyclonedx.model.bom_ref import BomRef
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model.contact import OrganizationalContact, OrganizationalEntity
from cyclonedx.model.impact_analysis import (
    ImpactAnalysisJustification,
    ImpactAnalysisState,
)
from cyclonedx.model.vulnerability import (
    BomTarget,
    Vulnerability,
    VulnerabilityAnalysis,
)
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from application.__init__ import __version__
from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Branch, Product
from application.core.queries.observation import get_current_modifying_observation_log
from application.core.types import Status, VEX_Justification
from application.vex.models import (
    CycloneDX,
    CycloneDX_Branch,
    CycloneDX_Vulnerability,
)
from application.vex.queries.cyclonedx import get_cyclonedx_by_document_id
from application.vex.services.vex_base import (
    check_product_or_vulnerabilities,
    check_vulnerability_names,
    get_observations_for_product,
    get_observations_for_vulnerabilities,
)


@dataclass()
class CycloneDXCreateParameters:
    product: Optional[Product]
    vulnerability_names: list[str]
    branches: list[Branch]
    document_id_prefix: str
    author: str
    manufacturer: str


@dataclass()
class CycloneDXUpdateParameters:
    document_id_prefix: str
    document_base_id: str
    author: str
    manufacturer: str


def create_cyclonedx_document(
    parameters: CycloneDXCreateParameters,
) -> Optional[Bom]:
    check_product_or_vulnerabilities(parameters.product, parameters.vulnerability_names)
    check_vulnerability_names(parameters.vulnerability_names)

    user = get_current_user()
    if not user:
        raise ValueError("No user in request")

    bom = Bom()
    bom.version = 1

    now = timezone.now()

    cyclonedx = CycloneDX.objects.create(
        product=parameters.product,
        document_id_prefix=parameters.document_id_prefix,
        document_base_id=str(bom.serial_number),
        author=parameters.author,
        manufacturer=parameters.manufacturer,
        version=1,
        user=user,
        first_issued=now,
        last_updated=now,
    )
    for vulnerability_name in parameters.vulnerability_names:
        if vulnerability_name is None:
            vulnerability_name = ""
        CycloneDX_Vulnerability.objects.create(cyclonedx=cyclonedx, name=vulnerability_name)

    for branch in parameters.branches:
        CycloneDX_Branch.objects.create(cyclonedx=cyclonedx, branch=branch)

    _add_metadata(bom, now, parameters.document_id_prefix, parameters.author, parameters.manufacturer)

    vulnerabilities = _create_vulnerabilities(
        parameters.product, parameters.branches, parameters.vulnerability_names, cyclonedx
    )
    bom.vulnerabilities = set(vulnerabilities)

    if not vulnerabilities:
        cyclonedx.delete()
        return None

    vulnerabilities_string = _get_vulnerabilities_string(vulnerabilities)
    cyclonedx.content_hash = hashlib.sha256(vulnerabilities_string.casefold().encode("utf-8").strip()).hexdigest()
    cyclonedx.save()

    return bom


def update_cyclonedx_document(
    parameters: CycloneDXUpdateParameters,
) -> Optional[Bom]:
    cyclonedx = get_cyclonedx_by_document_id(parameters.document_id_prefix, parameters.document_base_id)
    if not cyclonedx:
        raise NotFound(
            f"CycloneDX document with ids {parameters.document_id_prefix}"
            + f" and {parameters.document_base_id} does not exist"
        )

    user_has_permission_or_403(cyclonedx, Permissions.VEX_Edit)

    cyclonedx_branch_ids = CycloneDX_Branch.objects.filter(cyclonedx=cyclonedx).values_list("branch", flat=True)
    cyclonedx_branches = list(Branch.objects.filter(id__in=cyclonedx_branch_ids))

    cyclonedx_vulnerability_names = list(
        CycloneDX_Vulnerability.objects.filter(cyclonedx=cyclonedx).values_list("name", flat=True)
    )

    vulnerabilities = _create_vulnerabilities(
        cyclonedx.product, cyclonedx_branches, cyclonedx_vulnerability_names, cyclonedx
    )

    vulnerabilities_string = _get_vulnerabilities_string(vulnerabilities)
    vulnerabilities_hash = hashlib.sha256(vulnerabilities_string.casefold().encode("utf-8").strip()).hexdigest()
    if vulnerabilities_hash == cyclonedx.content_hash:
        return None

    now = timezone.now()

    bom = Bom()
    bom.version = cyclonedx.version + 1
    bom.serial_number = UUID(cyclonedx.document_base_id)
    _add_metadata(bom, now, cyclonedx.document_id_prefix, parameters.author, parameters.manufacturer)
    bom.vulnerabilities = set(vulnerabilities)

    for vulnerability in bom.vulnerabilities:
        if vulnerability.analysis:
            vulnerability.analysis.last_updated = now

    cyclonedx.author = parameters.author if parameters.author else ""
    cyclonedx.manufacturer = parameters.manufacturer if parameters.manufacturer else ""
    cyclonedx.version += 1
    cyclonedx.content_hash = vulnerabilities_hash
    cyclonedx.last_updated = now
    cyclonedx.save()

    return bom


def _add_metadata(bom: Bom, timestamp: datetime, document_id_prefix: str, author: str, manufacturer: str) -> None:
    bom.metadata.tools.components.add(Component(name=f"SecObserve / {__version__}", type=ComponentType.APPLICATION))
    bom.metadata.timestamp = timestamp
    bom.metadata.properties.add(Property(name="prefix", value=document_id_prefix))
    if author:
        bom.metadata.authors.add(OrganizationalContact(name=author))
    if manufacturer:
        bom.metadata.manufacturer = OrganizationalEntity(name=manufacturer)


def _create_vulnerabilities(
    product: Optional[Product], branches: list[Branch], vulnerability_names: list[str], cyclonedx: CycloneDX
) -> list[Vulnerability]:
    vulnerabilities: dict[str, Vulnerability] = {}
    if product:
        observations = get_observations_for_product(product, vulnerability_names, branches)
    else:
        observations = get_observations_for_vulnerabilities(vulnerability_names=vulnerability_names)
    for observation in observations:
        if not observation.origin_component_cyclonedx_bom_link:
            raise ValidationError(f"Observation {observation.title} doesn't have a BOM-link")

        state = _map_current_status_to_cyclonedx_state(observation.current_status)
        if not state:
            continue

        justification = None
        detail = None
        observation_log = get_current_modifying_observation_log(observation)
        if observation_log:
            justification = _map_vex_justification_to_cyclonedx_justification(observation_log.vex_justification)
            detail = observation_log.comment

        analysis = VulnerabilityAnalysis(
            state=state,
            justification=justification,
            detail=detail,
            first_issued=cyclonedx.first_issued,
            last_updated=cyclonedx.last_updated,
        )

        analysis_hash = hashlib.sha256(
            f"{str(vars(analysis))}_{observation.description}_{observation.recommendation}".casefold()
            .encode("utf-8")
            .strip()
        ).hexdigest()

        vulnerability = vulnerabilities.get(f"{observation.vulnerability_id}_{analysis_hash}")
        if not vulnerability:
            vulnerability = Vulnerability(
                bom_ref=BomRef(
                    value=str(
                        hashlib.sha256(
                            f"{observation.pk}_{observation.title}".casefold().encode("utf-8").strip()
                        ).hexdigest()
                    )
                ),
                id=observation.vulnerability_id,
                description=observation.description if observation.description else None,
                recommendation=(
                    observation.recommendation
                    if observation.recommendation
                    and analysis.state in [ImpactAnalysisState.EXPLOITABLE, ImpactAnalysisState.IN_TRIAGE]
                    else None
                ),
                analysis=analysis,
            )
            vulnerabilities[f"{observation.vulnerability_id}_{analysis_hash}"] = vulnerability

        vulnerability.affects.add(BomTarget(ref=observation.origin_component_cyclonedx_bom_link))

    return sorted(vulnerabilities.values())


def _get_vulnerabilities_string(vulnerabilities: list[Vulnerability]) -> str:
    vulnerability_string = ""
    for vulnerability in vulnerabilities:
        vulnerability_string += str(vulnerability.id)
        vulnerability_string += vulnerability.description if vulnerability.description else ""
        vulnerability_string += vulnerability.recommendation if vulnerability.recommendation else ""
        vulnerability_string += str(vars(vulnerability.analysis))
        for affects in vulnerability.affects:
            vulnerability_string += str(vars(affects))

    return vulnerability_string


def _map_current_status_to_cyclonedx_state(current_status: str) -> Optional[ImpactAnalysisState]:
    mapping = {
        Status.STATUS_OPEN: ImpactAnalysisState.EXPLOITABLE,
        Status.STATUS_AFFECTED: ImpactAnalysisState.EXPLOITABLE,
        Status.STATUS_RESOLVED: ImpactAnalysisState.RESOLVED,
        Status.STATUS_DUPLICATE: None,
        Status.STATUS_FALSE_POSITIVE: ImpactAnalysisState.FALSE_POSITIVE,
        Status.STATUS_IN_REVIEW: ImpactAnalysisState.IN_TRIAGE,
        Status.STATUS_NOT_AFFECTED: ImpactAnalysisState.NOT_AFFECTED,
        Status.STATUS_NOT_SECURITY: ImpactAnalysisState.NOT_AFFECTED,
        Status.STATUS_RISK_ACCEPTED: ImpactAnalysisState.EXPLOITABLE,
    }
    return mapping.get(current_status)


def _map_vex_justification_to_cyclonedx_justification(justification: str) -> Optional[ImpactAnalysisJustification]:
    mapping = {
        VEX_Justification.JUSTIFICATION_COMPONENT_NOT_PRESENT: ImpactAnalysisJustification.REQUIRES_DEPENDENCY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_PRESENT: ImpactAnalysisJustification.CODE_NOT_PRESENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_NOT_IN_EXECUTE_PATH: ImpactAnalysisJustification.CODE_NOT_REACHABLE,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_VULNERABLE_CODE_CANNOT_BE_CONTROLLED_BY_ADVERSARY: ImpactAnalysisJustification.PROTECTED_BY_MITIGATING_CONTROL,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_INLINE_MITIGATIONS_ALREADY_EXIST: ImpactAnalysisJustification.PROTECTED_BY_MITIGATING_CONTROL,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_CODE_NOT_PRESENT: ImpactAnalysisJustification.CODE_NOT_PRESENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_CODE_NOT_REACHABLE: ImpactAnalysisJustification.CODE_NOT_REACHABLE,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_CONFIGURATION: ImpactAnalysisJustification.REQUIRES_CONFIGURATION,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_DEPENDENCY: ImpactAnalysisJustification.REQUIRES_DEPENDENCY,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_REQUIRES_ENVIRONMENT: ImpactAnalysisJustification.REQUIRES_ENVIRONMENT,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_BY_COMPILER: ImpactAnalysisJustification.PROTECTED_BY_COMPILER,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_AT_RUNTIME: ImpactAnalysisJustification.PROTECTED_AT_RUNTIME,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_AT_PERIMETER: ImpactAnalysisJustification.PROTECTED_AT_PERIMITER,  # noqa: E501 pylint: disable=line-too-long
        VEX_Justification.JUSTIFICATION_CYCLONEDX_PROTECTED_BY_MITIGATING_CONTROL: ImpactAnalysisJustification.PROTECTED_BY_MITIGATING_CONTROL,  # noqa: E501 pylint: disable=line-too-long
    }
    return mapping.get(justification)
