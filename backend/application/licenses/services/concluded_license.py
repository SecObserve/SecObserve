from application.access_control.services.current_user import get_current_user
from application.core.models import Product
from application.licenses.models import Concluded_License, License_Component
from application.licenses.types import NO_LICENSE_INFORMATION


class ConcludeLicenseApplicator:
    def __init__(self, product: Product) -> None:
        self.product_name_version: dict[str, Concluded_License] = {}
        self.product_name: dict[str, Concluded_License] = {}
        self.product_group_name_version: dict[str, Concluded_License] = {}
        self.product_group_name: dict[str, Concluded_License] = {}

        concluded_licenses = Concluded_License.objects.filter(product=product).order_by(
            "last_updated", "component_purl_type", "component_name", "component_version"
        )
        for concluded_license in concluded_licenses:
            self.product_name_version[
                f"{concluded_license.component_purl_type}|{concluded_license.component_name}|"
                + f"{concluded_license.component_version}"
            ] = concluded_license
            self.product_name[f"{concluded_license.component_purl_type}|{concluded_license.component_name}"] = (
                concluded_license
            )

        product_group_products = []
        if product.product_group:
            product_group_products = list(
                Product.objects.filter(product_group=product.product_group).exclude(pk=product.pk)
            )
            concluded_licenses = Concluded_License.objects.filter(product__in=product_group_products).order_by(
                "last_updated", "component_purl_type", "component_name", "component_version"
            )
            for concluded_license in concluded_licenses:
                self.product_group_name_version[
                    f"{concluded_license.component_purl_type}|{concluded_license.component_name}|"
                    + f"{concluded_license.component_version}"
                ] = concluded_license
                self.product_group_name[
                    f"{concluded_license.component_purl_type}|{concluded_license.component_name}"
                ] = concluded_license

    def apply_concluded_license(self, component: License_Component) -> None:
        concluded_license = None
        manual_concluded_comment = ""

        concluded_license = self.product_name_version.get(
            f"{component.component_purl_type}|{component.component_name}|{component.component_version}"
        )
        if concluded_license:
            manual_concluded_comment = f"Set manually by {str(concluded_license.user)}"

        if not concluded_license:
            concluded_license = self.product_group_name_version.get(
                f"{component.component_purl_type}|{component.component_name}|{component.component_version}"
            )
            if concluded_license:
                manual_concluded_comment = (
                    f"Copied from product {concluded_license.product}, set by {str(concluded_license.user)}"
                )

        if not concluded_license:
            concluded_license = self.product_name.get(
                f"{component.component_purl_type}|{component.component_name}"
            )
            if concluded_license:
                manual_concluded_comment = (
                    f"Copied from version {concluded_license.component_version}, set by {str(concluded_license.user)}"
                )

        if not concluded_license:
            concluded_license = self.product_group_name.get(
                f"{component.component_purl_type}|{component.component_name}"
            )
            if concluded_license:
                manual_concluded_comment = (
                    f"Copied from product {concluded_license.product} and "
                    + f"version {concluded_license.component_version}, set by {str(concluded_license.user)}"
                )

        if concluded_license:
            if (
                concluded_license.manual_concluded_spdx_license
                and component.effective_spdx_license != concluded_license.manual_concluded_spdx_license
            ):
                component.manual_concluded_spdx_license = concluded_license.manual_concluded_spdx_license
                component.manual_concluded_license_name = concluded_license.manual_concluded_spdx_license.spdx_id
                component.manual_concluded_comment = manual_concluded_comment
            elif (
                concluded_license.manual_concluded_license_expression
                and component.effective_license_expression != concluded_license.manual_concluded_license_expression
            ):
                component.manual_concluded_license_expression = concluded_license.manual_concluded_license_expression
                component.manual_concluded_license_name = concluded_license.manual_concluded_license_expression
                component.manual_concluded_comment = manual_concluded_comment
            elif (
                concluded_license.manual_concluded_non_spdx_license
                and component.effective_non_spdx_license != concluded_license.manual_concluded_non_spdx_license
            ):
                component.manual_concluded_non_spdx_license = concluded_license.manual_concluded_non_spdx_license
                component.manual_concluded_license_name = concluded_license.manual_concluded_non_spdx_license
                component.manual_concluded_comment = manual_concluded_comment


def update_concluded_license(component: License_Component) -> None:
    if component.manual_concluded_license_name == NO_LICENSE_INFORMATION:
        component.manual_concluded_comment = ""
        try:
            concluded_license = Concluded_License.objects.get(
                product=component.product,
                component_purl_type=component.component_purl_type,
                component_name=component.component_name,
                component_version=component.component_version,
            )
            concluded_license.delete()

        except Concluded_License.DoesNotExist:
            pass
    else:
        concluded_license, _ = Concluded_License.objects.update_or_create(
            product=component.product,
            component_purl_type=component.component_purl_type,
            component_name=component.component_name,
            component_version=component.component_version,
            defaults={
                "manual_concluded_spdx_license": component.manual_concluded_spdx_license,
                "manual_concluded_license_expression": component.manual_concluded_license_expression,
                "manual_concluded_non_spdx_license": component.manual_concluded_non_spdx_license,
                "user": get_current_user(),
            },
        )
        component.manual_concluded_comment = f"Set manually by {str(concluded_license.user)}"
