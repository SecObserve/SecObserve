from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.access_control.models import User
from application.authorization.api.permissions_base import check_object_permission
from application.authorization.services.roles_permissions import Permissions
from application.notifications.models import Notification, Notification_Recipient


class UserHasNotificationPermission(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if obj.type in (Notification.TYPE_ASSESSMENT_REQUEST, Notification.TYPE_ASSESSMENT_RESULT):
            if not isinstance(request.user, User):
                return False
            if request.user.is_superuser:
                return True

            is_recipient = Notification_Recipient.objects.filter(notification=obj, user=request.user).exists()
            if request.method == "DELETE":
                return bool(
                    is_recipient
                    and obj.product
                    and check_object_permission(
                        request=request,
                        object_to_check=obj.product,
                        get_permission=Permissions.Product_View,
                        put_permission=None,
                        delete_permission=Permissions.Product_Delete,
                    )
                )
            return is_recipient

        if obj.product:
            return check_object_permission(
                request=request,
                object_to_check=obj.product,
                get_permission=Permissions.Product_View,
                put_permission=None,
                delete_permission=Permissions.Product_Delete,
            )

        if request.user and request.user.is_superuser:
            return True

        return False
