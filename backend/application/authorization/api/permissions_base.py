from typing import Any, Optional

from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ParseError
from rest_framework.request import Request

from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions


def check_post_permission(
    request: Request,
    post_model: Any,
    post_foreign_key: str,
    post_permission: Permissions,
) -> bool:
    if request.method == "POST":
        pk = request.data.get(post_foreign_key) if isinstance(request.data, dict) else None
        if pk is None:
            raise ParseError(f"Unable to check for permissions: Attribute '{post_foreign_key}' is required")
        object_to_check = get_object_or_404(post_model, pk=pk)
        return user_has_permission(object_to_check, post_permission)

    return True


def check_object_permission(
    *,
    request: Request,
    object_to_check: Any,
    get_permission: Optional[Permissions],
    put_permission: Optional[Permissions],
    delete_permission: Optional[Permissions],
    post_permission: Optional[Permissions] = None,
) -> bool:
    if request.method == "GET" and get_permission is not None:
        return user_has_permission(object_to_check, get_permission)

    if request.method in ("PUT", "PATCH") and put_permission is not None:
        return user_has_permission(object_to_check, put_permission)

    if request.method == "DELETE" and delete_permission is not None:
        return user_has_permission(object_to_check, delete_permission)

    if request.method == "POST" and post_permission is not None:
        return user_has_permission(object_to_check, post_permission)

    return False
