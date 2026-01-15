from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationProductMembers(TestAuthorizationBase):
    def test_authorization_product_members(self):
        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 1, 'user_data': {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 5, 'product': 1, 'user': 2}, {'id': 2, 'user_data': {'id': 3, 'username': 'db_internal_read', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_read', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:25:06+01:00', 'has_password': False}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 1, 'product': 1, 'user': 3}, {'id': 3, 'user_data': {'id': 4, 'username': 'db_external', 'first_name': '', 'last_name': '', 'full_name': 'db_external', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': True, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-12T19:48:08.514000+01:00', 'has_password': False}, 'product_data': {'id': 2, 'name': 'db_product_external', 'is_product_group': False}, 'role': 5, 'product': 2, 'user': 4}, {'id': 4, 'user_data': {'id': 3, 'username': 'db_internal_read', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_read', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:25:06+01:00', 'has_password': False}, 'product_data': {'id': 2, 'name': 'db_product_external', 'is_product_group': False}, 'role': 1, 'product': 2, 'user': 3}, {'id': 6, 'user_data': {'id': 6, 'username': 'db_product_group_user', 'first_name': '', 'last_name': '', 'full_name': 'db_product_group_user', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-04T11:09:18.495000+01:00', 'has_password': True}, 'product_data': {'id': 3, 'name': 'db_product_group', 'is_product_group': True}, 'role': 5, 'product': 3, 'user': 6}]}"
        self._test_api(APITest("db_admin", "get", "/api/product_members/", None, 200, expected_data))

        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'user_data': {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 5, 'product': 1, 'user': 2}, {'id': 2, 'user_data': {'id': 3, 'username': 'db_internal_read', 'full_name': 'db_internal_read'}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 1, 'product': 1, 'user': 3}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_members/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1, 'user_data': {'id': 2, 'username': 'db_internal_write', 'full_name': 'db_internal_write'}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 5, 'product': 1, 'user': 2}, {'id': 2, 'user_data': {'id': 3, 'username': 'db_internal_read', 'full_name': 'db_internal_read'}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 1, 'product': 1, 'user': 3}, {'id': 6, 'user_data': {'id': 6, 'username': 'db_product_group_user', 'first_name': '', 'last_name': '', 'full_name': 'db_product_group_user', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-04T11:09:18.495000+01:00', 'has_password': True}, 'product_data': {'id': 3, 'name': 'db_product_group', 'is_product_group': True}, 'role': 5, 'product': 3, 'user': 6}]}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "get",
                "/api/product_members/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'id': 1, 'user_data': {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_list_properties': '', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 5, 'product': 1, 'user': 2}"
        expected_data_product_group = "{'id': 1, 'user_data': {'id': 2, 'username': 'db_internal_write', 'full_name': 'db_internal_write'}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 5, 'product': 1, 'user': 2}"
        self._test_api(
            APITest(
                username="db_internal_write",
                method="get",
                url="/api/product_members/1/",
                post_data=None,
                expected_status_code=200,
                expected_data=expected_data,
                no_second_user=False,
                expected_data_product_group=expected_data_product_group,
            )
        )

        expected_data = "{'message': 'No Product_Member matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_members/3/",
                None,
                404,
                expected_data,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/product_members/99999/",
                None,
                404,
                expected_data,
            )
        )

        post_data = {"role": 3, "product": 1, "user": 1}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/product_members/",
                post_data,
                403,
                expected_data,
            )
        )
        expected_data = "{'id': 7, 'user_data': {'id': 1, 'username': 'db_admin', 'full_name': 'db_admin'}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 3, 'product': 1, 'user': 1}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/product_members/",
                post_data,
                201,
                expected_data,
            )
        )

        post_data = {"role": 2}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/product_members/7/",
                post_data,
                403,
                expected_data,
            )
        )

        expected_data = "{'id': 7, 'user_data': {'id': 1, 'username': 'db_admin', 'full_name': 'db_admin'}, 'product_data': {'id': 1, 'name': 'db_product_internal', 'is_product_group': False}, 'role': 2, 'product': 1, 'user': 1}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/product_members/7/",
                post_data,
                200,
                expected_data,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "delete",
                "/api/product_members/7/",
                None,
                403,
                expected_data,
            )
        )
        expected_data = "None"
        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/product_members/7/",
                None,
                204,
                expected_data,
            )
        )
