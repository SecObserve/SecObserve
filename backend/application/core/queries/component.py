from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet

from application.access_control.services.current_user import get_current_user
from application.core.models import (
    Component,
    Observation,
)
from application.core.queries.product import get_products
from application.core.types import Status
from application.licenses.models import License_Component


def get_components() -> QuerySet[Component]:
    user = get_current_user()

    if user is None:
        return Component.objects.none()

    components = Component.objects.all().order_by("id")

    active_observations = Observation.objects.filter(
        origin_component=OuterRef("pk"),
        current_status__in=Status.STATUS_ACTIVE,
    )
    inactive_observations = Observation.objects.filter(
        origin_component=OuterRef("pk"),
        current_status__in=Status.STATUS_INACTIVE,
    )
    license_components = License_Component.objects.filter(component=OuterRef("pk"))

    # The annotations are scoped to the products the user is allowed to read, so that a component
    # is only returned if it has at least one observation or license component the user can see.
    # The products are resolved before the query is built: as a subquery the permission check
    # would be repeated in each of the subqueries below and would keep the database from using
    # the indexes of the product columns.
    if not user.is_superuser:
        product_ids = list(get_products(is_product_group=False).values_list("pk", flat=True))
        active_observations = active_observations.filter(product_id__in=product_ids)
        inactive_observations = inactive_observations.filter(product_id__in=product_ids)
        license_components = license_components.filter(product_id__in=product_ids)

    components = components.annotate(
        has_active_observations=Exists(active_observations),
        has_inactive_observations=Exists(inactive_observations),
        has_licenses=Exists(license_components),
    )

    if not user.is_superuser:
        components = components.filter(
            Q(has_active_observations=True) | Q(has_inactive_observations=True) | Q(has_licenses=True)
        )

    return components
