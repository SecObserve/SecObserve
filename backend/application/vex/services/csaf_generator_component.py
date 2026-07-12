from typing import Optional

from packageurl import PackageURL

from application.core.models import Observation
from application.vex.services.csaf_generator_helpers import (
    get_component_id,
    get_product_id,
    get_relationship_name,
)
from application.vex.types import (
    CSAF_Branch_Category,
    CSAF_Relationship_Category,
    CSAFFullProductName,
    CSAFProductBranch,
    CSAFProductIdentificationHelper,
    CSAFProductRelationship,
    CSAFProductTree,
)


def append_component_to_product_tree(
    product_tree: CSAFProductTree,
    observation: Observation,
) -> None:
    if not observation.origin_component_name_version:
        return

    purl = None
    vendor_branch_name = "unknown"
    if observation.origin_component_purl:
        try:
            purl = PackageURL.from_string(observation.origin_component_purl)
            if purl.namespace:
                vendor_branch_name = purl.namespace
        except ValueError:
            pass

    found = False
    for vendor_branch in product_tree.branches:
        if vendor_branch.name == vendor_branch_name:
            found = True
            break
    if not found:
        vendor_branch = CSAFProductBranch(
            name=vendor_branch_name,
            category=CSAF_Branch_Category.CSAF_BRANCH_CATEGORY_VENDOR,
            branches=[],
        )
        product_tree.branches.append(vendor_branch)

    _append_component_to_relationships(product_tree, observation)

    product_branch_name = purl.name if purl and purl.name else observation.origin_component_name
    found = False

    vendor_branch.branches = vendor_branch.branches or []
    for product_branch in vendor_branch.branches:
        if product_branch.name == product_branch_name:
            found = True
            break
    if not found:
        product_branch = CSAFProductBranch(
            name=product_branch_name,
            category=CSAF_Branch_Category.CSAF_BRANCH_CATEGORY_PRODUCT_NAME,
            branches=[],
        )
        vendor_branch.branches.append(product_branch)

    product_branch.branches = product_branch.branches or []
    for component_branch in product_branch.branches:
        if component_branch.product and component_branch.product.product_id == get_component_id(
            observation.origin_component_name_version,
            observation.origin_component_purl,
            observation.origin_component_cpe,
        ):
            return

    component_branch = CSAFProductBranch(
        name=(_get_version(observation, purl)),
        category=CSAF_Branch_Category.CSAF_BRANCH_CATEGORY_PRODUCT_VERSION,
        product=_create_component(
            observation.origin_component_name_version,
            observation.origin_component_purl,
            observation.origin_component_cpe,
        ),
    )
    product_branch.branches.append(component_branch)


def _create_component(component_name_version: str, purl: Optional[str], cpe: Optional[str]) -> CSAFFullProductName:
    product_identification_helper = None
    if purl or cpe:
        purl = purl if purl else None
        cpe = cpe if cpe else None
        product_identification_helper = CSAFProductIdentificationHelper(purl=purl, cpe=cpe)

    component_id = get_component_id(component_name_version, purl, cpe)
    full_product_name = CSAFFullProductName(
        name=component_name_version,
        product_id=component_id,
        product_identification_helper=product_identification_helper,
    )

    return full_product_name


def _append_component_to_relationships(product_tree: CSAFProductTree, observation: Observation) -> None:
    if not observation.origin_component_name_version:
        return

    component_id = get_component_id(
        observation.origin_component_name_version,
        observation.origin_component_purl,
        observation.origin_component_cpe,
    )
    product_id = get_product_id(observation.product, observation.branch)

    for relationship in product_tree.relationships:
        if relationship.product_reference == component_id and relationship.relates_to_product_reference == product_id:
            return

    full_product_name = CSAFFullProductName(
        name=get_relationship_name(observation),
        product_id=get_relationship_name(observation),
    )

    relationship = CSAFProductRelationship(
        category=CSAF_Relationship_Category.CSAF_RELATIONSHIP_CATEGORY_DEFAULT_COMPONENT,
        product_reference=component_id,
        relates_to_product_reference=product_id,
        full_product_name=full_product_name,
    )
    product_tree.relationships.append(relationship)


def _get_version(observation: Observation, purl: Optional[PackageURL]) -> str:
    if purl and purl.version:
        return purl.version
    if observation.origin_component_version:
        return observation.origin_component_version
    return "unknown"
