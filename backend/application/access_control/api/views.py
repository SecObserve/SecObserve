import logging
from dataclasses import dataclass
from typing import Any

from django.contrib.auth import authenticate as django_authenticate
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.password_validation import (
    CommonPasswordValidator,
    MinimumLengthValidator,
    NumericPasswordValidator,
    UserAttributeSimilarityValidator,
    password_validators_help_texts,
    validate_password,
)
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import ListModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from application.access_control.api.filters import (
    ApiTokenFilter,
    AuthorizationGroupFilter,
    AuthorizationGroupMemberFilter,
    UserFilter,
)
from application.access_control.api.permissions import (
    UserHasAuthorizationGroupMemberPermission,
    UserHasAuthorizationGroupPermission,
    UserHasSuperuserPermission,
)
from application.access_control.api.serializers import (
    ApiTokenCreateRequestSerializer,
    ApiTokenCreateResponseSerializer,
    ApiTokenRevokeRequestSerializer,
    ApiTokenSerializer,
    AuthenticationRequestSerializer,
    AuthenticationResponseSerializer,
    AuthorizationGroupMemberSerializer,
    AuthorizationGroupSerializer,
    UserListSerializer,
    UserPasswordSerializer,
    UserPasswortRulesSerializer,
    UserSerializer,
    UserSettingsSerializer,
    UserUpdateSerializer,
)
from application.access_control.models import (
    API_Token_Multiple,
    Authorization_Group,
    Authorization_Group_Member,
    JWT_Secret,
    User,
)
from application.access_control.queries.api_token import get_api_tokens
from application.access_control.queries.authorization_group import (
    get_authorization_groups,
)
from application.access_control.queries.authorization_group_member import (
    get_authorization_group_members,
)
from application.access_control.queries.user import (
    get_users,
    get_users_without_api_tokens,
)
from application.access_control.services.jwt_authentication import create_jwt
from application.access_control.services.jwt_secret import create_secret
from application.access_control.services.user_api_token import (
    create_user_api_token,
    revoke_user_api_token,
)
from application.commons.models import Settings
from application.commons.services.log_message import format_log_message

logger = logging.getLogger("secobserve.access_control")


class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer
    filterset_class = UserFilter
    queryset = User.objects.none()
    permission_classes = (IsAuthenticated, UserHasSuperuserPermission)
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["full_name"]

    def get_queryset(self) -> QuerySet[User]:
        if self.action == "list":
            return get_users_without_api_tokens()

        return get_users()

    def get_serializer_class(self) -> type[BaseSerializer[Any]]:
        if self.action == "list":
            return UserListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return UserUpdateSerializer

        return super().get_serializer_class()

    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        instance: User = self.get_object()
        if instance == request.user:
            raise ValidationError("You cannot delete yourself")

        return super().destroy(request, *args, **kwargs)

    @extend_schema(methods=["GET"], responses={status.HTTP_200_OK: UserSerializer})
    @action(detail=False, methods=["get"])
    def me(self, request: Request) -> Response:
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["PATCH"],
        request=UserSettingsSerializer,
        responses={status.HTTP_200_OK: UserSerializer},
    )
    @action(detail=False, methods=["patch"])
    def my_settings(self, request: Request) -> Response:
        request_serializer = UserSettingsSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        setting_theme = request_serializer.validated_data.get("setting_theme")
        setting_list_size = request_serializer.validated_data.get("setting_list_size")
        setting_package_info_preference = request_serializer.validated_data.get("setting_package_info_preference")
        setting_list_properties = request_serializer.validated_data.get("setting_list_properties")
        setting_metrics_timespan = request_serializer.validated_data.get("setting_metrics_timespan")
        user = request.user
        if isinstance(user, AnonymousUser):
            raise PermissionDenied("You must be authenticated to change settings")

        if setting_theme:
            user.setting_theme = setting_theme
        if setting_list_size:
            user.setting_list_size = setting_list_size
        if setting_package_info_preference:
            user.setting_package_info_preference = setting_package_info_preference
        if setting_list_properties:
            user.setting_list_properties = setting_list_properties
        if setting_metrics_timespan:
            user.setting_metrics_timespan = setting_metrics_timespan
        user.save()

        response_serializer = UserSerializer(request.user)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        methods=["PATCH"],
        request=UserPasswordSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["patch"])
    def change_password(self, request: Request, pk: int = None) -> Response:  # pylint: disable=unused-argument
        # pk is not used, but it is required to match the action signature
        request_serializer = UserPasswordSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        instance: User = self.get_object()
        current_password = request_serializer.validated_data.get("current_password")
        new_password_1 = request_serializer.validated_data.get("new_password_1")
        new_password_2 = request_serializer.validated_data.get("new_password_2")

        if not request.user.is_superuser and request.user.pk != instance.pk:
            raise PermissionDenied("You are not allowed to change other users' passwords")

        if not instance.has_usable_password() or instance.is_oidc_user:
            raise ValidationError("User's password cannot be changed")

        if new_password_1 != new_password_2:
            raise ValidationError("The new passwords do not match")

        if not django_authenticate(
            username=request.user.username,
            password=current_password,
        ):
            raise ValidationError("Current password is incorrect")

        try:
            validate_password(new_password_1, instance, self._get_password_validators())
        except DjangoValidationError as e:
            raise ValidationError(e.messages)  # pylint: disable=raise-missing-from
            # The DjangoValidationError itself is not relevant and must not be re-raised

        instance.set_password(new_password_1)
        instance.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={status.HTTP_200_OK: UserPasswortRulesSerializer},
    )
    @action(detail=False, methods=["get"])
    def password_rules(self, request: Request) -> Response:

        @dataclass
        class PasswordRules:
            password_rules: str

        password_rules_list = password_validators_help_texts(self._get_password_validators())
        password_rules_list = [s.replace("Your password", "The password") for s in password_rules_list]
        password_rules = PasswordRules("- " + "\n- ".join(password_rules_list))
        response_serializer = UserPasswortRulesSerializer(password_rules)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _get_password_validators(self) -> list[Any]:
        validators: list[Any] = []
        settings = Settings.load()
        validators.append(MinimumLengthValidator(min_length=settings.password_validator_minimum_length))
        if settings.password_validator_common_passwords:
            validators.append(CommonPasswordValidator())
        if settings.password_validator_attribute_similarity:
            validators.append(UserAttributeSimilarityValidator())
        if settings.password_validator_not_numeric:
            validators.append(NumericPasswordValidator())

        return validators


class AuthorizationGroupViewSet(ModelViewSet):
    serializer_class = AuthorizationGroupSerializer
    filterset_class = AuthorizationGroupFilter
    queryset = Authorization_Group.objects.none()
    permission_classes = (IsAuthenticated, UserHasAuthorizationGroupPermission)
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Authorization_Group]:
        return get_authorization_groups()


class AuthorizationGroupMemberViewSet(ModelViewSet):
    serializer_class = AuthorizationGroupMemberSerializer
    filterset_class = AuthorizationGroupMemberFilter
    queryset = Authorization_Group_Member.objects.none()
    permission_classes = (IsAuthenticated, UserHasAuthorizationGroupMemberPermission)

    def get_queryset(self) -> QuerySet[Authorization_Group_Member]:
        return get_authorization_group_members()


class ApiTokenViewSet(ListModelMixin, GenericViewSet):
    serializer_class = ApiTokenSerializer
    filterset_class = ApiTokenFilter
    permission_classes = (IsAuthenticated,)
    queryset = API_Token_Multiple.objects.none()

    def get_queryset(self) -> QuerySet[API_Token_Multiple]:
        return get_api_tokens().select_related("user")


class UserAPITokenCreateView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=ApiTokenCreateRequestSerializer,
        responses={status.HTTP_201_CREATED: ApiTokenCreateResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        request_serializer = ApiTokenCreateRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        user = _get_authenticated_user(request_serializer.validated_data)
        name = request_serializer.validated_data.get("name")
        expiration_date = request_serializer.validated_data.get("expiration_date")

        try:
            token = create_user_api_token(user, name, expiration_date)
        except ValidationError as e:
            response = Response(status=status.HTTP_400_BAD_REQUEST)
            logger.warning(format_log_message(message=str(e), username=user.username, response=response))
            raise

        response = Response({"token": token}, status=status.HTTP_201_CREATED)
        logger.info(format_log_message(message="API token created", username=user.username, response=response))
        return response


class UserAPITokenRevokeView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=ApiTokenRevokeRequestSerializer,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request: Request) -> Response:
        request_serializer = ApiTokenRevokeRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        user = _get_authenticated_user(request_serializer.validated_data)
        name = request_serializer.validated_data.get("name")

        revoke_user_api_token(user, name)

        response = Response(status=status.HTTP_204_NO_CONTENT)
        logger.info(format_log_message(message="API token revoked", username=user.username, response=response))
        return response


class AuthenticateView(APIView):
    authentication_classes = []
    permission_classes = []

    @extend_schema(
        request=AuthenticationRequestSerializer,
        responses={status.HTTP_200_OK: AuthenticationResponseSerializer},
    )
    def post(self, request: Request) -> Response:
        user = _get_authenticated_user(request.data)

        jwt = create_jwt(user)

        user_serializer = UserSerializer(user)
        response = Response({"jwt": jwt, "user": user_serializer.data})
        logger.info(format_log_message(message="User authenticated", username=user.username, response=response))
        return response


class JWTSecretResetView(APIView):
    permission_classes = [IsAuthenticated, UserHasSuperuserPermission]

    @extend_schema(
        request=None,
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def post(self, request: Request) -> Response:
        jwt_secret = JWT_Secret(secret=create_secret())
        jwt_secret.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _get_authenticated_user(data: dict) -> User:
    username = data.get("username")
    password = data.get("password")

    user: User = django_authenticate(username=username, password=password)  # type: ignore[assignment]
    # We always get a User from our model
    if not user:
        raise PermissionDenied("Invalid credentials")

    return user
