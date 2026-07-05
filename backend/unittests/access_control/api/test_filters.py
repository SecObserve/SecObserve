from django.test import TestCase

from application.access_control.api.filters import AuthorizationGroupFilter, UserFilter
from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Product,
    Product_Authorization_Group_Member,
    Product_Member,
)


class TestApproverFilters(TestCase):
    def setUp(self) -> None:
        self.product_group = Product.objects.create(name="group", is_product_group=True)
        self.product = Product.objects.create(name="product", product_group=self.product_group)

        self.reader = User.objects.create(username="reader@example.com")
        self.writer = User.objects.create(username="writer@example.com")
        self.inherited_writer = User.objects.create(username="inherited_writer@example.com")

        Product_Member.objects.all().delete()

        Product_Member.objects.create(product=self.product, user=self.reader, role=Roles.Reader)
        Product_Member.objects.create(product=self.product, user=self.writer, role=Roles.Writer)
        Product_Member.objects.create(product=self.product_group, user=self.inherited_writer, role=Roles.Writer)

        self.reader_group = Authorization_Group.objects.create(name="reader_group")
        self.writer_group = Authorization_Group.objects.create(name="writer_group")
        self.inherited_writer_group = Authorization_Group.objects.create(name="inherited_writer_group")
        Authorization_Group_Member.objects.create(authorization_group=self.reader_group, user=self.reader)
        Authorization_Group_Member.objects.create(authorization_group=self.writer_group, user=self.writer)
        Authorization_Group_Member.objects.create(
            authorization_group=self.inherited_writer_group, user=self.inherited_writer
        )
        Product_Authorization_Group_Member.objects.create(
            product=self.product, authorization_group=self.reader_group, role=Roles.Reader
        )
        Product_Authorization_Group_Member.objects.create(
            product=self.product, authorization_group=self.writer_group, role=Roles.Writer
        )
        Product_Authorization_Group_Member.objects.create(
            product=self.product_group, authorization_group=self.inherited_writer_group, role=Roles.Writer
        )

    def test_user_assessment_approver_filter_returns_approval_capable_members(self) -> None:
        user_filter = UserFilter(
            data={"assessment_approver_for_product": self.product.pk},
            queryset=User.objects.all(),
        )

        self.assertEqual(
            {"writer@example.com", "inherited_writer@example.com"},
            set(user_filter.qs.values_list("username", flat=True)),
        )

    def test_authorization_group_assessment_approver_filter_returns_approval_capable_groups(self) -> None:
        group_filter = AuthorizationGroupFilter(
            data={"assessment_approver_for_product": self.product.pk},
            queryset=Authorization_Group.objects.all(),
        )

        self.assertEqual(
            {"writer_group", "inherited_writer_group"},
            set(group_filter.qs.values_list("name", flat=True)),
        )
