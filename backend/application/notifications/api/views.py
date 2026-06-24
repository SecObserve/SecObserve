from django.db.models.query import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.mixins import DestroyModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT
from rest_framework.viewsets import GenericViewSet

from application.access_control.models import User
from application.notifications.api.filters import NotificationFilter
from application.notifications.api.permissions import UserHasNotificationPermission
from application.notifications.api.serializers import (
    NotificationBulkSerializer,
    NotificationSerializer,
    WebhookTestSerializer,
)
from application.notifications.models import Notification, Notification_Viewed
from application.notifications.queries.notification import get_notifications
from application.notifications.services.notification import bulk_mark_as_viewed
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
        ms_teams_v2_format = request_serializer.validated_data.get("ms_teams_v2_format", False)

        try:
            if webhook_type == "msteams":
                send_msteams_notification_test(webhook_url, ms_teams_v2_format)
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
