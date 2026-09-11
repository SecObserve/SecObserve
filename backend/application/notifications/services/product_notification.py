from typing import Optional

from django.db import transaction
from django.db.models import BooleanField, Exists, OuterRef, Q, Subquery, Value
from django.db.models.functions import Coalesce

from application.access_control.models import User
from application.core.models import (
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)
from application.notifications.models import Product_Notification
from application.notifications.queries.product_notification import (
    get_product_notifications,
)
from application.notifications.types import Product_Notification_Type

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
    return get_product_notifications().filter(product=product, user=user).first()


def get_template_notification(product: Product, user: User) -> Product_Notification:
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

    parent = get_template_notification(product, user)
    parent_values = {field: getattr(parent, field) for field in Product_Notification_Type.PRODUCT_NOTIFICATION_TYPES}

    with transaction.atomic():
        product_notification, _ = Product_Notification.objects.get_or_create(
            product=product, user=user, defaults=parent_values
        )

    return product_notification


def get_users_for_product_notification(product: Product, notification_type: str) -> set[User]:
    """
    The users who want to be notified about the given kind of event for the given product: the
    settings of the product win, otherwise the ones of its product group, otherwise the user's
    template. Users without any settings are never notified, the fields default to False.

    Only active members of the product with an email address are returned, users for product API
    tokens never are.
    """
    if notification_type not in Product_Notification_Type.PRODUCT_NOTIFICATION_TYPES:
        raise ValueError(f"{notification_type} is not a product notification type")

    product_ids = [product.pk]
    notification_subqueries = [_get_notification_subquery(product.pk, notification_type)]
    if product.product_group_id:
        product_ids.append(product.product_group_id)
        notification_subqueries.append(_get_notification_subquery(product.product_group_id, notification_type))
    notification_subqueries.append(_get_notification_subquery(None, notification_type))

    # product_ids contains the product group as well, so all membership paths are covered
    product_members = Product_Member.objects.filter(product_id__in=product_ids, user=OuterRef("pk"))
    product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
        product_id__in=product_ids,
        authorization_group__users=OuterRef("pk"),
    )

    return set(
        User.objects.filter(is_active=True)
        .exclude(username__startswith=PRODUCT_API_TOKEN_USER_PREFIX)
        .exclude(email="")
        .annotate(
            notification_enabled=Coalesce(*notification_subqueries, Value(False), output_field=BooleanField()),
            is_product_member=Exists(product_members),
            is_authorization_group_member=Exists(product_authorization_group_members),
        )
        .filter(notification_enabled=True)
        .filter(Q(is_product_member=True) | Q(is_authorization_group_member=True))
    )


def _get_notification_subquery(product_id: Optional[int], notification_type: str) -> Subquery:
    """
    The settings of one tier for the user of the outer query, None when they have none there. The
    template is not covered by the unique constraint, so the lowest id wins, the same way
    get_or_create_template() picks one when there are duplicates.
    """
    product_notifications = Product_Notification.objects.filter(user=OuterRef("pk"))
    if product_id is None:
        product_notifications = product_notifications.filter(product__isnull=True)
    else:
        product_notifications = product_notifications.filter(product_id=product_id)

    return Subquery(
        product_notifications.order_by("pk").values(notification_type)[:1],
        output_field=BooleanField(),
    )
