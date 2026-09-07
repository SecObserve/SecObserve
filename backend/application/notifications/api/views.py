from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import (
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet

from application.access_control.models import User
from application.authorization.services.authorization import user_has_permission_or_403
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Product
from application.core.queries.product import get_product_by_id
from application.notifications.api.filters import NotificationFilter
from application.notifications.api.permissions import (
    UserHasNotificationPermission,
    UserHasProductNotificationPermission,
)
from application.notifications.api.serializers import (
    NotificationBulkSerializer,
    NotificationSerializer,
    ProductNotificationPairSerializer,
    ProductNotificationSerializer,
    WebhookTestSerializer,
)
from application.notifications.models import (
    Notification,
    Notification_Viewed,
    Product_Notification,
)
from application.notifications.queries.notification import get_notifications
from application.notifications.queries.product_notification import (
    get_product_notifications,
)
from application.notifications.services.notification import bulk_mark_as_viewed
from application.notifications.services.product_notification import (
    create_product_notification_override,
    delete_product_notification_override,
    get_or_create_template,
    get_parent_notification,
    get_product_notification,
    is_product_api_token_user,
)
from application.notifications.services.send_notifications_base import (
    send_msteams_notification_test,
    send_slack_notification_test,
)


class NotificationViewSet(GenericViewSet, DestroyModelMixin, ListModelMixin, RetrieveModelMixin):
    serializer_class = NotificationSerializer
    filterset_class = NotificationFilter
    permission_classes = (IsAuthenticated, UserHasNotificationPermission)
    queryset = Notification.objects.all()
    filter_backends = [SearchFilter, DjangoFilterBackend]
    search_fields = ["name"]

    def get_queryset(self) -> QuerySet[Notification]:
        return (
            get_notifications()
            .select_related("product")
            .select_related("observation")
            .select_related("observation__product")
            .select_related("user")
        )

    @extend_schema(
        methods=["POST"],
        request=NotificationBulkSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=["post"])
    def bulk_mark_as_viewed(self, request: Request) -> Response:
        request_serializer = NotificationBulkSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        bulk_mark_as_viewed(request_serializer.validated_data.get("notifications"))

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=WebhookTestSerializer,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=False, methods=["post"])
    def test_webhook(self, request: Request) -> Response:
        request_serializer = WebhookTestSerializer(data=request.data)
        if not request_serializer.is_valid():
            raise ValidationError(request_serializer.errors)

        webhook_url = request_serializer.validated_data["webhook_url"]
        webhook_type = request_serializer.validated_data["webhook_type"]

        try:
            if webhook_type == "msteams":
                send_msteams_notification_test(webhook_url)
            else:
                send_slack_notification_test(webhook_url)
        except Exception as e:
            raise ValidationError(f"Failed to send test notification: {str(e)}") from e

        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def mark_as_viewed(self, request: Request, pk: int) -> Response:  # pylint: disable=unused-argument
        # pk is needed in the signature
        notification = self.get_object()

        user = request.user if isinstance(request.user, User) else None

        Notification_Viewed.objects.update_or_create(
            notification_id=notification.pk,
            user=user,
        )
        return Response(status=HTTP_204_NO_CONTENT)


class ProductNotificationViewSet(GenericViewSet, RetrieveModelMixin, UpdateModelMixin):
    serializer_class = ProductNotificationSerializer
    permission_classes = (IsAuthenticated, UserHasProductNotificationPermission)
    queryset = Product_Notification.objects.none()

    def get_queryset(self) -> QuerySet[Product_Notification]:
        return get_product_notifications().select_related("product").select_related("user")

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: ProductNotificationSerializer},
    )
    @action(detail=False, methods=["get"])
    def template(self, request: Request) -> Response:
        user = _get_notification_user(request)

        product_notification = get_or_create_template(user)

        return Response(status=HTTP_200_OK, data=ProductNotificationSerializer(product_notification).data)

    @extend_schema(
        methods=["GET"],
        request=None,
        responses={HTTP_200_OK: ProductNotificationPairSerializer},
        parameters=[
            OpenApiParameter(name="product", location=OpenApiParameter.QUERY, required=True, type=int),
        ],
    )
    @action(detail=False, methods=["get"])
    def for_product(self, request: Request) -> Response:
        user, product = _get_notification_user_and_product(request)

        # Products and product groups alike only have settings while the user overrides their parent
        product_notification = get_product_notification(product, user)
        parent_notification = get_parent_notification(product, user)

        data = {
            "product_notification": (
                ProductNotificationSerializer(product_notification).data if product_notification else None
            ),
            "parent_notification": ProductNotificationSerializer(parent_notification).data,
        }

        return Response(status=HTTP_200_OK, data=data)

    @extend_schema(
        methods=["POST"],
        request=None,
        responses={HTTP_200_OK: ProductNotificationSerializer},
        parameters=[
            OpenApiParameter(name="product", location=OpenApiParameter.QUERY, required=True, type=int),
        ],
    )
    @extend_schema(
        methods=["DELETE"],
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
        parameters=[
            OpenApiParameter(name="product", location=OpenApiParameter.QUERY, required=True, type=int),
        ],
    )
    @action(detail=False, methods=["post", "delete"])
    def override(self, request: Request) -> Response:
        user, product = _get_notification_user_and_product(request)

        if request.method == "DELETE":
            delete_product_notification_override(product, user)
            return Response(status=HTTP_204_NO_CONTENT)

        product_notification = create_product_notification_override(product, user)

        return Response(status=HTTP_200_OK, data=ProductNotificationSerializer(product_notification).data)


def _get_notification_user_and_product(request: Request) -> tuple[User, Product]:
    user = _get_notification_user(request)

    product_id = str(request.query_params.get("product", ""))
    if not product_id:
        raise ValidationError("No product id provided")
    if not product_id.isdigit():
        raise ValidationError("Product id is not an integer")

    product = get_product_by_id(int(product_id))
    if not product:
        raise NotFound()

    user_has_permission_or_403(product, Permissions.Product_View)

    return user, product


def _get_notification_user(request: Request) -> User:
    user = request.user if isinstance(request.user, User) else None
    if not user:
        raise PermissionDenied()

    # Users for product API tokens must never have notification settings
    if is_product_api_token_user(user):
        raise PermissionDenied("Product API tokens do not have notification settings")

    return user
