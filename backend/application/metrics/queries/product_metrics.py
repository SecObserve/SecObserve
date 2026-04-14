from django.db.models import Exists, OuterRef, Q
from django.db.models.query import QuerySet
from django.utils import timezone

from application.access_control.services.current_user import get_current_user
from application.core.models import Product_Authorization_Group_Member, Product_Member
from application.metrics.models import Product_Metrics


def get_product_metrics() -> QuerySet[Product_Metrics]:
    user = get_current_user()

    if user is None:
        return Product_Metrics.objects.none()

    product_metrics = Product_Metrics.objects.all().order_by("id")

    if not user.is_superuser:
        product_members = Product_Member.objects.filter(product=OuterRef("product_id"), user=user)
        product_group_members = Product_Member.objects.filter(product=OuterRef("product__product_group"), user=user)

        product_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product_id"),
            authorization_group__users=user,
        )

        product_group_authorization_group_members = Product_Authorization_Group_Member.objects.filter(
            product=OuterRef("product__product_group"),
            authorization_group__users=user,
        )

        product_metrics = product_metrics.annotate(
            product__member=Exists(product_members),
            product__product_group__member=Exists(product_group_members),
            authorization_group_member=Exists(product_authorization_group_members),
            product_group_authorization_group_member=Exists(product_group_authorization_group_members),
        )

        product_metrics = product_metrics.filter(
            Q(product__is_product_group=False)
            & (
                (Q(product__member=True) | Q(product__product_group__member=True))
                | Q(authorization_group_member=True)
                | Q(product_group_authorization_group_member=True)
            )
        )

    return product_metrics


def get_todays_product_metrics() -> QuerySet[Product_Metrics]:
    return get_product_metrics().filter(date=timezone.localdate())
