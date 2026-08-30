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
    license_components = License_Component.objects.filter(component=OuterRef("pk"))

    # The annotations are scoped to the products the user is allowed to read, so that a component
    # is only returned if it has at least one observation or license component the user can see.
    if not user.is_superuser:
        products = get_products().values("pk")
        active_observations = active_observations.filter(product__in=products)
        license_components = license_components.filter(product__in=products)

    components = components.annotate(
        has_observations=Exists(active_observations),
        has_licenses=Exists(license_components),
    )

    if not user.is_superuser:
        components = components.filter(Q(has_observations=True) | Q(has_licenses=True))

    return components
