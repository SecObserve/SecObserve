import environ
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from application.commons.api.permissions import UserHasSuperuserPermission
from application.commons.api.serializers import (
    SettingsSerializer,
    StatusSettingsSerializer,
    VersionSerializer,
)
from application.commons.models import Settings


class VersionView(APIView):
    serializer_class = VersionSerializer

    @action(detail=True, methods=["get"], url_name="version")
    def get(self, request: Request) -> Response:
        content = {
            "version": "version_unknown",
        }
        return Response(content)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []
    serializer_class = None

    @action(detail=True, methods=["get"], url_name="health")
    def get(self, request: Request) -> Response:
        response = Response()
        response["Cache-Control"] = "no-cache, no-store, must-revalidate"

        return response


class StatusSettingsView(APIView):
    serializer_class = StatusSettingsSerializer
    permission_classes = []

    @action(detail=True, methods=["get"], url_name="settings")
    def get(self, request: Request) -> Response:  # pylint: disable=too-many-branches
        # There are quite a lot of branches, but at least they are not nested too much
        features = []

        settings = Settings.load()
        if settings.feature_disable_user_login:
            features.append("feature_disable_user_login")

        if request.user.is_authenticated:
            if settings.feature_vex:
                features.append("feature_vex")
            if settings.feature_general_rules_need_approval:
                features.append("feature_general_rules_need_approval")
            if settings.feature_license_management:
                features.append("feature_license_management")
            if settings.feature_automatic_api_import:
                features.append("feature_automatic_api_import")
            if settings.feature_automatic_osv_scanning:
                features.append("feature_automatic_osv_scanning")
            if settings.feature_automatic_vulnerablecode_scanning:
                features.append("feature_automatic_vulnerablecode_scanning")
            if settings.vulnerablecode_base_url:
                features.append("vulnerablecode_base_url_is_set")
            if settings.feature_exploit_information:
                features.append("feature_exploit_information")
            if settings.feature_show_product_header_chips:
                features.append("feature_show_product_header_chips")

            env = environ.Env()
            if env("EMAIL_HOST", default="") or env("EMAIL_PORT", default=""):
                features.append("feature_email")

        content: dict[str, (int | list[str]) | str] = {
            "features": features,
        }

        if request.user.is_authenticated:
            content["risk_acceptance_expiry_days"] = settings.risk_acceptance_expiry_days
            content["vex_justification_style"] = settings.vex_justification_style

        return Response(content)


class SettingsView(APIView):
    serializer_class = SettingsSerializer
    permission_classes = (IsAuthenticated, UserHasSuperuserPermission)

    @action(detail=True, methods=["get"], url_name="settings")
    def get(self, request: Request, pk: int = None) -> Response:  # pylint: disable=unused-argument
        # pk is needed for the API signature but we don't need it
        settings = Settings.load()
        response_serializer = SettingsSerializer(settings)
        return Response(response_serializer.data)

    @action(detail=True, methods=["patch"], url_name="settings")
    def patch(self, request: Request, pk: int = None) -> Response:  # pylint: disable=unused-argument
        # pk is needed for the API signature but we don't need it
        request_serializer = SettingsSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        if request_serializer.validated_data.get("feature_automatic_osv_scanning"):
            request_serializer.validated_data["feature_license_management"] = True

        settings = Settings.load()
        request_serializer.update(settings, request_serializer.validated_data)

        response_serializer = SettingsSerializer(settings)
        return Response(response_serializer.data)
