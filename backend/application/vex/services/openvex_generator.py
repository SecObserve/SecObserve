import hashlib
from dataclasses import dataclass
from typing import Optional

import jsonpickle
from rest_framework.exceptions import NotFound

from application.__init__ import __version__
from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Branch, Observation, Product
from application.core.queries.observation import get_current_modifying_observation_log
from application.core.types import Status
from application.vex.models import OpenVEX, OpenVEX_Branch, OpenVEX_Vulnerability
from application.vex.queries.openvex import get_openvex_by_document_id
from application.vex.services.openvex_generator_helpers import OpenVEXVulnerabilityCache
from application.vex.services.vex_base import (
    check_product_or_vulnerabilities,
    check_vulnerability_names,
    create_document_base_id,
    get_component_id,
    get_observations_for_product,
    get_observations_for_vulnerability,
    get_product_id,
    get_vulnerability_url,
    map_vex_justification_to_csaf_openvex_justification,
)
from application.vex.types import (
    OpenVEX_Status,
    OpenVEXDocument,
    OpenVEXProduct,
    OpenVEXProductIdentifiers,
    OpenVEXStatement,
    OpenVEXSubcomponent,
    OpenVEXVulnerability,
)


@dataclass()
class OpenVEXCreateParameters:
    product: Optional[Product]
    vulnerability_names: list[str]
    branches: list[Branch]
    id_namespace: str
    document_id_prefix: str
    author: str
    role: str


@dataclass()
class OpenVEXUpdateParameters:
    document_id_prefix: str
    document_base_id: str
    author: str
    role: str


def create_openvex_document(
    parameters: OpenVEXCreateParameters,
) -> Optional[OpenVEXDocument]:
    check_product_or_vulnerabilities(parameters.product, parameters.vulnerability_names)
    check_vulnerability_names(parameters.vulnerability_names)

    user = get_current_user()
    if not user:
        raise ValueError("No user in request")

    document_base_id = create_document_base_id(parameters.document_id_prefix)

    openvex = OpenVEX.objects.create(
        product=parameters.product,
        id_namespace=parameters.id_namespace,
        document_id_prefix=parameters.document_id_prefix,
        document_base_id=document_base_id,
        author=parameters.author,
        role=parameters.role,
        version=1,
        user=user,
    )
    for vulnerability_name in parameters.vulnerability_names:
        if vulnerability_name is None:
            vulnerability_name = ""
        OpenVEX_Vulnerability.objects.create(openvex=openvex, name=vulnerability_name)

    for branch in parameters.branches:
        OpenVEX_Branch.objects.create(openvex=openvex, branch=branch)

    document_id = _get_document_id(parameters.id_namespace, parameters.document_id_prefix, document_base_id)
    openvex_document = OpenVEXDocument(
        context="https://openvex.dev/ns/v0.2.0",
        id=document_id,
        version=openvex.version,
        author=openvex.author,
        role=openvex.role,
        timestamp=openvex.timestamp.isoformat(),
        last_updated=openvex.last_updated.isoformat(),
        tooling="SecObserve / " + __version__,
        statements=[],
    )

    statements = []
    if parameters.product:
        statements = _get_statements_for_product(
            parameters.product, parameters.vulnerability_names, parameters.branches
        )
    else:
        statements = _get_statements_for_vulnerabilities(parameters.vulnerability_names)

    if not statements:
        openvex.delete()
        return None

    statements_json = jsonpickle.encode(statements, unpicklable=False)
    statements_hash = hashlib.sha256(statements_json.casefold().encode("utf-8").strip()).hexdigest()
    openvex.content_hash = statements_hash
    openvex.save()

    for statement in statements:
        openvex_document.statements.append(statement)

    return openvex_document


def update_openvex_document(
    parameters: OpenVEXUpdateParameters,
) -> Optional[OpenVEXDocument]:
    openvex = get_openvex_by_document_id(parameters.document_id_prefix, parameters.document_base_id)
    if not openvex:
        raise NotFound(
            f"OpenVEX document with ids {parameters.document_id_prefix}"
            + f" and {parameters.document_base_id} does not exist"
        )

    user_has_permission_or_403(openvex, Permissions.VEX_Edit)

    openvex_vulnerability_names = list(
        OpenVEX_Vulnerability.objects.filter(openvex=openvex).values_list("name", flat=True)
    )

    openvex_branch_ids = OpenVEX_Branch.objects.filter(openvex=openvex).values_list("branch", flat=True)
    openvex_branches = list(Branch.objects.filter(id__in=openvex_branch_ids))

    statements = []
    if openvex.product:
        statements = _get_statements_for_product(openvex.product, openvex_vulnerability_names, openvex_branches)
    else:
        statements = _get_statements_for_vulnerabilities(openvex_vulnerability_names)

    statements_json = jsonpickle.encode(statements, unpicklable=False)
    statements_hash = hashlib.sha256(statements_json.casefold().encode("utf-8").strip()).hexdigest()

    if statements_hash == openvex.content_hash:
        return None

    if parameters.author:
        openvex.author = parameters.author
    if parameters.role:
        openvex.role = parameters.role
    openvex.version += 1
    openvex.content_hash = statements_hash
    openvex.save()

    document_id = _get_document_id(openvex.id_namespace, openvex.document_id_prefix, parameters.document_base_id)
    openvex_document = OpenVEXDocument(
        context="https://openvex.dev/ns/v0.2.0",
        id=document_id,
        version=openvex.version,
        author=openvex.author,
        role=openvex.role,
        timestamp=openvex.timestamp.isoformat(),
        last_updated=openvex.last_updated.isoformat(),
        tooling="SecObserve / " + __version__,
        statements=[],
    )

    for statement in statements:
        openvex_document.statements.append(statement)

    return openvex_document


def _get_document_id(id_namespace: str, document_id_prefix: str, document_base_id: str) -> str:
    if not id_namespace.endswith("/"):
        id_namespace += "/"

    return f"{id_namespace}{document_id_prefix}_{document_base_id}"


def _get_statements_for_vulnerabilities(
    vulnerability_names: list[str],
) -> list[OpenVEXStatement]:
    statements: dict[str, OpenVEXStatement] = {}

    for vulnerability_name in vulnerability_names:
        openvex_vulnerability = OpenVEXVulnerability(
            name=vulnerability_name, id=get_vulnerability_url(vulnerability_name)
        )

        observations = get_observations_for_vulnerability(vulnerability_name)
        for observation in observations:
            prepared_statement = _prepare_statement(observation)
            if not prepared_statement:
                continue

            string_to_hash = (
                str(openvex_vulnerability.name)
                + str(prepared_statement.status)
                + str(prepared_statement.justification)
                + str(prepared_statement.status_notes)
                + str(prepared_statement.action_statement)
                + str(prepared_statement.impact_statement)
            )
            hashed_string = hashlib.sha256(string_to_hash.casefold().encode("utf-8").strip()).hexdigest()

            existing_statement = statements.get(hashed_string)
            if existing_statement:
                existing_product = get_openvex_product_by_id(existing_statement.products, get_product_id(observation))
                if existing_product:
                    _add_subcomponent(observation, existing_product)
                else:
                    openvex_product = _create_product(observation)
                    existing_statement.products.append(openvex_product)
            else:
                if observation.description:
                    openvex_vulnerability.description = observation.description
                prepared_statement.vulnerability = openvex_vulnerability
                openvex_product = _create_product(observation)
                prepared_statement.products.append(openvex_product)
                statements[hashed_string] = prepared_statement

    return list(statements.values())


def _get_statements_for_product(
    product: Product, vulnerability_names: list[str], branches: list[Branch]
) -> list[OpenVEXStatement]:
    statements: dict[str, OpenVEXStatement] = {}

    vulnerability_cache = OpenVEXVulnerabilityCache()

    observations = get_observations_for_product(product, vulnerability_names, branches)
    for observation in observations:
        prepared_statement = _prepare_statement(observation)
        if not prepared_statement:
            continue

        openvex_vulnerability = vulnerability_cache.get_vulnerability(observation.vulnerability_id)
        if not openvex_vulnerability:
            openvex_vulnerability = OpenVEXVulnerability(
                name=observation.vulnerability_id,
                description=observation.description,
                id=get_vulnerability_url(observation.vulnerability_id),
            )
            vulnerability_cache.add_vulnerability(openvex_vulnerability)

        string_to_hash = (
            str(openvex_vulnerability.name)
            + str(prepared_statement.status)
            + str(prepared_statement.justification)
            + str(prepared_statement.status_notes)
            + str(prepared_statement.action_statement)
            + str(prepared_statement.impact_statement)
        )
        hashed_string = hashlib.sha256(string_to_hash.casefold().encode("utf-8").strip()).hexdigest()

        existing_statement = statements.get(hashed_string)
        if existing_statement:
            existing_product = get_openvex_product_by_id(existing_statement.products, get_product_id(observation))
            if existing_product:
                _add_subcomponent(observation, existing_product)
            else:
                raise ValueError(f"Product {product.name} not found in existing statement")
        else:
            prepared_statement.vulnerability = openvex_vulnerability
            openvex_product = _create_product(observation)
            prepared_statement.products.append(openvex_product)
            statements[hashed_string] = prepared_statement

    return list(statements.values())


def _prepare_statement(observation: Observation) -> Optional[OpenVEXStatement]:
    openvex_status = _map_status(observation.current_status)
    if not openvex_status:
        return None

    openvex_justification = None
    openvex_impact_statement = None
    openvex_action_statement = None
    openvex_status_notes = None

    if openvex_status == OpenVEX_Status.OPENVEX_STATUS_AFFECTED:
        if observation.recommendation:
            openvex_action_statement = observation.recommendation
        else:
            openvex_action_statement = "No recommendation for remediation or mitigation available"
    else:
        observation_log = get_current_modifying_observation_log(observation)
        if openvex_status == OpenVEX_Status.OPENVEX_STATUS_NOT_AFFECTED:
            if observation_log:
                if observation_log.vex_justification:
                    openvex_justification = map_vex_justification_to_csaf_openvex_justification(
                        observation_log.vex_justification
                    )
                openvex_impact_statement = observation_log.comment
            else:
                openvex_impact_statement = "No impact statement available"
        else:
            if observation_log:
                openvex_status_notes = observation_log.comment

    return OpenVEXStatement(
        status=openvex_status,
        status_notes=openvex_status_notes,
        impact_statement=openvex_impact_statement,
        justification=openvex_justification,
        action_statement=openvex_action_statement,
        vulnerability=None,
        products=[],
    )


def _map_status(secobserve_status: str) -> Optional[str]:
    if secobserve_status in (Status.STATUS_OPEN, Status.STATUS_AFFECTED, Status.STATUS_RISK_ACCEPTED):
        return OpenVEX_Status.OPENVEX_STATUS_AFFECTED

    if secobserve_status == Status.STATUS_RESOLVED:
        return OpenVEX_Status.OPENVEX_STATUS_FIXED

    if secobserve_status in (
        Status.STATUS_NOT_AFFECTED,
        Status.STATUS_NOT_SECURITY,
        Status.STATUS_FALSE_POSITIVE,
    ):
        return OpenVEX_Status.OPENVEX_STATUS_NOT_AFFECTED

    if secobserve_status == Status.STATUS_IN_REVIEW:
        return OpenVEX_Status.OPENVEX_STATUS_UNDER_INVESTIGATION

    if secobserve_status == Status.STATUS_DUPLICATE:
        return None

    raise ValueError(f"Invalid status {secobserve_status}")


def get_openvex_product_by_id(openvex_products: list[OpenVEXProduct], product_id: str) -> Optional[OpenVEXProduct]:
    for openvex_product in openvex_products:
        if openvex_product.id == product_id:
            return openvex_product
    return None


def _add_subcomponent(observation: Observation, existing_product: OpenVEXProduct) -> None:
    if get_component_id(observation):
        openvex_subcomponent = OpenVEXSubcomponent(id=get_component_id(observation))
        if openvex_subcomponent not in existing_product.subcomponents:
            existing_product.subcomponents.append(OpenVEXSubcomponent(id=get_component_id(observation)))


def _create_product(observation: Observation) -> OpenVEXProduct:
    openvex_product_identifiers = None
    if observation.branch:
        if observation.branch.purl or observation.branch.cpe23:
            purl = observation.branch.purl if observation.branch.purl else None
            cpe23 = observation.branch.cpe23 if observation.branch.cpe23 else None
            openvex_product_identifiers = OpenVEXProductIdentifiers(cpe23=cpe23, purl=purl)
    else:
        if observation.product.purl or observation.product.cpe23:
            purl = observation.product.purl if observation.product.purl else None
            cpe23 = observation.product.cpe23 if observation.product.cpe23 else None
            openvex_product_identifiers = OpenVEXProductIdentifiers(cpe23=cpe23, purl=purl)

    openvex_product = OpenVEXProduct(
        id=get_product_id(observation),
        subcomponents=[],
        identifiers=openvex_product_identifiers,
    )

    _add_subcomponent(observation, openvex_product)

    return openvex_product
