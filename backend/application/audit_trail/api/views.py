from typing import Any

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from application.audit_trail.api.filters import ProductAuditEventFilter
from application.audit_trail.api.serializers import ProductAuditEventSerializer
from application.audit_trail.models import Product_Audit_Event
from application.audit_trail.queries.product_audit_event import (
    get_product_audit_events,
)
from application.authorization.services.authorization import (
    user_has_permission_or_403,
)
from application.authorization.services.roles_permissions import Permissions
from application.core.queries.product import get_product_by_id


class ProductAuditEventViewSet(GenericViewSet, ListModelMixin):
    serializer_class = ProductAuditEventSerializer
    filterset_class = ProductAuditEventFilter
    permission_classes = (IsAuthenticated,)
    queryset = Product_Audit_Event.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["object_name"]

    def get_queryset(self) -> QuerySet[Product_Audit_Event]:
        return get_product_audit_events()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="product",
                location=OpenApiParameter.QUERY,
                type=int,
                description="Required for all users except superusers",
            ),
        ],
    )
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        # The permission depends on the role in the product, superusers can also see the events of deleted products
        if not request.user.is_superuser:
            product_id = str(request.query_params.get("product", ""))
            if not product_id.isdigit():
                raise ValidationError("Product is required")
            product = get_product_by_id(int(product_id))
            if not product:
                raise ValidationError(f"Product {product_id} does not exist")
            user_has_permission_or_403(product, Permissions.Product_Audit_Trail_View)

        return super().list(request, *args, **kwargs)
