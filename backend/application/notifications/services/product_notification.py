from typing import Optional

from django.db import transaction

from application.access_control.models import User
from application.core.models import Product
from application.notifications.models import Product_Notification

NOTIFICATION_FIELDS = (
    "security_gate_changed",
    "observation_new_changed",
    "observation_to_be_reviewed",
    "assessment_to_be_reviewed",
    "product_rule_to_be_reviewed",
)

PRODUCT_API_TOKEN_USER_PREFIX = "-product-"


def is_product_api_token_user(user: User) -> bool:
    return user.username.startswith(PRODUCT_API_TOKEN_USER_PREFIX)


def get_or_create_template(user: User) -> Product_Notification:
    """
    The template is the row without a product. It cannot be protected by the unique constraint,
    because MySQL and PostgreSQL treat NULLs as distinct in a unique index, so duplicates are
    read tolerantly instead of raising.
    """
    template = Product_Notification.objects.filter(product__isnull=True, user=user).order_by("id").first()
    if template:
        return template

    with transaction.atomic():
        return Product_Notification.objects.create(user=user)


def get_product_notification(product: Product, user: User) -> Optional[Product_Notification]:
    """
    The settings of a product or a product group, None while the user does not override them. Only
    the template always exists, everything below it is an override.
    """
    return Product_Notification.objects.filter(product=product, user=user).first()


def get_parent_notification(product: Product, user: User) -> Product_Notification:
    """
    The settings a product inherits from: the settings of its product group when the user overrides
    them, otherwise the user's template. A product group always inherits from the template.
    """
    if product.product_group:
        product_group_notification = get_product_notification(product.product_group, user)
        if product_group_notification:
            return product_group_notification

    return get_or_create_template(user)


def create_product_notification_override(product: Product, user: User) -> Product_Notification:
    """
    Lets the user override the settings a product or a product group inherits, by giving it settings
    of its own with the values of the parent. Idempotent: an existing override is returned unchanged.
    """
    product_notification = get_product_notification(product, user)
    if product_notification:
        return product_notification

    parent = get_parent_notification(product, user)
    parent_values = {field: getattr(parent, field) for field in NOTIFICATION_FIELDS}

    with transaction.atomic():
        # In contrast to the template, product and user are covered by the unique constraint
        product_notification, _ = Product_Notification.objects.get_or_create(
            product=product, user=user, defaults=parent_values
        )

    return product_notification


def delete_product_notification_override(product: Product, user: User) -> None:
    """
    Removes the settings of a product, so that it inherits from its parent again. Idempotent: it is
    no error if the user does not override the product.
    """
    Product_Notification.objects.filter(product=product, user=user).delete()
