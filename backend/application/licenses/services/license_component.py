import hashlib

from django.db.models.query import QuerySet
from license_expression import get_spdx_licensing
from packageurl import PackageURL
from rest_framework.exceptions import ValidationError

from application.commons.services.functions import get_comma_separated_as_list
from application.core.models import Product
from application.licenses.models import License_Component
from application.licenses.services.concluded_license import update_concluded_license
from application.licenses.services.license_policy import (
    apply_license_policy_to_component,
    get_license_evaluation_results_for_product,
    get_license_policy,
)
from application.licenses.services.spdx_license_cache import SPDXLicenseCache
from application.licenses.types import (
    NO_LICENSE_INFORMATION,
    License_Policy_Evaluation_Result,
)
from licenselynx.licenselynx import LicenseLynx

def get_identity_hash(license_component: License_Component) -> str:
    hash_string = _get_string_to_hash(license_component)
    return hashlib.sha256(hash_string.casefold().encode("utf-8").strip()).hexdigest()


def _get_string_to_hash(license_component: License_Component) -> str:  # pylint: disable=too-many-branches
    hash_string = license_component.component_name_version
    if license_component.component_dependencies:
        hash_string += license_component.component_dependencies
    if license_component.origin_service:
        hash_string += license_component.origin_service.name
    return hash_string


def prepare_license_component(component: License_Component, spdx_cache: SPDXLicenseCache) -> None:
    _prepare_name_version(component)

    if component.component_name_version is None:
        component.component_name_version = ""
    if component.component_name is None:
        component.component_name = ""
    if component.component_version is None:
        component.component_version = ""
    if component.component_purl is None:
        component.component_purl = ""
    if component.component_cpe is None:
        component.component_cpe = ""
    if component.component_dependencies is None:
        component.component_dependencies = ""

    if component.component_purl:
        try:
            purl = PackageURL.from_string(component.component_purl)
            component.component_purl_type = purl.type
        except ValueError:
            component.component_purl = ""
            component.component_purl_type = ""

    if component.component_purl_type is None:
        component.component_purl_type = ""

    _prepare_license(component, spdx_cache)

    if component.evaluation_result in [None, ""]:
        component.evaluation_result = License_Policy_Evaluation_Result.RESULT_UNKNOWN

    component.identity_hash = get_identity_hash(component)


def _prepare_name_version(component: License_Component) -> None:
    if not component.component_name_version:
        if component.component_name and component.component_version:
            component.component_name_version = component.component_name + ":" + component.component_version
        elif component.component_name:
            component.component_name_version = component.component_name
    else:
        component_parts = component.component_name_version.split(":")
        if len(component_parts) == 3:
            component.component_name = f"{component_parts[0]}:{component_parts[1]}"
            component.component_version = component_parts[2]
        elif len(component_parts) == 2:
            component.component_name = component_parts[0]
            component.component_version = component_parts[1]
        elif len(component_parts) == 1:
            component.component_name = component.component_name_version
            component.component_version = ""


def _prepare_license(component: License_Component, spdx_cache: SPDXLicenseCache) -> None:
    _prepare_imported_declared_license(component, spdx_cache)
    _prepare_imported_concluded_license(component, spdx_cache)
    set_effective_license(component)


def _prepare_imported_declared_license(component: License_Component, spdx_cache: SPDXLicenseCache) -> None:
    component.imported_declared_spdx_license = None
    component.imported_declared_license_expression = ""
    component.imported_declared_non_spdx_license = ""
    component.imported_declared_multiple_licenses = ""

    if not component.unsaved_declared_licenses:
        component.imported_declared_license_name = NO_LICENSE_INFORMATION
    elif len(component.unsaved_declared_licenses) == 1:
        component.imported_declared_spdx_license = spdx_cache.get(component.unsaved_declared_licenses[0])
        if component.imported_declared_spdx_license:
            component.imported_declared_license_name = component.imported_declared_spdx_license.spdx_id
        else:
            licensing = get_spdx_licensing()
            try:
                expression_info = licensing.validate(component.unsaved_declared_licenses[0], strict=True)
                if not expression_info.errors:
                    component.imported_declared_license_expression = expression_info.normalized_expression
                    component.imported_declared_license_name = component.imported_declared_license_expression
                else:
                    component.imported_declared_non_spdx_license = component.unsaved_declared_licenses[0]
                    component.imported_declared_license_name = component.imported_declared_non_spdx_license
            except Exception:
                component.imported_declared_non_spdx_license = component.unsaved_declared_licenses[0]
                component.imported_declared_license_name = component.imported_declared_non_spdx_license

        if component.imported_declared_non_spdx_license:
            _get_mapped_licence(component.imported_declared_non_spdx_license, spdx_cache)

    else:
        for i, unsaved_declared_license in enumerate(component.unsaved_declared_licenses):
            mapped_license = _get_mapped_licence_string(unsaved_declared_license)
            if mapped_license:
                component.unsaved_declared_licenses[i] = mapped_license
        component.imported_declared_multiple_licenses = ", ".join(component.unsaved_declared_licenses)
        component.imported_declared_license_name = component.imported_declared_multiple_licenses


def _prepare_imported_concluded_license(component: License_Component, spdx_cache: SPDXLicenseCache) -> None:
    if not component.unsaved_concluded_licenses:
        component.imported_concluded_license_name = NO_LICENSE_INFORMATION
    elif len(component.unsaved_concluded_licenses) == 1:
        component.imported_concluded_spdx_license = spdx_cache.get(component.unsaved_concluded_licenses[0])
        if component.imported_concluded_spdx_license:

            component.imported_concluded_license_name = component.imported_concluded_spdx_license.spdx_id
        else:
            licensing = get_spdx_licensing()
            try:
                expression_info = licensing.validate(component.unsaved_concluded_licenses[0], strict=True)
                if not expression_info.errors:
                    component.imported_concluded_license_expression = expression_info.normalized_expression
                    component.imported_concluded_license_name = component.imported_concluded_license_expression
                else:
                    component.imported_concluded_non_spdx_license = component.unsaved_concluded_licenses[0]
                    component.imported_concluded_license_name = component.imported_concluded_non_spdx_license
            except Exception:
                component.imported_concluded_non_spdx_license = component.unsaved_concluded_licenses[0]
                component.imported_concluded_license_name = component.imported_concluded_non_spdx_license

    else:
        component.imported_concluded_multiple_licenses = ", ".join(component.unsaved_concluded_licenses)
        component.imported_concluded_license_name = component.imported_concluded_multiple_licenses


def set_effective_license(component: License_Component) -> None:
    component.effective_license_name = NO_LICENSE_INFORMATION
    component.effective_spdx_license = None
    component.effective_license_expression = ""
    component.effective_non_spdx_license = ""
    component.effective_multiple_licenses = ""

    if component.manual_concluded_license_name != NO_LICENSE_INFORMATION:
        component.effective_license_name = component.manual_concluded_license_name
        component.effective_spdx_license = component.manual_concluded_spdx_license
        component.effective_license_expression = component.manual_concluded_license_expression
        component.effective_non_spdx_license = component.manual_concluded_non_spdx_license
    elif component.imported_concluded_license_name != NO_LICENSE_INFORMATION:
        component.effective_license_name = component.imported_concluded_license_name
        component.effective_spdx_license = component.imported_concluded_spdx_license
        component.effective_license_expression = component.imported_concluded_license_expression
        component.effective_non_spdx_license = component.imported_concluded_non_spdx_license
        component.effective_multiple_licenses = component.imported_concluded_multiple_licenses
    elif component.imported_declared_license_name != NO_LICENSE_INFORMATION:
        component.effective_license_name = component.imported_declared_license_name
        component.effective_spdx_license = component.imported_declared_spdx_license
        component.effective_license_expression = component.imported_declared_license_expression
        component.effective_non_spdx_license = component.imported_declared_non_spdx_license
        component.effective_multiple_licenses = component.imported_declared_multiple_licenses


def license_components_bulk_delete(product: Product, component_ids: list[int]) -> None:
    components = _check_components(product, component_ids)
    components.delete()


def _check_components(product: Product, component_ids: list[int]) -> QuerySet[License_Component]:
    components = License_Component.objects.filter(id__in=component_ids)
    if len(components) != len(component_ids):
        raise ValidationError("Some components do not exist")

    for component in components:
        if component.product != product:
            raise ValidationError(f"Component {component.pk} does not belong to product {product.pk}")

    return components


def save_concluded_license(component: License_Component) -> None:
    component.manual_concluded_license_name = NO_LICENSE_INFORMATION

    if component.manual_concluded_spdx_license:
        component.manual_concluded_license_name = component.manual_concluded_spdx_license.spdx_id
    elif component.manual_concluded_license_expression:
        licensing = get_spdx_licensing()
        expression_info = licensing.validate(component.manual_concluded_license_expression, strict=True)
        if not expression_info.errors:
            component.manual_concluded_license_name = component.manual_concluded_license_expression
        else:
            raise ValidationError("Invalid concluded license expression")
    elif component.manual_concluded_non_spdx_license:
        component.manual_concluded_license_name = component.manual_concluded_non_spdx_license

    set_effective_license(component)
    update_concluded_license(component)

    license_policy = get_license_policy(component.product)
    if license_policy:
        license_evaluation_results = get_license_evaluation_results_for_product(component.product)
        apply_license_policy_to_component(
            component,
            license_evaluation_results,
            get_comma_separated_as_list(license_policy.ignore_component_types),
            SPDXLicenseCache(),
        )

    component.save()


def _get_mapped_licence_string(license_string: str) -> Optional[str]:
    license_object = LicenseLynx.map(license_string)

    print("---")
    print(license_string)
    if license_object and license_object.id != license_string:
        print(license_object.id)
        
    return license_object.id if license_object else None

def _get_mapped_licence(license_string: str, spdx_cache: SPDXLicenseCache) -> Optional[License]:
    license_string = _get_mapped_licence_string(license_string)
    return spdx_cache.get(license_string) if license_string else None
