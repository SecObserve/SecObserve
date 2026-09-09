from unittest.mock import patch

from django.core.management import call_command
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from rest_framework.test import APIClient

from application.access_control.models import User
from application.access_control.queries.user import get_user_by_username
from application.core.models import Product
from application.notifications.models import Notification_Viewed, Product_Notification
from unittests.base_test_case import BaseTestCase


class TestViews(BaseTestCase):
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_bulk_mark_as_viewed_no_list(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/bulk_mark_as_viewed/")

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({"message": "Notifications: This field is required."}, response.data)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_bulk_mark_as_viewed_successful(self, mock_authentication):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        # mock_authentication.return_value = self.user_internal, None
        user = get_user_by_username("db_internal_write")
        mock_authentication.return_value = user, None

        data = {"notifications": [3, 5]}
        api_client = APIClient()
        response = api_client.post("/api/notifications/bulk_mark_as_viewed/", data=data, format="json")

        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)

        notification_viewed = Notification_Viewed.objects.get(notification_id=3, user=user)
        self.assertIsNotNone(notification_viewed)

        notification_viewed = Notification_Viewed.objects.get(notification_id=5, user=user)
        self.assertIsNotNone(notification_viewed)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_mark_as_viewed_not_found(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/99999/mark_as_viewed/")

        self.assertEqual(HTTP_404_NOT_FOUND, response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_mark_as_viewed_not_found_for_user(self, mock_authentication):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        user = User.objects.get(username="db_internal_write")
        mock_authentication.return_value = user, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/2/mark_as_viewed/")

        self.assertEqual(HTTP_404_NOT_FOUND, response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_notification_mark_as_viewed_successful(self, mock_authentication):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        user = User.objects.get(username="db_internal_write")
        mock_authentication.return_value = user, None

        api_client = APIClient()
        response = api_client.post("/api/notifications/3/mark_as_viewed/")

        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)

        notification_viewed = Notification_Viewed.objects.get(notification_id=3, user=user)
        self.assertIsNotNone(notification_viewed)


class TestProductNotificationViews(BaseTestCase):
    """
    The notification settings of products are created on demand: they are never listed or created
    through the regular routes, but by the template, for_product and override actions.
    """

    def _authenticate(self, mock_authentication, username: str) -> User:
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")

        user = User.objects.get(username=username)
        mock_authentication.return_value = user, None

        return user

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_template(self, mock_authentication):
        user = self._authenticate(mock_authentication, "db_internal_write")
        self.assertFalse(Product_Notification.objects.filter(user=user).exists())

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/template/")

        self.assertEqual(HTTP_200_OK, response.status_code)

        # the template has been created on the fly
        self.assertEqual(1, Product_Notification.objects.filter(user=user, product__isnull=True).count())

        # reading it again returns the same row instead of creating another one
        response = api_client.get("/api/product_notifications/template/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(1, Product_Notification.objects.filter(user=user, product__isnull=True).count())

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_creates_nothing_but_the_template(self, mock_authentication):
        # product 1 belongs to product group 3, neither of them is overridden
        user = self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/?product=1")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(1, Product_Notification.objects.filter(user=user).count())
        self.assertIsNone(Product_Notification.objects.get(user=user).product)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_without_product(self, mock_authentication):
        self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/")

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({"message": "No product id provided"}, response.data)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_with_invalid_product(self, mock_authentication):
        self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/?product=abc")

        self.assertEqual(HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual({"message": "Product id is not an integer"}, response.data)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_with_unknown_product(self, mock_authentication):
        self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/?product=99999")

        self.assertEqual(HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual({"message": "Not found."}, response.data)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_without_permission(self, mock_authentication):
        # db_internal_write is not a member of db_product_external
        user = self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/?product=2")

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Product_Notification.objects.filter(user=user).exists())

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_with_product_group(self, mock_authentication):
        user = self._authenticate(mock_authentication, "db_product_group_user")
        # the product group is overridden in the fixtures already
        Product_Notification.objects.filter(user=user).delete()

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/?product=3")

        self.assertEqual(HTTP_200_OK, response.status_code)

        # a product group is only created by an override, reading it creates the template only
        self.assertFalse(Product_Notification.objects.filter(user=user, product=3).exists())
        self.assertTrue(Product_Notification.objects.filter(user=user, product__isnull=True).exists())

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_for_product_with_product_group_without_permission(self, mock_authentication):
        # db_internal_write is a member of product 1, but not of its product group 3
        user = self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.get("/api/product_notifications/for_product/?product=3")

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Product_Notification.objects.filter(user=user).exists())

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_override_ignores_invisible_product_group_settings(self, mock_authentication):
        # db_internal_write is a member of db_product_internal, but not of its product group, so
        # their settings for the product group must not be inherited
        user = self._authenticate(mock_authentication, "db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), observation_new_changed=True)

        api_client = APIClient()
        response = api_client.post("/api/product_notifications/override/?product=1")

        self.assertEqual(HTTP_200_OK, response.status_code)

        product_notification = Product_Notification.objects.get(user=user, product=1)
        self.assertTrue(product_notification.security_gate_changed)
        self.assertFalse(product_notification.observation_new_changed)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_override_inherits_the_visible_product_group_settings(self, mock_authentication):
        # db_product_group_user is an owner of the product group of db_product_internal, so the
        # very same settings are inherited here
        user = self._authenticate(mock_authentication, "db_product_group_user")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        product_group_notification = Product_Notification.objects.get(user=user, product=3)
        product_group_notification.observation_new_changed = True
        product_group_notification.save()

        api_client = APIClient()
        response = api_client.post("/api/product_notifications/override/?product=1")

        self.assertEqual(HTTP_200_OK, response.status_code)

        product_notification = Product_Notification.objects.get(user=user, product=1)
        self.assertFalse(product_notification.security_gate_changed)
        self.assertTrue(product_notification.observation_new_changed)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_override_creates_and_deletes_the_settings_of_the_product(self, mock_authentication):
        user = self._authenticate(mock_authentication, "db_internal_write")
        Product_Notification.objects.create(user=user, observation_to_be_reviewed=True)

        api_client = APIClient()
        response = api_client.post("/api/product_notifications/override/?product=1")

        self.assertEqual(HTTP_200_OK, response.status_code)

        # the product group is not overridden, so the settings of the product come from the template
        product_notification = Product_Notification.objects.get(user=user, product=1)
        self.assertTrue(product_notification.observation_to_be_reviewed)
        self.assertFalse(Product_Notification.objects.filter(user=user, product=3).exists())

        response = api_client.delete("/api/product_notifications/override/?product=1")

        self.assertEqual(HTTP_204_NO_CONTENT, response.status_code)

        # the product inherits from the template again, which is kept
        self.assertFalse(Product_Notification.objects.filter(user=user, product=1).exists())
        self.assertTrue(Product_Notification.objects.filter(user=user, product__isnull=True).exists())

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_override_with_product_group(self, mock_authentication):
        # a product group overrides the template, just like a product overrides its parent
        user = self._authenticate(mock_authentication, "db_product_group_user")
        # the product group is overridden in the fixtures already
        Product_Notification.objects.filter(user=user, product=3).delete()
        Product_Notification.objects.create(user=user, assessment_to_be_reviewed=True)

        api_client = APIClient()
        response = api_client.post("/api/product_notifications/override/?product=3")

        self.assertEqual(HTTP_200_OK, response.status_code)

        product_group_notification = Product_Notification.objects.get(user=user, product=3)
        self.assertTrue(product_group_notification.assessment_to_be_reviewed)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_override_without_permission(self, mock_authentication):
        # db_internal_write is not a member of db_product_external
        user = self._authenticate(mock_authentication, "db_internal_write")

        api_client = APIClient()
        response = api_client.post("/api/product_notifications/override/?product=2")

        self.assertEqual(HTTP_403_FORBIDDEN, response.status_code)
        self.assertFalse(Product_Notification.objects.filter(user=user).exists())
