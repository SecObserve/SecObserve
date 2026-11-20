from typing import Optional

from django.db.models.query import QuerySet

from application.licenses.models import License


def get_license(license_id: int) -> Optional[License]:
    try:
        return License.objects.get(id=license_id)
    except License.DoesNotExist:
        return None


def get_license_by_spdx_id(spdx_id: str) -> Optional[License]:
    try:
        return License.objects.get(spdx_id=spdx_id)
    except License.DoesNotExist:
        return None


def get_scancode_categories(licenses: QuerySet[License]) -> list[str]:
    return list(
        licenses.exclude(scancode_category="")
        .order_by("scancode_category")
        .values_list("scancode_category", flat=True)
        .distinct()
    )
