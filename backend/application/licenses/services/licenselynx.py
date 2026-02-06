from typing import Optional

from licenselynx.licenselynx import LicenseLynx

from application.commons.services.functions import get_comma_separated_as_list
from application.licenses.models import License, License_Component
from application.licenses.services.license_component import set_effective_license
from application.licenses.services.spdx_license_cache import SPDXLicenseCache
from application.licenses.types import NO_LICENSE_INFORMATION

SET_BY_LICENSELYNX = "Set by LicenseLynx"


def apply_licenselynx(component: License_Component, spdx_cache: SPDXLicenseCache) -> None:
    if (
        component.manual_concluded_license_name
        and component.manual_concluded_license_name != NO_LICENSE_INFORMATION
        and component.manual_concluded_comment != SET_BY_LICENSELYNX
    ):
        return

    if component.imported_declared_non_spdx_license:
        mapped_license = _get_mapped_licence(component.imported_declared_non_spdx_license, spdx_cache)
        if mapped_license:
            component.manual_concluded_spdx_license = mapped_license
            component.manual_concluded_comment = SET_BY_LICENSELYNX
            component.manual_concluded_license_name = mapped_license.spdx_id
    elif component.imported_declared_multiple_licenses:
        licenses = get_comma_separated_as_list(component.imported_declared_multiple_licenses)
        for i, license_string in enumerate(licenses):
            mapped_license_string = _get_mapped_licence_string(license_string)
            if mapped_license_string:
                licenses[i] = mapped_license_string
        component.imported_declared_multiple_licenses = ", ".join(licenses)
        component.imported_declared_license_name = component.imported_declared_multiple_licenses

    if component.imported_concluded_non_spdx_license:
        mapped_license = _get_mapped_licence(component.imported_concluded_non_spdx_license, spdx_cache)
        if mapped_license:
            component.manual_concluded_spdx_license = mapped_license
            component.manual_concluded_comment = SET_BY_LICENSELYNX
            component.manual_concluded_license_name = mapped_license.spdx_id
    elif component.imported_concluded_multiple_licenses:
        licenses = get_comma_separated_as_list(component.imported_concluded_multiple_licenses)
        for i, license_string in enumerate(licenses):
            mapped_license_string = _get_mapped_licence_string(license_string)
            if mapped_license_string:
                licenses[i] = mapped_license_string
        component.imported_concluded_multiple_licenses = ", ".join(licenses)
        component.imported_concluded_license_name = component.imported_concluded_multiple_licenses

    set_effective_license(component)


def _get_mapped_licence_string(license_string: str) -> Optional[str]:
    license_object = LicenseLynx.map(license_string)
    return license_object.id if license_object else None


def _get_mapped_licence(license_string: str, spdx_cache: SPDXLicenseCache) -> Optional[License]:
    mapped_license_string = _get_mapped_licence_string(license_string)
    return spdx_cache.get(mapped_license_string) if mapped_license_string else None
