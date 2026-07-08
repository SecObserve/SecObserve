from typing import Optional

from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from application.access_control.models import User
from application.authorization.services.authorization import user_has_permission
from application.authorization.services.roles_permissions import Permissions
from application.core.models import Observation, Product, Product_Delete_Request
from application.core.types import Product_Delete_Request_Status
from application.licenses.models import License_Component
from application.notifications.services.send_notifications import (
    send_product_delete_request_notification,
)


def force_delete_product(product: Product, confirmation_name: str) -> None:
    _validate_confirmation_name(product, confirmation_name)

    with transaction.atomic():
        locked_product = Product.objects.select_for_update().get(pk=product.pk)
        if locked_product.is_product_group:
            child_products = Product.objects.select_for_update().filter(product_group=locked_product).order_by("id")
            for child_product in child_products:
                _force_delete_single_product(child_product)

        _force_delete_single_product(locked_product)


def request_product_delete(product: Product, user: User) -> Product_Delete_Request:
    if user_has_permission(product, _delete_permission(product), user):
        raise ValidationError("Owners can force delete directly and do not need to request deletion.")

    if not user_has_permission(product, _edit_permission(product), user):
        raise PermissionDenied()

    if get_pending_delete_request(product):
        raise ValidationError("A delete request is already pending.")

    delete_request = Product_Delete_Request.objects.create(product=product, user=user)
    send_product_delete_request_notification(delete_request)
    return delete_request


def approve_product_delete_request(product: Product, confirmation_name: str) -> None:
    if not get_pending_delete_request(product):
        raise ValidationError("No pending delete request exists.")

    force_delete_product(product, confirmation_name)


def reject_product_delete_request(product: Product) -> None:
    delete_request = get_pending_delete_request(product)
    if not delete_request:
        raise ValidationError("No pending delete request exists.")

    delete_request.delete()


def undo_product_delete_request(product: Product, user: User) -> None:
    delete_request = get_pending_delete_request(product)
    if not delete_request:
        raise ValidationError("No pending delete request exists.")

    if delete_request.user_id != user.id:
        raise PermissionDenied()

    delete_request.delete()


def get_pending_delete_request(product: Product) -> Optional[Product_Delete_Request]:
    return (
        Product_Delete_Request.objects.filter(
            product=product,
            status=Product_Delete_Request_Status.STATUS_PENDING,
        )
        .select_related("user")
        .first()
    )


def _force_delete_single_product(product: Product) -> None:
    if product.repository_default_branch_id:
        product.repository_default_branch = None
        product.save(update_fields=["repository_default_branch"])

    License_Component.objects.filter(product=product).delete()
    Observation.objects.filter(product=product).delete()
    Product_Delete_Request.objects.filter(product=product).delete()
    product.delete()


def _validate_confirmation_name(product: Product, confirmation_name: str) -> None:
    if confirmation_name.strip() != product.name:
        raise ValidationError({"confirmation_name": "Confirmation name must match the product name."})


def _delete_permission(product: Product) -> Permissions:
    if product.is_product_group:
        return Permissions.Product_Group_Delete
    return Permissions.Product_Delete


def _edit_permission(product: Product) -> Permissions:
    if product.is_product_group:
        return Permissions.Product_Group_Edit
    return Permissions.Product_Edit
