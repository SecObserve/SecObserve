import hashlib
from dataclasses import dataclass
from typing import Optional

import jsonpickle
from rest_framework.exceptions import NotFound, ValidationError

from application.access_control.services.current_user import get_current_user
from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Branch, Product
from application.vex.models import CSAF, CSAF_Branch, CSAF_Revision, CSAF_Vulnerability
from application.vex.queries.csaf import get_csaf_by_document_id
from application.vex.services.csaf_generator_component import (
    append_component_to_product_tree,
)
from application.vex.services.csaf_generator_document import create_csaf_root
from application.vex.services.csaf_generator_product import (
    append_product_to_product_tree,
)
from application.vex.services.csaf_generator_remediation import set_remediation
from application.vex.services.csaf_generator_vulnerability import (
    create_vulnerability,
    remove_conflicting_product_status,
    set_flag_or_threat,
    set_product_status,
    set_vulnerability_description,
    validate_not_affected_impact_statements,
)
from application.vex.services.vex_base import (
    check_product_or_vulnerabilities,
    check_vulnerability_names,
    create_document_base_id,
    get_observations_for_product,
    get_observations_for_vulnerability,
)
from application.vex.types import CSAFProductTree, CSAFRoot, CSAFVulnerability


@dataclass()
class CSAFCreateParameters:
    product: Optional[Product]
    vulnerability_names: list[str]
    branches: list[Branch]
    document_id_prefix: str
    title: str
    publisher_name: str
    publisher_category: str
    publisher_namespace: str
    tracking_status: str
    tlp_label: str


@dataclass()
class CSAFUpdateParameters:
    document_id_prefix: str
    document_base_id: str
    publisher_name: str
    publisher_category: str
    publisher_namespace: str
    tracking_status: str
    tlp_label: str


@dataclass()
class CSAFContent:
    vulnerabilities: list[CSAFVulnerability]
    product_tree: CSAFProductTree


def create_csaf_document(parameters: CSAFCreateParameters) -> Optional[CSAFRoot]:
    check_product_or_vulnerabilities(parameters.product, parameters.vulnerability_names)
    check_vulnerability_names(parameters.vulnerability_names)

    user = get_current_user()
    if not user:
        raise ValueError("No user in request")

    document_base_id = create_document_base_id(parameters.document_id_prefix)

    csaf = CSAF.objects.create(
        product=parameters.product,
        document_id_prefix=parameters.document_id_prefix,
        document_base_id=document_base_id,
        version=1,
        title=parameters.title,
        publisher_name=parameters.publisher_name,
        publisher_category=parameters.publisher_category,
        publisher_namespace=parameters.publisher_namespace,
        tracking_status=parameters.tracking_status,
        tlp_label=parameters.tlp_label,
        user=user,
    )
    CSAF_Revision.objects.create(
        csaf=csaf,
        date=csaf.tracking_current_release_date,
        version=1,
        summary="Initial release",
    )
    for vulnerability_name in parameters.vulnerability_names:
        if vulnerability_name is None:
            vulnerability_name = ""
        CSAF_Vulnerability.objects.create(csaf=csaf, name=vulnerability_name)

    for branch in parameters.branches:
        CSAF_Branch.objects.create(csaf=csaf, branch=branch)

    csaf_root = create_csaf_root(csaf)

    vulnerabilities = []

    if parameters.product:
        vulnerabilities, product_tree = _get_content_for_product(
            parameters.product, parameters.vulnerability_names, parameters.branches
        )
    else:
        vulnerabilities, product_tree = _get_content_for_vulnerabilities(parameters.vulnerability_names)

    if not vulnerabilities:
        csaf.delete()
        return None

    try:
        validate_not_affected_impact_statements(vulnerabilities)
    except ValidationError:
        csaf.delete()
        raise

    csaf_content = CSAFContent(vulnerabilities, product_tree)
    content_json = jsonpickle.encode(csaf_content, unpicklable=False)
    content_hash = hashlib.sha256(content_json.casefold().encode("utf-8").strip()).hexdigest()
    csaf.content_hash = content_hash
    csaf.save()

    csaf_root.product_tree = product_tree
    csaf_root.vulnerabilities = vulnerabilities

    return csaf_root


def update_csaf_document(parameters: CSAFUpdateParameters) -> Optional[CSAFRoot]:
    csaf = get_csaf_by_document_id(parameters.document_id_prefix, parameters.document_base_id)
    if not csaf:
        raise NotFound(
            f"CSAF document with ids {parameters.document_id_prefix} and {parameters.document_base_id} does not exist"
        )

    user_has_permission_or_403(csaf, Permissions.VEX_Edit)

    csaf_vulnerability_names = list(CSAF_Vulnerability.objects.filter(csaf=csaf).values_list("name", flat=True))

    csaf_branch_ids = CSAF_Branch.objects.filter(csaf=csaf).values_list("branch", flat=True)
    csaf_branches = list(Branch.objects.filter(id__in=csaf_branch_ids))

    vulnerabilities = []

    if csaf.product:
        vulnerabilities, product_tree = _get_content_for_product(csaf.product, csaf_vulnerability_names, csaf_branches)
    else:
        vulnerabilities, product_tree = _get_content_for_vulnerabilities(csaf_vulnerability_names)

    validate_not_affected_impact_statements(vulnerabilities)

    csaf_content = CSAFContent(vulnerabilities, product_tree)
    content_json = jsonpickle.encode(csaf_content, unpicklable=False)
    content_hash = hashlib.sha256(content_json.casefold().encode("utf-8").strip()).hexdigest()

    if content_hash == csaf.content_hash:
        return None

    if parameters.publisher_name:
        csaf.publisher_name = parameters.publisher_name
    if parameters.publisher_category:
        csaf.publisher_category = parameters.publisher_category
    if parameters.publisher_namespace:
        csaf.publisher_namespace = parameters.publisher_namespace
    if parameters.tracking_status:
        csaf.tracking_status = parameters.tracking_status
    if parameters.tlp_label:
        csaf.tlp_label = parameters.tlp_label
    csaf.version += 1
    csaf.content_hash = content_hash
    csaf.save()

    CSAF_Revision.objects.create(
        csaf=csaf,
        date=csaf.tracking_current_release_date,
        version=csaf.version,
        summary="Update",
    )

    csaf_root = create_csaf_root(csaf)

    csaf_root.product_tree = product_tree
    csaf_root.vulnerabilities = vulnerabilities

    return csaf_root


def _get_content_for_vulnerabilities(vulnerability_names: list[str]) -> tuple:
    vulnerabilities = []
    product_tree = CSAFProductTree(branches=[], relationships=[])
    for vulnerability_name in vulnerability_names:
        vulnerability = create_vulnerability(vulnerability_name)
        vulnerabilities.append(vulnerability)
        current_vulnerability_description = None

        observations = get_observations_for_vulnerability(vulnerability_name)
        for observation in observations:
            append_component_to_product_tree(product_tree, observation)
            current_vulnerability_description = set_vulnerability_description(
                vulnerability, observation, current_vulnerability_description
            )
            append_product_to_product_tree(product_tree, observation.product, observation.branch)

            set_product_status(vulnerability, observation)
            remove_conflicting_product_status(vulnerability)
            set_remediation(vulnerability, observation)
            set_flag_or_threat(vulnerability, observation)

    return vulnerabilities, product_tree


def _get_content_for_product(product: Product, vulnerability_names: list[str], branches: list[Branch]) -> tuple:
    vulnerabilities: dict[str, CSAFVulnerability] = {}
    product_tree = CSAFProductTree(branches=[], relationships=[])

    product_has_branches = False
    if branches:
        for branch in branches:
            product_has_branches = True
            append_product_to_product_tree(product_tree, product, branch)
    else:
        for branch in Branch.objects.filter(product=product):
            product_has_branches = True
            append_product_to_product_tree(product_tree, product, branch)

    if not product_has_branches:
        append_product_to_product_tree(product_tree, product, None)

    observations = get_observations_for_product(product, vulnerability_names, branches)
    for observation in observations:
        append_component_to_product_tree(product_tree, observation)
        vulnerability = vulnerabilities.get(observation.vulnerability_id)
        if not vulnerability:
            vulnerability = create_vulnerability(observation.vulnerability_id)
            vulnerabilities[observation.vulnerability_id] = vulnerability
            set_vulnerability_description(vulnerability, observation, None)

        set_product_status(vulnerability, observation)
        remove_conflicting_product_status(vulnerability)
        set_remediation(vulnerability, observation)
        set_flag_or_threat(vulnerability, observation)

    return list(vulnerabilities.values()), product_tree
