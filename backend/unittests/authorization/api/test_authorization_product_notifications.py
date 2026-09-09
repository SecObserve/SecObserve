from application.notifications.models import Product_Notification
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationProductNotifications(TestAuthorizationBase):
    def test_authorization_product_notifications(self):
        expected_data = "{'count': 4, 'next': None, 'previous': None, 'results': [{'id': 1, 'product_data': None, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': None, 'user': 3}, {'id': 3, 'product_data': {'id': 2, 'name': 'db_product_external', 'is_product_group': False}, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': 2, 'user': 3}, {'id': 4, 'product_data': {'id': 3, 'name': 'db_product_group', 'is_product_group': True}, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': 3, 'user': 6}, {'id': 2, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': 1, 'user': 3}]}"
        self._test_api(APITest("db_admin", "get", "/api/product_notifications/", None, 200, expected_data))

        # db_internal_read is a member of db_product_internal and db_product_external, the settings
        # of db_product_group_user are not visible for them
        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1, 'product_data': None, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': None, 'user': 3}, {'id': 3, 'product_data': {'id': 2, 'name': 'db_product_external', 'is_product_group': False}, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': 2, 'user': 3}, {'id': 2, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': 1, 'user': 3}]}"
        self._test_api(
            APITest(
                "db_internal_read",
                "get",
                "/api/product_notifications/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        # db_product_group_user only has settings for the product group
        expected_data = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 4, 'product_data': {'id': 3, 'name': 'db_product_group', 'is_product_group': True}, 'security_gate_changed': False, 'observation_new_changed': False, 'observation_to_be_reviewed': False, 'assessment_to_be_reviewed': False, 'product_rule_to_be_reviewed': False, 'product': 3, 'user': 6}]}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "get",
                "/api/product_notifications/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        # Users can change their own notification settings, including the template
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/product_notifications/2/",
                {"security_gate_changed": True},
                200,
                None,
                no_second_user=True,
            )
        )
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/product_notifications/1/",
                {"observation_new_changed": True},
                200,
                None,
                no_second_user=True,
            )
        )

        product_notification = Product_Notification.objects.get(pk=2)
        template = Product_Notification.objects.get(pk=1)
        self.assertTrue(product_notification.security_gate_changed)
        self.assertTrue(template.observation_new_changed)

        # Members of a product group can change its notification settings
        self._test_api(
            APITest(
                "db_product_group_user",
                "patch",
                "/api/product_notifications/4/",
                {"security_gate_changed": True},
                200,
                None,
                no_second_user=True,
            )
        )
        self.assertTrue(Product_Notification.objects.get(pk=4).security_gate_changed)

        # product and user are read only
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/product_notifications/2/",
                {"product": 2, "user": 2},
                200,
                None,
                no_second_user=True,
            )
        )
        product_notification = Product_Notification.objects.get(pk=2)
        self.assertEqual(1, product_notification.product_id)
        self.assertEqual(3, product_notification.user_id)

        # Other users cannot change the notification settings, they are not even visible for them
        expected_data = "{'message': 'No Product_Notification matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/product_notifications/2/",
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
                "/api/product_notifications/2/",
                {"security_gate_changed": False},
                403,
                expected_data,
                no_second_user=True,
            )
        )
        self.assertTrue(Product_Notification.objects.get(pk=2).security_gate_changed)

        # Rows are created by the override action, not through the list route
        expected_data = "{'message': 'Method \"POST\" not allowed.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/product_notifications/",
                {"product": 1},
                405,
                expected_data,
            )
        )

        # Rows are read through the list and for_product, the detail route only accepts changes
        expected_data = "{'message': 'Method \"GET\" not allowed.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "get",
                "/api/product_notifications/2/",
                None,
                405,
                expected_data,
            )
        )

        # Rows are deleted through the override action, not through the detail route
        expected_data = "{'message': 'Method \"DELETE\" not allowed.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "delete",
                "/api/product_notifications/2/",
                None,
                405,
                expected_data,
            )
        )
