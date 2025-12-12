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
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from rest_framework.viewsets import GenericViewSet

from application.notifications.api.filters import NotificationFilter
from application.notifications.api.permissions import UserHasNotificationPermission
from application.notifications.api.serializers import (
    NotificationBulkSerializer,
    NotificationSerializer,
)
from application.notifications.models import Notification, Notification_Viewed
from application.notifications.queries.notification import (
    get_notification_by_id,
    get_notifications,
)
from application.notifications.services.notification import bulk_mark_as_viewed


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
        request=None,
        responses={HTTP_204_NO_CONTENT: None},
    )
    @action(detail=True, methods=["post"])
    def mark_as_viewed(self, request: Request, pk: int) -> Response:
        if not get_notification_by_id(pk):
            return Response(status=HTTP_404_NOT_FOUND)

        Notification_Viewed.objects.update_or_create(
            notification_id=pk,
            user=request.user,
        )
        return Response(status=HTTP_204_NO_CONTENT)
