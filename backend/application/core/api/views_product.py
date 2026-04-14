import logging
import re
from tempfile import NamedTemporaryFile
from typing import Any

from django.db.models import QuerySet
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
)
from rest_framework.viewsets import GenericViewSet, ModelViewSet, ViewSet

from application.access_control.api.serializers import (
    ApiTokenCreateResponseSerializer,
)
from application.access_control.queries.api_token import get_api_token_by_id
from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.commons.services.log_message import format_log_message
from application.core.api.filters import (
    BranchFilter,
    ProductAuthorizationGroupMemberFilter,
    ProductFilter,
    ProductGroupFilter,
    ProductMemberFilter,
    ServiceFilter,
)
from application.core.api.permissions import (
    UserHasBranchPermission,
    UserHasProductAuthorizationGroupMemberPermission,
    UserHasProductGroupPermission,
    UserHasProductMemberPermission,
    UserHasProductPermission,
    UserHasServicePermission,
)
from application.core.api.serializers_observation import (
    ObservationBulkAssessmentSerializer,
    ObservationBulkDeleteSerializer,
    ObservationBulkMarkDuplicatesSerializer,
)
from application.core.api.serializers_product import (
    BranchNameSerializer,
    BranchSerializer,
    ProductApiTokenSerializer,
    ProductAuthorizationGroupMemberSerializer,
    ProductGroupSerializer,
    ProductListSerializer,
    ProductMemberSerializer,
    ProductNameSerializer,
    ProductSerializer,
    ServiceNameSerializer,
    ServiceSerializer,
)
from application.core.models import (
    Branch,
    Observation,
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
    Service,
)
from application.core.queries.branch import get_branches
from application.core.queries.product import get_product_by_id, get_products
from application.core.queries.product_member import (
    get_product_authorization_group_members,
    get_product_members,
)
from application.core.queries.service import get_services
from application.core.services.export_observations import (
    export_observations_csv_for_product,
    export_observations_excel_for_product,
)
from application.core.services.observations_bulk_actions import (
    observations_bulk_assessment,
    observations_bulk_delete,
    observations_bulk_mark_duplicates,
)
from application.core.services.product_api_token import (
    create_product_api_token,
    get_product_api_tokens,
    revoke_product_api_token,
)
from application.core.types import Status
from application.issue_tracker.services.issue_tracker import (
    push_observations_to_issue_tracker,
)
from application.licenses.api.serializers import LicenseComponentBulkDeleteSerializer
from application.licenses.services.export_license_components import (
    export_license_components_csv,
    export_license_components_excel,
)
from application.licenses.services.license_component import (
    license_components_bulk_delete,
)
from application.rules.services.rule_engine import Rule_Engine

logger = logging.getLogger("secobserve.core")


class ProductGroupViewSet(ModelViewSet):
    serializer_class = ProductGroupSerializer
    filterset_class = ProductGroupFilter
    permission_classes = (IsAuthenticated, UserHasProductGroupPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        settings = Settings.load()
        return get_products(
            is_product_group=True,
            with_observation_annotations=not settings.observation_count_from_metrics,
            with_metrics_annotations=settings.observation_count_from_metrics,
        )


class ProductGroupNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ProductNameSerializer
    filterset_class = ProductGroupFilter
    permission_classes = (IsAuthenticated, UserHasProductGroupPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        return get_products(is_product_group=True)


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    permission_classes = (IsAuthenticated, UserHasProductPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        settings = Settings.load()
        return (
            get_products(
                is_product_group=False,
                with_observation_annotations=not settings.observation_count_from_metrics,
                with_metrics_annotations=settings.observation_count_from_metrics,
            )
            .select_related("product_group")
            .select_related("product_group__license_policy")
            .select_related("repository_default_branch")
        )

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        if self.action == "list":
            return ProductListSerializer

        return super().get_serializer_class()

    @extend_schema(
        methods=["GET"],
        responses={200: None},
        parameters=[
            OpenApiParameter(name="status", description="status", type=str),
        ],
    )
    @action(detail=True, methods=["get"])
    def export_observations_excel(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        statuses = self.request.query_params.getlist("status")
        for status in statuses:
            if status and (status, status) not in Status.STATUS_CHOICES:
                raise ValidationError(f"Status {status} is not a valid choice")

        workbook = export_observations_excel_for_product(product, statuses)
        with NamedTemporaryFile() as tmp:
            workbook.save(tmp.name)  # nosemgrep: python.lang.correctness.tempfile.flush.tempfile-without-flush
            # export works fine without .flush()
            tmp.seek(0)
            stream = tmp.read()

        response = HttpResponse(
            content=stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = "attachment; filename=observations.xlsx"

        return response

    @extend_schema(
        methods=["GET"],
        responses={200: None},
        parameters=[
            OpenApiParameter(name="status", description="status", type=str),
        ],
    )
    @action(detail=True, methods=["get"])
    def export_observations_csv(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        statuses = self.request.query_params.getlist("status")
        for status in statuses:
            if status and (status, status) not in Status.STATUS_CHOICES:
                raise ValidationError(f"Status {status} is not a valid choice")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=observations.csv"

        export_observations_csv_for_product(response, product, statuses)

        return response

    @action(detail=True, methods=["get"])
    def export_license_components_excel(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        workbook = export_license_components_excel(product)
        with NamedTemporaryFile() as tmp:
            workbook.save(tmp.name)  # nosemgrep: python.lang.correctness.tempfile.flush.tempfile-without-flush
            # export works fine without .flush()
            tmp.seek(0)
            stream = tmp.read()

        response = HttpResponse(
            content=stream,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = "attachment; filename=license_components.xlsx"

        return response

    @extend_schema(
        methods=["GET"],
        responses={200: None},
    )
    @action(detail=True, methods=["get"])
    def export_license_components_csv(self, request: Request, pk: int) -> HttpResponse:
        product = self.__get_product(pk)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=license_observations.csv"

        export_license_components_csv(response, product)

        return response

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def apply_rules(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Product_Rule_Apply)

        rule_engine = Rule_Engine(product)
        rule_engine.apply_all_rules_for_product()

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkAssessmentSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def observations_bulk_assessment(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Observation_Assessment)

        request_serializer = ObservationBulkAssessmentSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_assessment(
            product=product,
            new_severity=request_serializer.validated_data.get("severity"),
            new_status=request_serializer.validated_data.get("status"),
            new_priority=request_serializer.validated_data.get("priority"),
            comment=request_serializer.validated_data.get("comment"),
            observation_ids=request_serializer.validated_data.get("observations"),
            new_vex_justification=request_serializer.validated_data.get("vex_justification"),
            new_risk_acceptance_expiry_date=request_serializer.validated_data.get("risk_acceptance_expiry_date"),
        )
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkMarkDuplicatesSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def observations_bulk_mark_duplicates(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Observation_Assessment)

        request_serializer = ObservationBulkMarkDuplicatesSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_mark_duplicates(
            product,
            request_serializer.validated_data.get("observation_id"),
            request_serializer.validated_data.get("potential_duplicates"),
        )
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=ObservationBulkDeleteSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def observations_bulk_delete(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Observation_Delete)

        request_serializer = ObservationBulkDeleteSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        observations_bulk_delete(product, request_serializer.validated_data.get("observations"))
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=LicenseComponentBulkDeleteSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def license_components_bulk_delete(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.License_Component_Delete)

        request_serializer = LicenseComponentBulkDeleteSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        license_components_bulk_delete(product, request_serializer.validated_data.get("components"))
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def synchronize_issues(self, request: Request, pk: int) -> Response:
        product = self.__get_product(pk)
        user_has_permission_or_403(product, Permissions.Product_Edit)

        observations = Observation.objects.filter(product=product)
        push_observations_to_issue_tracker(product, set(observations))

        return Response(status=HTTP_204_NO_CONTENT)

    def __get_product(self, pk: int) -> Product:
        if not pk:
            raise ValidationError("No id provided")

        product = get_product_by_id(pk)
        if not product:
            raise NotFound()

        user_has_permission_or_403(product, Permissions.Product_View)

        return product


class ProductNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ProductNameSerializer
    filterset_class = ProductFilter
    permission_classes = (IsAuthenticated, UserHasProductPermission)
    queryset = Product.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Product]:
        return get_products(is_product_group=False)


class ProductMemberViewSet(ModelViewSet):
    serializer_class = ProductMemberSerializer
    filterset_class = ProductMemberFilter
    permission_classes = (IsAuthenticated, UserHasProductMemberPermission)
    queryset = Product_Member.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[Product_Member]:
        return get_product_members().select_related("product").select_related("user")


class ProductAuthorizationGroupMemberViewSet(ModelViewSet):
    serializer_class = ProductAuthorizationGroupMemberSerializer
    filterset_class = ProductAuthorizationGroupMemberFilter
    permission_classes = (
        IsAuthenticated,
        UserHasProductAuthorizationGroupMemberPermission,
    )
    queryset = Product_Authorization_Group_Member.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[Product_Authorization_Group_Member]:
        return get_product_authorization_group_members().select_related("product").select_related("authorization_group")


class BranchViewSet(ModelViewSet):
    serializer_class = BranchSerializer
    filterset_class = BranchFilter
    permission_classes = (IsAuthenticated, UserHasBranchPermission)
    queryset = Branch.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Branch]:
        return get_branches(with_annotations=True).select_related("product")

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance: Branch = self.get_object()
        if instance.is_default_branch:
            raise ValidationError("You cannot delete the default branch of a product.")

        return super().destroy(request, *args, **kwargs)


class BranchNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = BranchNameSerializer
    filterset_class = BranchFilter
    permission_classes = (IsAuthenticated, UserHasBranchPermission)
    queryset = Branch.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Branch]:
        return get_branches().select_related("product")


class ServiceViewSet(ModelViewSet):
    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    permission_classes = (IsAuthenticated, UserHasServicePermission)
    queryset = Service.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Service]:
        return get_services(with_annotations=True).select_related("product")


class ServiceNameViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ServiceNameSerializer
    filterset_class = ServiceFilter
    permission_classes = (IsAuthenticated, UserHasServicePermission)
    queryset = Service.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Service]:
        return get_services().select_related("product")


class ProductApiTokenViewset(ViewSet):
    serializer_class = ProductApiTokenSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name="product", location=OpenApiParameter.QUERY, required=True, type=int),
        ],
    )
    def list(self, request: Request) -> Response:
        product_id = str(request.query_params.get("product", ""))
        if not product_id:
            raise ValidationError("Product is required")
        if not product_id.isdigit():
            raise ValidationError("Product id must be an integer")
        product = _get_product(int(str(product_id)))
        user_has_permission_or_403(product, Permissions.Product_View)
        tokens = get_product_api_tokens(product)
        serializer = ProductApiTokenSerializer(tokens, many=True)
        response_data = {"results": serializer.data}
        return Response(response_data)

    @extend_schema(
        request=ProductApiTokenSerializer,
        responses={HTTP_200_OK: ApiTokenCreateResponseSerializer},
    )
    def create(self, request: Request) -> Response:
        request_serializer = ProductApiTokenSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        product = _get_product(request_serializer.validated_data.get("product"))

        user_has_permission_or_403(product, Permissions.Product_Api_Token_Create)

        token = create_product_api_token(
            product,
            request_serializer.validated_data.get("role"),
            request_serializer.validated_data.get("name"),
            request_serializer.validated_data.get("expiration_date"),
        )

        response = Response({"token": token}, status=HTTP_201_CREATED)
        logger.info(format_log_message(message="Product API token created", response=response))
        return response

    @extend_schema(
        parameters=[
            OpenApiParameter(name="id", location=OpenApiParameter.PATH, required=True, type=int),
        ],
        responses={HTTP_204_NO_CONTENT: None},
    )
    def destroy(self, request: Request, pk: int) -> Response:
        API_TOKEN_NOT_VALID = "API token not valid"

        api_token = get_api_token_by_id(pk)
        if not api_token:
            raise ValidationError(API_TOKEN_NOT_VALID)

        if not re.match("-product-(\\d)*(-.*)?-api_token-", api_token.user.username):
            raise ValidationError(API_TOKEN_NOT_VALID)

        product_member = Product_Member.objects.filter(user=api_token.user).first()
        if not product_member:
            raise ValidationError(API_TOKEN_NOT_VALID)

        product = _get_product(product_member.product.pk)
        user_has_permission_or_403(product, Permissions.Product_Api_Token_Revoke)

        revoke_product_api_token(product, api_token)

        response = Response(status=HTTP_204_NO_CONTENT)
        logger.info(format_log_message(message="Product API token revoked", response=response))
        return response


def _get_product(product_id: int) -> Product:
    product = get_product_by_id(product_id)
    if not product:
        raise ValidationError(f"Product {product_id} does not exist")
    return product
