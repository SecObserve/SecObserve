from typing import Any

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from application.authorization.api.permissions_base import check_object_permission
from application.authorization.services.roles_permissions import Permissions
from application.notifications.models import Notification


class UserHasNotificationPermission(BasePermission):
    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if obj.product:
            get_permission = Permissions.Product_View
            if obj.type == Notification.TYPE_PRODUCT_DELETE_REQUEST:
                get_permission = (
                    Permissions.Product_Group_Delete if obj.product.is_product_group else Permissions.Product_Delete
                )

            return check_object_permission(
                request=request,
                object_to_check=obj.product,
                get_permission=get_permission,
                put_permission=None,
                delete_permission=Permissions.Product_Delete,
            )

        if request.user and request.user.is_superuser:
            return True

        return False
