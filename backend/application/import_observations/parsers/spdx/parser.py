from json import dumps
from typing import Any, Optional

from rest_framework.exceptions import ValidationError
from spdx_tools.spdx.model import Document, RelationshipType, SpdxNoAssertion, SpdxNone
from spdx_tools.spdx.parser.error import SPDXParsingError
from spdx_tools.spdx.parser.jsonlikedict.json_like_dict_parser import JsonLikeDictParser

from application.core.models import Branch, Observation, Product
from application.import_observations.parsers.base_parser import (
    BaseFileParser,
    BaseParser,
)
from application.import_observations.types import Parser_Filetype, Parser_Type
from application.licenses.models import License_Component


class SPDXParser(BaseParser, BaseFileParser):
    @classmethod
    def get_name(cls) -> str:
        return "SPDX"

    @classmethod
    def get_filetype(cls) -> str:
        return Parser_Filetype.FILETYPE_JSON

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_SCA

    @classmethod
    def sbom(cls) -> bool:
        return True

    def check_format(self, data: Any) -> bool:
        if isinstance(data, dict) and data.get("SPDXID") and (data.get("SPDXVersion") or data.get("spdxVersion")):
            return True
        return False

    def get_observations(self, data: dict, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        return [], ""

    def get_license_components(self, data: dict) -> tuple[list[License_Component], str]:
        try:
            document: Document = JsonLikeDictParser().parse(data)
        except SPDXParsingError as e:
            raise ValidationError(e.get_messages())  # pylint: disable=raise-missing-from
            # The ValidationError itself is not relevant and must not be re-raised

        scanner = self._get_scanner(data)

        observations = []

        packages = self._create_package_dict(data)
        relationships = self._create_relationship_dict(document, packages)

        for package in document.packages:  # pylint: disable=not-an-iterable
            # I don't know why pylint is complaining about this, Document.packages is a list
            version = ""
            if package.version is not None:
                version = str(package.version)

            concluded_licenses: list[str] = []
            if (
                package.license_concluded is not None
                and not isinstance(package.license_concluded, SpdxNoAssertion)
                and not isinstance(package.license_concluded, SpdxNone)
            ):
                concluded_licenses.append(str(package.license_concluded))

            declared_licenses: list[str] = []
            if (
                package.license_declared is not None
                and not isinstance(package.license_declared, SpdxNoAssertion)
                and not isinstance(package.license_declared, SpdxNone)
            ):
                declared_licenses.append(str(package.license_declared))

            purl = ""
            for external_reference in package.external_references:
                if external_reference.reference_type == "purl":
                    purl = external_reference.locator
                    break

            dependencies = self._get_dependencies(package.spdx_id, packages, relationships)

            license_component = License_Component(
                component_name=package.name,
                component_version=version,
                component_purl=purl,
                component_dependencies=dependencies,
            )

            license_component.unsaved_declared_licenses = declared_licenses
            license_component.unsaved_concluded_licenses = concluded_licenses

            evidence = []
            package_json = packages.get(package.spdx_id)
            if package_json:
                evidence.append("Package")
                evidence.append(dumps(package_json))
                license_component.unsaved_evidences.append(evidence)

            observations.append(license_component)

        return observations, scanner

    def _get_scanner(self, data: dict) -> str:
        scanner = ""

        creators = data.get("creationInfo", {}).get("creators", [])
        for creator in creators:
            creator_elements = creator.split(":")
            if len(creator_elements) == 2 and creator_elements[0].strip() == "Tool":
                scanner = creator_elements[1].strip()
                break

        return scanner

    def _create_package_dict(self, data: dict) -> dict[str, dict]:
        package_dict = {}
        for package in data["packages"]:
            package_dict[package["SPDXID"]] = package
        return package_dict

    def _create_relationship_dict(self, document: Document, package_dict: dict[str, dict]) -> dict[str, list[str]]:
        relationship_dict: dict[str, list[str]] = {}
        for relationship in document.relationships:
            if (
                relationship.spdx_element_id in package_dict.keys()
                and relationship.related_spdx_element_id in package_dict.keys()
                and (relationship.relationship_type in (RelationshipType.DEPENDS_ON, RelationshipType.CONTAINS))
            ):
                relationship_value = relationship_dict.get(str(relationship.related_spdx_element_id), [])
                relationship_value.append(relationship.spdx_element_id)
                relationship_dict[str(relationship.related_spdx_element_id)] = relationship_value
        return relationship_dict

    def _get_dependencies(self, package_id: str, package_dict: dict, relationship_dict: dict) -> str:
        dependencies: set[str] = set()
        self._get_dependencies_recursive(package_id, package_dict, relationship_dict, dependencies)

        return "\n".join(sorted(dependencies))

    def _get_dependencies_recursive(
        self,
        package_id: str,
        package_dict: dict,
        relationship_dict: dict,
        dependencies: set[str],
    ) -> None:
        if package_id in relationship_dict.keys():
            for dependency_id in relationship_dict[package_id]:
                translated_dependency_id = self._translate_package_id(dependency_id, package_dict)
                translated_package_id = self._translate_package_id(package_id, package_dict)
                dependency = f"{translated_dependency_id} --> {translated_package_id}"
                if dependency not in dependencies:
                    dependencies.add(dependency)
                    self._get_dependencies_recursive(dependency_id, package_dict, relationship_dict, dependencies)

    def _translate_package_id(self, package_id: str, package_dict: dict) -> str:
        package = package_dict.get(package_id)
        if not package:
            return ""

        if package.get("versionInfo"):
            return f"{package.get('name', '')}:{package.get('versionInfo', '')}"

        return package.get("name", "")
