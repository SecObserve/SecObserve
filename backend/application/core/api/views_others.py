from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions
from application.core.api.filters import ComponentFilter
from application.core.api.serializers_others import (
    ComponentNameSerializer,
    ComponentSerializer,
    PURLTypeElementSerializer,
    PURLTypeSerializer,
)
from application.core.models import Component
from application.core.queries.component import get_components
from application.core.queries.product import get_product_by_id
from application.core.services.purl_type import get_purl_type, get_purl_types


class PURLTypeOneView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: PURLTypeSerializer},
    )
    @action(detail=True, methods=["get"])
    def get(self, request: Request, purl_type_id: str) -> Response:
        purl_type = get_purl_type(purl_type_id)
        if purl_type:
            response_serializer = PURLTypeElementSerializer(purl_type)
            return Response(
                status=HTTP_200_OK,
                data=response_serializer.data,
            )

        return Response(status=HTTP_404_NOT_FOUND)


class PURLTypeManyView(APIView):
    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: PURLTypeSerializer},
    )
    @action(detail=False, methods=["get"])
    def get(self, request: Request) -> Response:
        product_id = request.query_params.get("product")
        if not product_id:
            return Response(status=HTTP_404_NOT_FOUND)
        product = get_product_by_id(int(product_id))
        if not product:
            return Response(status=HTTP_404_NOT_FOUND)
        if not user_has_permission(product, Permissions.Product_View):
            return Response(status=HTTP_404_NOT_FOUND)

        for_observations = bool(request.query_params.get("for_observations"))
        for_license_components = bool(request.query_params.get("for_license_components"))
        purl_types = get_purl_types(product, for_observations, for_license_components)

        response_serializer = PURLTypeSerializer(purl_types)
        return Response(
            status=HTTP_200_OK,
            data=response_serializer.data,
        )


class ComponentViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ComponentSerializer
    filterset_class = ComponentFilter
    permission_classes = (IsAuthenticated,)
    queryset = Component.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["component_name_version"]

    def get_queryset(self) -> QuerySet[Component]:
        return (
            get_components()
            .select_related("product")
            .select_related("product__product_group")
            .select_related("branch")
            .select_related("origin_service")
        )


class ComponentNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ComponentNameSerializer
    filterset_class = ComponentFilter
    permission_classes = (IsAuthenticated,)
    queryset = Component.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["component_name_version"]

    def get_queryset(self) -> QuerySet[Component]:
        return get_components()
