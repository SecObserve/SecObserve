from typing import Any

from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.commons.models import Settings
from application.core.queries.product import get_product_by_id
from application.scancodeio.api.filters import ScanCodeIOProjectFilter
from application.scancodeio.api.permissions import UserHasScanCodeIOProjectPermission
from application.scancodeio.api.serializers import (
    CreateScanCodeIOProjectSerializer,
    ScanCodeIOPipelineSerializer,
    ScanCodeIOProjectDetailsSerializer,
    ScanCodeIOProjectSerializer,
)
from application.scancodeio.models import ScanCodeIO_Project
from application.scancodeio.queries.scancodeio_project import (
    get_scancodeio_project_by_webhook_token_hash,
    get_scancodeio_projects,
)
from application.scancodeio.services.scancodeio import (
    create_scancodeio_project,
    delete_scancodeio_project,
    get_scancodeio_pipelines,
    get_scancodeio_project_details,
    hash_webhook_token,
    process_scancodeio_webhook,
)
from application.scancodeio.types import CreateProjectParameters


def _check_feature_enabled() -> None:
    if not Settings.load().feature_scancodeio_integration:
        raise ValidationError("ScanCode.io integration is not enabled")


class CreateScanCodeIOProjectView(APIView):
    parser_classes = [MultiPartParser]

    @extend_schema(
        request=CreateScanCodeIOProjectSerializer,
        responses={HTTP_201_CREATED: ScanCodeIOProjectSerializer},
    )
    def post(self, request: Request, product_id: int) -> Response:
        product = get_product_by_id(product_id)
        if not product:
            return Response(status=HTTP_404_NOT_FOUND)

        user_has_permission_or_403(product, Permissions.Product_Edit)

        _check_feature_enabled()

        request_serializer = CreateScanCodeIOProjectSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        parameters = CreateProjectParameters(
            name=request_serializer.validated_data["name"],
            input_urls=request_serializer.validated_data["input_urls"],
            upload_file=request_serializer.validated_data.get("upload_file"),
            pipeline=request_serializer.validated_data["pipeline"],
            execute_now=request_serializer.validated_data["execute_now"],
        )
        scancodeio_project = create_scancodeio_project(product, parameters)

        return Response(ScanCodeIOProjectSerializer(scancodeio_project).data, status=HTTP_201_CREATED)


class ScanCodeIOProjectViewSet(GenericViewSet, ListModelMixin, RetrieveModelMixin, DestroyModelMixin):
    serializer_class = ScanCodeIOProjectSerializer
    filterset_class = ScanCodeIOProjectFilter
    permission_classes = (IsAuthenticated, UserHasScanCodeIOProjectPermission)
    queryset = ScanCodeIO_Project.objects.none()
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self) -> QuerySet[ScanCodeIO_Project]:
        return get_scancodeio_projects()

    @extend_schema(
        request=None,
        parameters=[
            OpenApiParameter(
                name="name",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Exact, case- and whitespace-sensitive name of the ScanCode.io project.",
            )
        ],
        responses={
            HTTP_204_NO_CONTENT: None,
            HTTP_400_BAD_REQUEST: OpenApiResponse(
                description="Invalid or non-matching confirmation name, or ScanCode.io refused the deletion."
            ),
            HTTP_403_FORBIDDEN: OpenApiResponse(description="Product edit permission is required."),
        },
    )
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        scancodeio_project = self.get_object()

        _check_feature_enabled()

        confirmation_names = request.query_params.getlist("name")
        if confirmation_names != [scancodeio_project.project_name]:
            raise ValidationError({"name": "Confirmation name must match the project name."})

        delete_scancodeio_project(scancodeio_project)
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={200: ScanCodeIOProjectDetailsSerializer},
    )
    @action(detail=True, methods=["get"])
    def details(self, request: Request, pk: int) -> Response:  # pylint: disable=unused-argument
        scancodeio_project = self.get_object()

        _check_feature_enabled()

        details = get_scancodeio_project_details(scancodeio_project)
        return Response(ScanCodeIOProjectDetailsSerializer(details).data)


class ScanCodeIOPipelinesView(APIView):
    @extend_schema(
        request=None,
        responses={200: ScanCodeIOPipelineSerializer(many=True)},
    )
    def get(self, request: Request) -> Response:
        _check_feature_enabled()

        return Response(ScanCodeIOPipelineSerializer(get_scancodeio_pipelines(), many=True).data)


class ScanCodeIOWebhookView(APIView):
    # ScanCode.io sends webhooks without authentication, the secret token in the URL identifies the project
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=None,
        responses={HTTP_200_OK: None, HTTP_400_BAD_REQUEST: None, HTTP_404_NOT_FOUND: None},
    )
    def post(self, request: Request, token: str) -> Response:
        scancodeio_project = get_scancodeio_project_by_webhook_token_hash(hash_webhook_token(token))
        if not scancodeio_project:
            return Response(status=HTTP_404_NOT_FOUND)

        _check_feature_enabled()

        payload = request.data if isinstance(request.data, dict) else {}
        project = payload.get("project")
        project_uuid = project.get("uuid") if isinstance(project, dict) else None
        if project_uuid != str(scancodeio_project.project_uuid):
            raise ValidationError("Webhook payload doesn't belong to the ScanCode.io project")

        process_scancodeio_webhook(scancodeio_project, payload)
        return Response(status=HTTP_200_OK)
