from unittest.mock import patch

from django.core.management import call_command

from application.access_control.models import Authorization_Group, User
from application.core.models import Product, Product_Authorization_Group_Member
from application.notifications.models import Product_Notification
from application.notifications.services.housekeeping import (
    delete_orphaned_product_notifications,
)
from unittests.base_test_case import BaseTestCase


class TestDeleteOrphanedProductNotifications(BaseTestCase):
    patch.TEST_PREFIX = (
        "test",
        "setUp",
    )

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def test_empty_table(self):
        self.assertEqual(0, delete_orphaned_product_notifications())

    def test_row_of_a_member_survives(self):
        # db_internal_write is a member of product 1
        user = User.objects.get(username="db_internal_write")
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_row_of_a_non_member_is_deleted(self):
        # db_internal_write is not a member of product 2
        user = User.objects.get(username="db_internal_write")
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=2))

        self.assertEqual(1, delete_orphaned_product_notifications())
        self.assertFalse(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_template_is_never_deleted(self):
        # db_admin is a member of nothing, the template must survive anyway
        template = Product_Notification.objects.create(user=User.objects.get(username="db_admin"))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=template.pk).exists())

    def test_product_group_member_keeps_the_row(self):
        # db_product_group_user is a member of product group 3, which product 1 belongs to
        user = User.objects.get(username="db_product_group_user")
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_row_of_a_product_group_member_survives(self):
        # db_product_group_user is a member of product group 3, their settings for it are in the fixtures
        user = User.objects.get(username="db_product_group_user")
        product_notification = Product_Notification.objects.get(user=user, product=Product.objects.get(pk=3))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_row_of_a_product_group_survives_for_a_member_of_its_product(self):
        # db_internal_write is a member of product 1, which belongs to product group 3. The settings
        # of the product group are inherited by product 1, so they must not be deleted.
        user = User.objects.get(username="db_internal_write")
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_row_of_a_product_group_without_any_membership_is_deleted(self):
        # db_external is a member of product 2, which does not belong to a product group
        user = User.objects.get(username="db_external")
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3))

        self.assertEqual(1, delete_orphaned_product_notifications())
        self.assertFalse(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_authorization_group_member_keeps_the_row(self):
        user = User.objects.get(username="db_external")
        authorization_group = Authorization_Group.objects.create(name="housekeeping_group")
        authorization_group.users.add(user)
        Product_Authorization_Group_Member.objects.create(
            product=Product.objects.get(pk=1),
            authorization_group=authorization_group,
            role=1,
        )
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_authorization_group_of_the_product_group_keeps_the_row(self):
        user = User.objects.get(username="db_external")
        authorization_group = Authorization_Group.objects.create(name="housekeeping_group_group")
        authorization_group.users.add(user)
        # product group 3 is the product group of product 1
        Product_Authorization_Group_Member.objects.create(
            product=Product.objects.get(pk=3),
            authorization_group=authorization_group,
            role=1,
        )
        product_notification = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1))

        self.assertEqual(0, delete_orphaned_product_notifications())
        self.assertTrue(Product_Notification.objects.filter(pk=product_notification.pk).exists())

    def test_counts_and_deletes_only_the_orphans(self):
        user = User.objects.get(username="db_internal_write")
        template = Product_Notification.objects.create(user=user)
        kept = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=1))
        orphaned = Product_Notification.objects.create(user=user, product=Product.objects.get(pk=2))
        # db_external is a member of product 2 but not of product 1
        other_user = User.objects.get(username="db_external")
        other_orphaned = Product_Notification.objects.create(user=other_user, product=Product.objects.get(pk=1))

        self.assertEqual(2, delete_orphaned_product_notifications())

        self.assertTrue(Product_Notification.objects.filter(pk=template.pk).exists())
        self.assertTrue(Product_Notification.objects.filter(pk=kept.pk).exists())
        self.assertFalse(Product_Notification.objects.filter(pk=orphaned.pk).exists())
        self.assertFalse(Product_Notification.objects.filter(pk=other_orphaned.pk).exists())
