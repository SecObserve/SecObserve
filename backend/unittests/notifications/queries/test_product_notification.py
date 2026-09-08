from unittest.mock import patch

from django.core.management import call_command

from application.access_control.models import User
from application.core.models import Product
from application.notifications.models import Product_Notification
from application.notifications.queries.product_notification import (
    get_product_notification_by_id,
    get_product_notifications,
)
from unittests.base_test_case import BaseTestCase


class TestGetProductNotifications(BaseTestCase):
    """
    get_product_notifications() resolves the current user itself and again through get_products(),
    which imports it in application.core.queries.product, so both have to be patched.
    """

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

    def _get_product_names(self, product_notifications):
        return set(product_notifications.values_list("product__name", flat=True))

    # --- No user ---

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_no_user(self, mock_user, mock_products_user):
        mock_user.return_value = None
        mock_products_user.return_value = None

        self.assertEqual(0, len(get_product_notifications()))

    # --- The query does not create anything ---

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_query_does_not_create_rows(self, mock_user, mock_products_user):
        # db_internal_write is a member of db_product_internal, but reading must not materialize
        user = User.objects.get(username="db_internal_write")
        mock_user.return_value = user
        mock_products_user.return_value = user

        self.assertEqual(0, len(get_product_notifications()))
        self.assertFalse(Product_Notification.objects.exists())

    # --- Scoping ---

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_own_rows_are_visible(self, mock_user, mock_products_user):
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user)
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_internal"))
        mock_user.return_value = user
        mock_products_user.return_value = user

        self.assertEqual({None, "db_product_internal"}, self._get_product_names(get_product_notifications()))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_superuser_sees_all_rows(self, mock_user, mock_products_user):
        internal_write = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=internal_write)
        Product_Notification.objects.create(
            user=internal_write, product=Product.objects.get(name="db_product_internal")
        )
        admin = User.objects.get(username="db_admin")
        Product_Notification.objects.create(user=admin)
        mock_user.return_value = admin
        mock_products_user.return_value = admin

        product_notifications = get_product_notifications()

        self.assertEqual(
            {"db_admin", "db_internal_write"}, set(product_notifications.values_list("user__username", flat=True))
        )

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_other_users_rows_are_not_visible(self, mock_user, mock_products_user):
        Product_Notification.objects.create(user=User.objects.get(username="db_internal_read"))
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user)
        mock_user.return_value = user
        mock_products_user.return_value = user

        product_notifications = get_product_notifications()

        self.assertEqual({"db_internal_write"}, set(product_notifications.values_list("user__username", flat=True)))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_row_of_inaccessible_product_is_hidden(self, mock_user, mock_products_user):
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user)
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_internal"))
        # db_internal_write is not a member of db_product_external
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_external"))
        mock_user.return_value = user
        mock_products_user.return_value = user

        self.assertEqual({None, "db_product_internal"}, self._get_product_names(get_product_notifications()))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_row_of_product_group_is_visible_for_a_member(self, mock_user, mock_products_user):
        # db_product_group_user is a member of db_product_group, which db_product_internal belongs to
        user = User.objects.get(username="db_product_group_user")
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_group"))
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_internal"))
        mock_user.return_value = user
        mock_products_user.return_value = user

        self.assertEqual(
            {"db_product_group", "db_product_internal"}, self._get_product_names(get_product_notifications())
        )

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_row_of_product_group_is_hidden_for_a_member_of_its_product(self, mock_user, mock_products_user):
        # db_internal_write is a member of db_product_internal, but not of its product group, so
        # the settings of the product group are not visible for them
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_group"))
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_internal"))
        mock_user.return_value = user
        mock_products_user.return_value = user

        self.assertEqual({"db_product_internal"}, self._get_product_names(get_product_notifications()))

    @patch("application.core.queries.product.get_current_user")
    @patch("application.notifications.queries.product_notification.get_current_user")
    def test_row_of_inaccessible_product_group_is_hidden(self, mock_user, mock_products_user):
        # db_external is a member of db_product_external, which has no product group
        user = User.objects.get(username="db_external")
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_group"))
        Product_Notification.objects.create(user=user, product=Product.objects.get(name="db_product_external"))
        mock_user.return_value = user
        mock_products_user.return_value = user

        self.assertEqual({"db_product_external"}, self._get_product_names(get_product_notifications()))


class TestGetProductNotificationById(BaseTestCase):
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

    def test_existing(self):
        product_notification = Product_Notification.objects.create(user=User.objects.get(username="db_internal_write"))

        self.assertEqual(product_notification, get_product_notification_by_id(product_notification.pk))

    def test_not_existing(self):
        self.assertIsNone(get_product_notification_by_id(99999))
