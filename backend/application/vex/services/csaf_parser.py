from dataclasses import dataclass

from rest_framework.exceptions import ValidationError

from application.core.api.serializers_helpers import validate_purl
from application.vex.models import VEX_Document, VEX_Statement
from application.vex.services.vex_engine import apply_vex_statements_after_import
from application.vex.types import CSAF_Status, VEX_Document_Type, VEX_Status


@dataclass
class Relationship:
    product_id: str = ""
    component_id: str = ""


@dataclass
class Product_Component:
    product_purl: str = ""
    component_purl: str = ""


def parse_csaf_data(data: dict) -> None:
    csaf_document = _create_csaf_document(data)

    products: dict[str, str] = {}
    product_tree: dict = data.get("product_tree", {})
    _find_products_in_branches(product_tree.get("branches", []), products)
    _find_products_in_full_product_names(product_tree.get("full_product_names", []), products)
    _find_products_in_relationships(product_tree.get("relationships", []), products)

    relationships: dict[str, Relationship] = _process_relationships(product_tree)

    product_purls, vex_statements = _process_vulnerabilities(data, csaf_document, products, relationships)

    apply_vex_statements_after_import(product_purls, vex_statements)


def _create_csaf_document(data: dict) -> VEX_Document:
    namespace = data.get("document", {}).get("publisher", {}).get("namespace")
    if not namespace:
        raise ValidationError("document/publisher/namespace is missing")
    tracking_id = data.get("document", {}).get("tracking", {}).get("id")
    if not tracking_id:
        raise ValidationError("document/tracking/id is missing")
    document_id = f"{namespace}/{tracking_id}"
    version = data.get("document", {}).get("tracking", {}).get("version")
    if not version:
        raise ValidationError("document/tracking/version is missing")
    initial_release_date = data.get("document", {}).get("tracking", {}).get("initial_release_date")
    if not initial_release_date:
        raise ValidationError("document/tracking/initial_release_date is missing")
    current_release_date = data.get("document", {}).get("tracking", {}).get("current_release_date")
    if not current_release_date:
        current_release_date = initial_release_date
    author = data.get("document", {}).get("publisher", {}).get("name")
    if not author:
        raise ValidationError("author is missing")
    role = data.get("document", {}).get("publisher", {}).get("category")

    try:
        csaf_document = VEX_Document.objects.get(document_id=document_id, author=author)
        csaf_document.delete()
    except VEX_Document.DoesNotExist:
        pass
    csaf_document = VEX_Document.objects.create(
        type=VEX_Document_Type.VEX_DOCUMENT_TYPE_CSAF,
        document_id=document_id,
        version=version,
        initial_release_date=initial_release_date,
        current_release_date=current_release_date,
        author=author,
        role=role,
    )

    return csaf_document


def _find_products_in_branches(branches: list, products: dict[str, str]) -> None:
    for branch in branches:
        branches = branch.get("branches")
        if branches:
            _find_products_in_branches(branches, products)
        product = branch.get("product")
        if product:
            _process_product(product, products)


def _find_products_in_full_product_names(full_product_names: list, products: dict[str, str]) -> None:
    for product in full_product_names:
        _process_product(product, products)


def _find_products_in_relationships(relationships: list, products: dict[str, str]) -> None:
    for relationship in relationships:
        full_product_name = relationship.get("full_product_name")
        if full_product_name:
            _process_product(full_product_name, products)


def _process_product(product: dict, products: dict[str, str]) -> None:
    product_id = product.get("product_id")
    purl = product.get("product_identification_helper", {}).get("purl")
    if product_id and purl:
        validate_purl(purl)
        products[product_id] = purl


def _process_relationships(product_tree: dict) -> dict[str, Relationship]:
    relationships: dict[str, Relationship] = {}

    relationship_data = product_tree.get("relationships", [])
    for relationship in relationship_data:
        category = relationship.get("category")
        if category not in [
            "default_component_of",
            "external_component_of",
            "optional_component_of",
        ]:
            continue
        relationship_id = relationship.get("full_product_name", {}).get("product_id")
        product_id = relationship.get("relates_to_product_reference")
        component_id = relationship.get("product_reference")
        if relationship_id and component_id and product_id:
            relationships[relationship_id] = Relationship(component_id=component_id, product_id=product_id)

    return relationships


def _process_vulnerabilities(
    data: dict,
    csaf_document: VEX_Document,
    products: dict[str, str],
    relationships: dict[str, Relationship],
) -> tuple[set[str], set[VEX_Statement]]:
    vulnerabilities = data.get("vulnerabilities", [])
    if not vulnerabilities:
        raise ValidationError("CSAF document doesn't contain any vulnerabilities")
    if not isinstance(vulnerabilities, list):
        raise ValidationError("vulnerabilities is not a list")

    product_purls: set[str] = set()
    vex_statements: set[VEX_Statement] = set()

    for vulnerability in vulnerabilities:
        vulnerability_id = vulnerability.get("cve")
        if not vulnerability_id:
            vulnerability_id_data = vulnerability.get("ids")
            if not vulnerability_id_data:
                raise ValidationError("Vulnerability ID is missing")
            vulnerability_id = vulnerability_id_data[0].get("text")
            if not vulnerability_id:
                raise ValidationError("Vulnerability ID is missing")

        product_status = vulnerability.get("product_status")
        if not product_status:
            raise ValidationError("product_status is missing")

        known_affected = product_status.get(CSAF_Status.CSAF_STATUS_AFFECTED, [])
        for product_id in known_affected:
            product_component = _get_product_component(product_id, products, relationships)
            vex_statement = VEX_Statement(
                document=csaf_document,
                vulnerability_id=vulnerability_id,
                description=_get_description(vulnerability),
                status=VEX_Status.VEX_STATUS_AFFECTED,
                remediation=_get_remediation(vulnerability, product_id),
                product_purl=product_component.product_purl,
                component_purl=product_component.component_purl,
            )
            vex_statement.save()
            vex_statements.add(vex_statement)
            product_purls.add(product_component.product_purl)

        known_not_affected = product_status.get(CSAF_Status.CSAF_STATUS_NOT_AFFECTED, [])
        for product_id in known_not_affected:
            product_component = _get_product_component(product_id, products, relationships)
            vex_statement = VEX_Statement(
                document=csaf_document,
                vulnerability_id=vulnerability_id,
                description=_get_description(vulnerability),
                status=VEX_Status.VEX_STATUS_NOT_AFFECTED,
                justification=_get_justification(vulnerability, product_id),
                impact=_get_impact(vulnerability, product_id),
                product_purl=product_component.product_purl,
                component_purl=product_component.component_purl,
            )
            vex_statement.save()
            vex_statements.add(vex_statement)
            product_purls.add(product_component.product_purl)

        under_investigation = product_status.get(CSAF_Status.CSAF_STATUS_UNDER_INVESTIGATION, [])
        for product_id in under_investigation:
            product_component = _get_product_component(product_id, products, relationships)
            vex_statement = VEX_Statement(
                document=csaf_document,
                vulnerability_id=vulnerability_id,
                description=_get_description(vulnerability),
                status=VEX_Status.VEX_STATUS_UNDER_INVESTIGATION,
                product_purl=product_component.product_purl,
                component_purl=product_component.component_purl,
            )
            vex_statement.save()
            vex_statements.add(vex_statement)
            product_purls.add(product_component.product_purl)

        fixed = product_status.get(CSAF_Status.CSAF_STATUS_FIXED, [])
        for product_id in fixed:
            product_component = _get_product_component(product_id, products, relationships)
            vex_statement = VEX_Statement(
                document=csaf_document,
                vulnerability_id=vulnerability_id,
                description=_get_description(vulnerability),
                status=VEX_Status.VEX_STATUS_FIXED,
                product_purl=product_component.product_purl,
                component_purl=product_component.component_purl,
            )
            vex_statement.save()
            vex_statements.add(vex_statement)
            product_purls.add(product_component.product_purl)

    return product_purls, vex_statements


def _get_product_component(
    product_id: str, products: dict[str, str], relationships: dict[str, Relationship]
) -> Product_Component:
    if product_id in products:
        return Product_Component(product_purl=products[product_id])
    if product_id in relationships:
        relationship = relationships[product_id]
        product_purl = products.get(relationship.product_id)
        component_purl = products.get(relationship.component_id)
        if product_purl and component_purl:
            return Product_Component(product_purl=product_purl, component_purl=component_purl)

    raise ValidationError(f"Product or relationship data not found for {product_id}")


def _get_description(vulnerability: dict) -> str:
    notes = vulnerability.get("notes", [])
    for note in notes:
        if note.get("category") == "description":
            return note.get("text", "")

    return ""


def _get_remediation(vulnerability: dict, product_id: str) -> str:
    remediations = vulnerability.get("remediations", [])
    for remediation in remediations:
        if remediation.get("category") == "mitigation":
            product_ids = remediation.get("product_ids", [])
            if product_id in product_ids:
                return remediation.get("details", "")

    return ""


def _get_justification(vulnerability: dict, product_id: str) -> str:
    flags = vulnerability.get("flags", [])
    for flag in flags:
        product_ids = flag.get("product_ids", [])
        if product_id in product_ids:
            return flag.get("label", "")

    return ""


def _get_impact(vulnerability: dict, product_id: str) -> str:
    threats = vulnerability.get("threats", [])
    for threat in threats:
        if threat.get("category") == "impact":
            product_ids = threat.get("product_ids", [])
            if product_id in product_ids:
                return threat.get("details", "")

    return ""
