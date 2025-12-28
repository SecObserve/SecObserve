from typing import Optional

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Branch, Product
from application.core.queries.branch import get_branch_by_id, get_branch_by_name
from application.core.queries.product import get_product_by_id, get_product_by_name
from application.core.queries.service import get_service_by_id
from application.import_observations.api.filters import (
    ApiConfigurationFilter,
    ParserFilter,
    VulnerabilityCheckFilter,
)
from application.import_observations.api.permissions import (
    UserHasApiConfigurationPermission,
    UserHasVulnerabilityCheckPermission,
)
from application.import_observations.api.serializers import (
    ApiConfigurationSerializer,
    ApiImportObservationsByIdRequestSerializer,
    ApiImportObservationsByNameRequestSerializer,
    APIImportObservationsResponseSerializer,
    FileImportObservationsResponseSerializer,
    FileImportSBOMResponseSerializer,
    FileUploadObservationsByIdRequestSerializer,
    FileUploadObservationsByNameRequestSerializer,
    FileUploadSBOMByIdRequestSerializer,
    FileUploadSBOMByNameRequestSerializer,
    ParserSerializer,
    VulnerabilityCheckSerializer,
)
from application.import_observations.models import (
    Api_Configuration,
    Parser,
    Vulnerability_Check,
)
from application.import_observations.queries.api_configuration import (
    get_api_configuration_by_id,
    get_api_configuration_by_name,
    get_api_configurations,
)
from application.import_observations.queries.vulnerability_check import (
    get_vulnerability_checks,
)
from application.import_observations.scanners.osv_scanner import (
    scan_branch,
    scan_product,
)
from application.import_observations.services.import_observations import (
    ApiImportParameters,
    FileUploadParameters,
    api_import_observations,
    file_upload_observations,
)


class ApiImportObservationsById(APIView):
    @extend_schema(
        request=ApiImportObservationsByIdRequestSerializer,
        responses={status.HTTP_200_OK: APIImportObservationsResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = ApiImportObservationsByIdRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        api_configuration_id = request_serializer.validated_data.get("api_configuration")
        api_configuration = get_api_configuration_by_id(api_configuration_id)
        if not api_configuration:
            raise ValidationError(f"API Configuration {api_configuration} does not exist")

        user_has_permission_or_403(api_configuration.product, Permissions.Product_Import_Observations)

        branch = None
        branch_id = request_serializer.validated_data.get("branch")
        if branch_id:
            branch = get_branch_by_id(api_configuration.product, branch_id)
            if not branch:
                raise ValidationError(f"Branch {branch_id} does not exist for product {api_configuration.product}")

        response_data = _api_import_observations(request_serializer, api_configuration, branch)
        return Response(response_data)


class ApiImportObservationsByName(APIView):
    @extend_schema(
        request=ApiImportObservationsByNameRequestSerializer,
        responses={status.HTTP_200_OK: APIImportObservationsResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = ApiImportObservationsByNameRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        product_name = request_serializer.validated_data.get("product_name")
        product = get_product_by_name(product_name)
        if not product:
            raise ValidationError(f"Product {product_name} does not exist")

        user_has_permission_or_403(product, Permissions.Product_Import_Observations)

        branch = None
        branch_name = request_serializer.validated_data.get("branch_name")
        if branch_name:
            branch = get_branch_by_name(product, branch_name)
            if not branch:
                branch = Branch.objects.create(
                    product=product, name=branch_name, is_default_branch=product.repository_default_branch is None
                )

        api_configuration_name = request_serializer.validated_data.get("api_configuration_name")
        api_configuration = get_api_configuration_by_name(product, api_configuration_name)
        if not api_configuration:
            raise ValidationError(
                f"API Configuration {api_configuration_name} does not exist for product {product.name}"
            )

        response_data = _api_import_observations(request_serializer, api_configuration, branch)
        return Response(response_data)


def _api_import_observations(
    request_serializer: Serializer, api_configuration: Api_Configuration, branch: Optional[Branch]
) -> dict[str, int]:
    service_name = _get_service_name(api_configuration.product, request_serializer)
    docker_image_name_tag = request_serializer.validated_data.get("docker_image_name_tag")
    endpoint_url = request_serializer.validated_data.get("endpoint_url")
    kubernetes_cluster = request_serializer.validated_data.get("kubernetes_cluster")

    api_import_parameters = ApiImportParameters(
        api_configuration=api_configuration,
        branch=branch,
        service_name=service_name,
        docker_image_name_tag=docker_image_name_tag,
        endpoint_url=endpoint_url,
        kubernetes_cluster=kubernetes_cluster,
    )

    (
        observations_new,
        observations_updated,
        observations_resolved,
    ) = api_import_observations(api_import_parameters)

    response_data = {
        "observations_new": observations_new,
        "observations_updated": observations_updated,
        "observations_resolved": observations_resolved,
    }

    return response_data


class FileUploadObservationsById(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=FileUploadObservationsByIdRequestSerializer,
        responses={status.HTTP_200_OK: FileImportObservationsResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = FileUploadObservationsByIdRequestSerializer(data=request.data)
        product, branch = _get_product_branch_by_id(request_serializer)
        service_name = _get_service_name(product, request_serializer)
        response_data = _file_upload_observations(request_serializer, product, branch, service_name)
        return Response(response_data)


class FileUploadObservationsByName(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=FileUploadObservationsByNameRequestSerializer,
        responses={status.HTTP_200_OK: FileImportObservationsResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = FileUploadObservationsByNameRequestSerializer(data=request.data)
        product, branch = _get_product_branch_by_name(request_serializer)
        service_name = request_serializer.validated_data.get("service", "")
        response_data = _file_upload_observations(request_serializer, product, branch, service_name)

        return Response(response_data)


class FileUploadSBOMById(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=FileUploadSBOMByIdRequestSerializer,
        responses={status.HTTP_200_OK: FileImportSBOMResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = FileUploadSBOMByIdRequestSerializer(data=request.data)
        product, branch = _get_product_branch_by_id(request_serializer)
        service_name = _get_service_name(product, request_serializer)
        response_data = _file_upload_sbom(request_serializer, product, branch, service_name)
        return Response(response_data)


class FileUploadSBOMByName(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=FileUploadSBOMByNameRequestSerializer,
        responses={status.HTTP_200_OK: FileImportSBOMResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = FileUploadSBOMByNameRequestSerializer(data=request.data)
        product, branch = _get_product_branch_by_name(request_serializer)
        service_name = request_serializer.validated_data.get("service", "")
        response_data = _file_upload_sbom(request_serializer, product, branch, service_name)
        return Response(response_data)


def _get_product_branch_by_id(request_serializer: Serializer) -> tuple[Product, Optional[Branch]]:
    if not request_serializer.is_valid():
        raise ValidationError(request_serializer.errors)

    product_id = request_serializer.validated_data.get("product")
    product = get_product_by_id(product_id)
    if not product:
        raise ValidationError(f"Product {product_id} does not exist")

    user_has_permission_or_403(product, Permissions.Product_Import_Observations)

    branch = None
    branch_id = request_serializer.validated_data.get("branch")
    if branch_id:
        branch = get_branch_by_id(product, branch_id)
        if not branch:
            raise ValidationError(f"Branch {branch_id} does not exist for product {product}")
    return product, branch


def _get_product_branch_by_name(request_serializer: Serializer) -> tuple[Product, Optional[Branch]]:
    if not request_serializer.is_valid():
        raise ValidationError(request_serializer.errors)

    product_name = request_serializer.validated_data.get("product_name")
    product = get_product_by_name(product_name)
    if not product:
        raise ValidationError(f"Product {product_name} does not exist")

    user_has_permission_or_403(product, Permissions.Product_Import_Observations)

    branch = None
    branch_name = request_serializer.validated_data.get("branch_name")
    if branch_name:
        branch = get_branch_by_name(product, branch_name)
        if not branch:
            branch = Branch.objects.create(
                product=product, name=branch_name, is_default_branch=product.repository_default_branch is None
            )
    return product, branch


def _get_service_name(product: Product, request_serializer: Serializer) -> str:
    service_name = request_serializer.validated_data.get("service", "")
    service_id = request_serializer.validated_data.get("service_id")

    if service_name and service_id:
        raise ValidationError("Only one of the fields service and service_id may be set")

    if service_id:
        service = get_service_by_id(product, service_id)
        if not service:
            raise ValidationError(f"Service {service_id} does not exist for product {product.name}")
        service_name = service.name

    return service_name


def _file_upload_observations(
    request_serializer: Serializer, product: Product, branch: Optional[Branch], service_name: str
) -> dict[str, int]:
    file = request_serializer.validated_data.get("file")
    docker_image_name_tag = request_serializer.validated_data.get("docker_image_name_tag")
    endpoint_url = request_serializer.validated_data.get("endpoint_url")
    kubernetes_cluster = request_serializer.validated_data.get("kubernetes_cluster")
    suppress_licenses = request_serializer.validated_data.get("suppress_licenses", False)

    file_upload_parameters = FileUploadParameters(
        product=product,
        branch=branch,
        file=file,
        service_name=service_name,
        docker_image_name_tag=docker_image_name_tag,
        endpoint_url=endpoint_url,
        kubernetes_cluster=kubernetes_cluster,
        suppress_licenses=suppress_licenses,
        sbom=False,
    )

    (
        observations_new,
        observations_updated,
        observations_resolved,
        license_components_new,
        license_components_updated,
        license_components_deleted,
    ) = file_upload_observations(file_upload_parameters)

    num_observations = observations_new + observations_updated + observations_resolved
    num_license_components = license_components_new + license_components_updated + license_components_deleted

    response_data = {}
    if num_observations > 0 or num_license_components == 0:
        response_data["observations_new"] = observations_new
        response_data["observations_updated"] = observations_updated
        response_data["observations_resolved"] = observations_resolved
    if num_license_components > 0:
        response_data["license_components_new"] = license_components_new
        response_data["license_components_updated"] = license_components_updated
        response_data["license_components_deleted"] = license_components_deleted
    return response_data


def _file_upload_sbom(
    request_serializer: Serializer, product: Product, branch: Optional[Branch], service_name: str
) -> dict[str, int]:
    file = request_serializer.validated_data.get("file")

    file_upload_parameters = FileUploadParameters(
        product=product,
        branch=branch,
        file=file,
        service_name=service_name,
        docker_image_name_tag="",
        endpoint_url="",
        kubernetes_cluster="",
        suppress_licenses=False,
        sbom=True,
    )

    (
        _,
        _,
        _,
        license_components_new,
        license_components_updated,
        license_components_deleted,
    ) = file_upload_observations(file_upload_parameters)

    num_license_components = license_components_new + license_components_updated + license_components_deleted

    response_data = {}
    if num_license_components > 0:
        response_data["license_components_new"] = license_components_new
        response_data["license_components_updated"] = license_components_updated
        response_data["license_components_deleted"] = license_components_deleted
    return response_data


class ApiConfigurationViewSet(ModelViewSet):
    serializer_class = ApiConfigurationSerializer
    filterset_class = ApiConfigurationFilter
    permission_classes = (IsAuthenticated, UserHasApiConfigurationPermission)
    queryset = Api_Configuration.objects.none()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Api_Configuration]:
        return get_api_configurations().select_related("product").select_related("product__product_group")


class VulnerabilityCheckViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = VulnerabilityCheckSerializer
    filterset_class = VulnerabilityCheckFilter
    permission_classes = (IsAuthenticated, UserHasVulnerabilityCheckPermission)
    queryset = Vulnerability_Check.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[Vulnerability_Check]:
        return get_vulnerability_checks().select_related("branch").select_related("service")


class ParserViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin):
    serializer_class = ParserSerializer
    filterset_class = ParserFilter
    queryset = Parser.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]


class ScanOSVProductView(APIView):
    @extend_schema(
        request=None,
        responses={status.HTTP_200_OK: APIImportObservationsResponseSerializer},
    )
    @action(detail=True, methods=["post"])
    def post(self, request: Request, product_id: int) -> Response:
        product = get_product_by_id(product_id)
        if not product:
            return Response(status=HTTP_404_NOT_FOUND)

        user_has_permission_or_403(product, Permissions.Product_Scan_OSV)

        if not product.osv_enabled:
            raise ValidationError(f"OSV scan is not enabled for product {product.name}")

        observations_new, observations_updated, observations_resolved = scan_product(product)
        response_data = {
            "observations_new": observations_new,
            "observations_updated": observations_updated,
            "observations_resolved": observations_resolved,
        }
        return Response(response_data)


class ScanOSVBranchView(APIView):
    @extend_schema(
        request=None,
        responses={status.HTTP_200_OK: APIImportObservationsResponseSerializer},
    )
    @action(detail=True, methods=["post"])
    def post(self, request: Request, product_id: int, branch_id: int) -> Response:
        product = get_product_by_id(product_id)
        if not product:
            return Response(status=HTTP_404_NOT_FOUND)

        user_has_permission_or_403(product, Permissions.Product_Scan_OSV)

        if not product.osv_enabled:
            raise ValidationError(f"OSV scan is not enabled for product {product.name}")

        branch = get_branch_by_id(product, branch_id)
        if not branch:
            return Response(status=HTTP_404_NOT_FOUND)

        observations_new, observations_updated, observations_resolved = scan_branch(branch)
        response_data = {
            "observations_new": observations_new,
            "observations_updated": observations_updated,
            "observations_resolved": observations_resolved,
        }
        return Response(response_data)
