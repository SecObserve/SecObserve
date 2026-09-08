from application.access_control.models import User
from application.core.models import Product
from application.notifications.models import Product_Notification
from application.notifications.services.product_notification import (
    create_product_notification_override,
)
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationProductNotifications(TestAuthorizationBase):
    def test_authorization_product_notifications(self):
        # db_internal_write is a member of db_product_internal, overriding the settings for it
        # creates the template as well. The product group is not overridden, so it has no settings.
        create_product_notification_override(
            Product.objects.get(name="db_product_internal"), User.objects.get(username="db_internal_write")
        )

        product_notifications = Product_Notification.objects.filter(user__username="db_internal_write").order_by("id")
        self.assertEqual(2, len(product_notifications))
        template = product_notifications[0]
        product_notification = product_notifications[1]
        self.assertIsNone(template.product)
        self.assertEqual("db_product_internal", product_notification.product.name)

        # Users can change their own notification settings, including the template
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                f"/api/product_notifications/{product_notification.pk}/",
                {"security_gate_changed": True},
                200,
                None,
                no_second_user=True,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                f"/api/product_notifications/{template.pk}/",
                {"observation_new_changed": True},
                200,
                None,
                no_second_user=True,
            )
        )

        product_notification.refresh_from_db()
        template.refresh_from_db()
        self.assertTrue(product_notification.security_gate_changed)
        self.assertTrue(template.observation_new_changed)

        # product and user are read only
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                f"/api/product_notifications/{product_notification.pk}/",
                {"product": 2, "user": 3},
                200,
                None,
                no_second_user=True,
            )
        )
        product_notification.refresh_from_db()
        self.assertEqual(1, product_notification.product_id)
        self.assertEqual(2, product_notification.user_id)

        # Other users cannot change the notification settings, they are not even visible for them
        expected_data = "{'message': 'No Product_Notification matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                f"/api/product_notifications/{product_notification.pk}/",
                {"security_gate_changed": False},
                404,
                expected_data,
                no_second_user=True,
            )
        )

        # Not even superusers can change the notification settings of somebody else
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_admin",
                "patch",
                f"/api/product_notifications/{product_notification.pk}/",
                {"security_gate_changed": False},
                403,
                expected_data,
                no_second_user=True,
            )
        )
        product_notification.refresh_from_db()
        self.assertTrue(product_notification.security_gate_changed)

        # There is no list endpoint, so the collection URL does not resolve at all
        # and there is no route to create rows either
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/",
                None,
                404,
                None,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/product_notifications/",
                {"product": 1},
                404,
                None,
            )
        )

        # Rows are read through for_product, the detail route only accepts changes
        expected_data = "{'message': 'Method \"GET\" not allowed.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                f"/api/product_notifications/{product_notification.pk}/",
                None,
                405,
                expected_data,
            )
        )

        # Rows are deleted through the override action, not through the detail route
        expected_data = "{'message': 'Method \"DELETE\" not allowed.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                f"/api/product_notifications/{product_notification.pk}/",
                None,
                405,
                expected_data,
            )
        )

    def test_authorization_product_group_notifications(self):
        # db_product_group_user is an owner of db_product_group
        product_group = Product.objects.get(name="db_product_group")
        product_group_notification = create_product_notification_override(
            product_group, User.objects.get(username="db_product_group_user")
        )

        # Members of the product group can change its notification settings
        self._test_api(
            APITest(
                "db_product_group_user",
                "patch",
                f"/api/product_notifications/{product_group_notification.pk}/",
                {"security_gate_changed": True},
                200,
                None,
                no_second_user=True,
            )
        )
        product_group_notification.refresh_from_db()
        self.assertTrue(product_group_notification.security_gate_changed)

        # db_internal_write is a member of db_product_internal, but not of its product group,
        # so the notification settings of the product group are not visible for them
        expected_data = "{'message': 'No Product_Notification matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                f"/api/product_notifications/{product_group_notification.pk}/",
                {"security_gate_changed": False},
                404,
                expected_data,
                no_second_user=True,
            )
        )


class TestAuthorizationProductNotificationsOnDemand(TestAuthorizationBase):
    def test_template(self):
        user = User.objects.get(username="db_internal_write")
        self.assertFalse(Product_Notification.objects.filter(user=user).exists())

        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/template/",
                None,
                200,
                None,
                no_second_user=True,
            )
        )

        # the template has been created on the fly
        templates = Product_Notification.objects.filter(user=user, product__isnull=True)
        self.assertEqual(1, len(templates))

        # reading it again returns the same row instead of creating another one
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/template/",
                None,
                200,
                None,
                no_second_user=True,
            )
        )
        self.assertEqual(1, Product_Notification.objects.filter(user=user, product__isnull=True).count())

    def test_for_product_creates_nothing_but_the_template(self):
        # product 1 belongs to product group 3, neither of them is overridden
        user = User.objects.get(username="db_internal_write")

        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/for_product/?product=1",
                None,
                200,
                None,
                no_second_user=True,
            )
        )

        self.assertEqual(1, Product_Notification.objects.filter(user=user).count())
        self.assertIsNone(Product_Notification.objects.get(user=user).product)

    def test_override_ignores_invisible_product_group_settings(self):
        # db_internal_write is a member of db_product_internal, but not of its product group, so
        # their settings for the product group must not be inherited
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), observation_new_changed=True)

        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/product_notifications/override/?product=1",
                {},
                200,
                None,
                no_second_user=True,
            )
        )

        product_notification = Product_Notification.objects.get(user=user, product=1)
        self.assertTrue(product_notification.security_gate_changed)
        self.assertFalse(product_notification.observation_new_changed)

    def test_override_inherits_the_visible_product_group_settings(self):
        # db_product_group_user is an owner of the product group of db_product_internal, so the
        # very same settings are inherited here
        user = User.objects.get(username="db_product_group_user")
        Product_Notification.objects.create(user=user, security_gate_changed=True)
        Product_Notification.objects.create(user=user, product=Product.objects.get(pk=3), observation_new_changed=True)

        self._test_api(
            APITest(
                "db_product_group_user",
                "post",
                "/api/product_notifications/override/?product=1",
                {},
                200,
                None,
                no_second_user=True,
            )
        )

        product_notification = Product_Notification.objects.get(user=user, product=1)
        self.assertFalse(product_notification.security_gate_changed)
        self.assertTrue(product_notification.observation_new_changed)

    def test_override_creates_and_deletes_the_settings_of_the_product(self):
        user = User.objects.get(username="db_internal_write")
        Product_Notification.objects.create(user=user, observation_to_be_reviewed=True)

        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/product_notifications/override/?product=1",
                {},
                200,
                None,
                no_second_user=True,
            )
        )

        # the product group is not overridden, so the settings of the product come from the template
        product_notification = Product_Notification.objects.get(user=user, product=1)
        self.assertTrue(product_notification.observation_to_be_reviewed)
        self.assertFalse(Product_Notification.objects.filter(user=user, product=3).exists())

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/product_notifications/override/?product=1",
                None,
                204,
                None,
                no_second_user=True,
            )
        )

        # the product inherits from the template again, which is kept
        self.assertFalse(Product_Notification.objects.filter(user=user, product=1).exists())
        self.assertTrue(Product_Notification.objects.filter(user=user, product__isnull=True).exists())

    def test_override_with_product_group(self):
        # a product group overrides the template, just like a product overrides its parent
        user = User.objects.get(username="db_product_group_user")
        Product_Notification.objects.create(user=user, assessment_to_be_reviewed=True)

        self._test_api(
            APITest(
                "db_product_group_user",
                "post",
                "/api/product_notifications/override/?product=3",
                {},
                200,
                None,
                no_second_user=True,
            )
        )

        product_group_notification = Product_Notification.objects.get(user=user, product=3)
        self.assertTrue(product_group_notification.assessment_to_be_reviewed)

    def test_override_without_permission(self):
        # db_internal_write is not a member of db_product_external
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/product_notifications/override/?product=2",
                {},
                403,
                expected_data,
                no_second_user=True,
            )
        )
        self.assertFalse(Product_Notification.objects.filter(user__username="db_internal_write").exists())

    def test_for_product_without_product(self):
        expected_data = "{'message': 'No product id provided'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/for_product/",
                None,
                400,
                expected_data,
                no_second_user=True,
            )
        )

    def test_for_product_with_invalid_product(self):
        expected_data = "{'message': 'Product id is not an integer'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/for_product/?product=abc",
                None,
                400,
                expected_data,
                no_second_user=True,
            )
        )

    def test_for_product_with_unknown_product(self):
        expected_data = "{'message': 'Not found.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/for_product/?product=99999",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )

    def test_for_product_with_product_group(self):
        user = User.objects.get(username="db_product_group_user")

        self._test_api(
            APITest(
                "db_product_group_user",
                "get",
                "/api/product_notifications/for_product/?product=3",
                None,
                200,
                None,
                no_second_user=True,
            )
        )

        # a product group is only created by an override, reading it creates the template only
        self.assertFalse(Product_Notification.objects.filter(user=user, product=3).exists())
        self.assertTrue(Product_Notification.objects.filter(user=user, product__isnull=True).exists())

    def test_for_product_with_product_group_without_permission(self):
        # db_internal_write is a member of product 1, but not of its product group 3
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/for_product/?product=3",
                None,
                403,
                expected_data,
                no_second_user=True,
            )
        )
        self.assertFalse(Product_Notification.objects.filter(user__username="db_internal_write").exists())

    def test_for_product_without_permission(self):
        # db_internal_write is not a member of db_product_external
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_notifications/for_product/?product=2",
                None,
                403,
                expected_data,
                no_second_user=True,
            )
        )
        self.assertFalse(Product_Notification.objects.filter(user__username="db_internal_write").exists())
