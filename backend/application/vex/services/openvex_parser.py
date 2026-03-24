from dataclasses import dataclass

from rest_framework.exceptions import ValidationError

from application.core.api.serializers_helpers import validate_purl
from application.vex.models import VEX_Document, VEX_Statement
from application.vex.services.vex_engine import apply_vex_statements_after_import
from application.vex.types import OpenVEX_Status, VEX_Document_Type, VEX_Status


@dataclass
class OpenVEX_Statement:
    vulnerability_id: str = ""
    description: str = ""
    status: str = ""
    justification: str = ""
    impact: str = ""
    remediation: str = ""


def parse_openvex_data(data: dict) -> None:
    openvex_document = _create_openvex_document(data)

    product_purls, vex_statements = _process_vex_statements(data, openvex_document)

    apply_vex_statements_after_import(product_purls, vex_statements)


def _create_openvex_document(data: dict) -> VEX_Document:
    document_id = data.get("@id")
    if not document_id:
        raise ValidationError("@id is missing")
    version = data.get("version")
    if not version:
        raise ValidationError("version is missing")
    initial_release_date = data.get("timestamp")
    if not initial_release_date:
        raise ValidationError("timestamp is missing")
    current_release_date = data.get("last_updated")
    if not current_release_date:
        current_release_date = initial_release_date
    author = data.get("author")
    if not author:
        raise ValidationError("author is missing")
    role = data.get("role", "")

    try:
        openvex_document = VEX_Document.objects.get(document_id=document_id, author=author)
        openvex_document.delete()
    except VEX_Document.DoesNotExist:
        pass
    openvex_document = VEX_Document.objects.create(
        type=VEX_Document_Type.VEX_DOCUMENT_TYPE_OPENVEX,
        document_id=document_id,
        version=version,
        initial_release_date=initial_release_date,
        current_release_date=current_release_date,
        author=author,
        role=role,
    )

    return openvex_document


def _process_vex_statements(data: dict, openvex_document: VEX_Document) -> tuple[set[str], set[VEX_Statement]]:
    statements = data.get("statements", [])
    if not statements:
        raise ValidationError("OpenVEX document doesn't contain any statements")
    if not isinstance(statements, list):
        raise ValidationError("statements is not a list")

    product_purls: set[str] = set()
    vex_statements: set[VEX_Statement] = set()

    statement_counter = 0
    for statement in statements:
        if not isinstance(statement, dict):
            raise ValidationError(f"statement[{statement_counter}] is not a dictionary")

        openvex_statement = OpenVEX_Statement()

        openvex_statement.vulnerability_id = statement.get("vulnerability", {}).get("name")
        if not openvex_statement.vulnerability_id:
            raise ValidationError(f"vulnerability[{statement_counter}]/name is missing")
        openvex_statement.description = statement.get("vulnerability", {}).get("description", "")
        openvex_statement.status = statement.get("status", "")
        if not openvex_statement.status:
            raise ValidationError(f"status[{statement_counter}] is missing")
        if (
            openvex_statement.status,
            openvex_statement.status,
        ) not in VEX_Status.VEX_STATUS_CHOICES:
            raise ValidationError(f"status[{statement_counter}] is not valid: {openvex_statement.status}")
        openvex_statement.justification = statement.get("justification", "")
        openvex_statement.impact = statement.get("impact_statement", "")
        if openvex_statement.status == OpenVEX_Status.OPENVEX_STATUS_NOT_AFFECTED and not (
            openvex_statement.justification or openvex_statement.impact
        ):
            raise ValidationError(
                f"justification or impact_statement is required for status[{statement_counter}] not affected"
            )
        openvex_statement.remediation = statement.get("action_statement", "")
        if openvex_statement.status == OpenVEX_Status.OPENVEX_STATUS_AFFECTED and not openvex_statement.remediation:
            raise ValidationError(f"action_statement is required for status[{statement_counter}] affected")

        _process_products(
            openvex_document=openvex_document,
            product_purls=product_purls,
            vex_statements=vex_statements,
            statement_counter=statement_counter,
            statement=statement,
            openvex_statement=openvex_statement,
        )

        statement_counter += 1

    return product_purls, vex_statements


def _process_products(
    *,
    openvex_document: VEX_Document,
    product_purls: set,
    vex_statements: set,
    statement_counter: int,
    statement: dict,
    openvex_statement: OpenVEX_Statement,
) -> None:
    products = statement.get("products", [])
    if not products:
        raise ValidationError(f"statement[{statement_counter}] doesn't contain any products")
    if not isinstance(products, list):
        raise ValidationError(f"products[{statement_counter}] is not a list")

    product_counter = 0
    for product in products:
        if not isinstance(product, dict):
            raise ValidationError(f"product[{statement_counter}][{product_counter}] is not a dictionary")
        product_purl = product.get("identifiers", {}).get("purl", "")
        if product_purl:
            validate_purl(product_purl)
        else:
            product_purl = product.get("@id", "")
            validate_purl(product_purl)

        components = product.get("subcomponents", [])
        if not components:
            vex_statement = VEX_Statement(
                document=openvex_document,
                vulnerability_id=openvex_statement.vulnerability_id,
                description=openvex_statement.description,
                status=openvex_statement.status,
                justification=openvex_statement.justification,
                impact=openvex_statement.impact,
                remediation=openvex_statement.remediation,
                product_purl=product_purl,
            )
            vex_statement.save()
            vex_statements.add(vex_statement)
            product_purls.add(product_purl)
        elif not isinstance(components, list):
            raise ValidationError(f"subcomponents[{statement_counter}][{product_counter}] is not a list")

        component_counter = 0
        for component in components:
            if not isinstance(component, dict):
                raise ValidationError(
                    f"subcomponent[{statement_counter}][{product_counter}][{component_counter}] is not a dictionary"
                )
            component_purl = component.get("identifiers", {}).get("purl", "")
            if component_purl:
                validate_purl(component_purl)
            else:
                component_purl = component.get("@id", "")
                validate_purl(component_purl)

            vex_statement = VEX_Statement(
                document=openvex_document,
                vulnerability_id=openvex_statement.vulnerability_id,
                description=openvex_statement.description,
                status=openvex_statement.status,
                justification=openvex_statement.justification,
                impact=openvex_statement.impact,
                remediation=openvex_statement.remediation,
                product_purl=product_purl,
                component_purl=component_purl,
            )
            vex_statement.save()
            vex_statements.add(vex_statement)
            product_purls.add(product_purl)

            component_counter += 1
        product_counter += 1
