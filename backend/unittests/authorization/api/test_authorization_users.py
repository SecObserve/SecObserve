from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationUsers(TestAuthorizationBase):
    def test_authorization_users(self):
        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 1, 'username': 'db_admin', 'first_name': '', 'last_name': '', 'full_name': 'db_admin', 'email': '', 'is_active': True, 'is_superuser': True, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-04T11:09:18.495000+01:00', 'has_password': True}, {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, {'id': 3, 'username': 'db_internal_read', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_read', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:25:06+01:00', 'has_password': False}, {'id': 4, 'username': 'db_external', 'first_name': '', 'last_name': '', 'full_name': 'db_external', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': True, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-12T19:48:08.514000+01:00', 'has_password': False}, {'id': 6, 'username': 'db_product_group_user', 'first_name': '', 'last_name': '', 'full_name': 'db_product_group_user', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-04T11:09:18.495000+01:00', 'has_password': True}]}"
        self._test_api(APITest("db_admin", "get", "/api/users/", None, 200, expected_data))

        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 1, 'username': 'db_admin', 'full_name': 'db_admin'}, {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, {'id': 3, 'username': 'db_internal_read', 'full_name': 'db_internal_read'}, {'id': 4, 'username': 'db_external', 'full_name': 'db_external'}, {'id': 6, 'username': 'db_product_group_user', 'full_name': 'db_product_group_user'}]}"
        expected_data_product_group = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 1, 'username': 'db_admin', 'full_name': 'db_admin'}, {'id': 2, 'username': 'db_internal_write', 'full_name': 'db_internal_write'}, {'id': 3, 'username': 'db_internal_read', 'full_name': 'db_internal_read'}, {'id': 4, 'username': 'db_external', 'full_name': 'db_external'}, {'id': 6, 'username': 'db_product_group_user', 'first_name': '', 'last_name': '', 'full_name': 'db_product_group_user', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-04T11:09:18.495000+01:00', 'has_password': True}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/users/",
                None,
                200,
                expected_data,
                False,
                expected_data_product_group,
            )
        )

        expected_data = "{'id': 1, 'username': 'db_admin', 'full_name': 'db_admin'}"
        self._test_api(APITest("db_internal_write", "get", "/api/users/1/", None, 200, expected_data))

        expected_data = "{'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False, 'has_authorization_groups': True, 'has_product_group_members': False, 'has_product_members': True, 'has_api_tokens': False}"
        expected_data_product_group = "{'id': 2, 'username': 'db_internal_write', 'full_name': 'db_internal_write'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/users/2/",
                None,
                200,
                expected_data,
                False,
                expected_data_product_group,
            )
        )

        expected_data = "{'message': 'No User matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/users/99999/",
                None,
                404,
                expected_data,
            )
        )

        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 3, 'username': 'db_internal_read', 'full_name': 'db_internal_read'}, {'id': 4, 'username': 'db_external', 'first_name': '', 'last_name': '', 'full_name': 'db_external', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': True, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-12T19:48:08.514000+01:00', 'has_password': False}]}"
        self._test_api(APITest("db_external", "get", "/api/users/", None, 200, expected_data))
        expected_data = "{'id': 4, 'username': 'db_external', 'first_name': '', 'last_name': '', 'full_name': 'db_external', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': True, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-12T19:48:08.514000+01:00', 'has_password': False, 'has_authorization_groups': False, 'has_product_group_members': False, 'has_product_members': True, 'has_api_tokens': False}"
        self._test_api(APITest("db_external", "get", "/api/users/4/", None, 200, expected_data))
        expected_data = "{'id': 3, 'username': 'db_internal_read', 'full_name': 'db_internal_read'}"
        self._test_api(APITest("db_external", "get", "/api/users/3/", None, 200, expected_data))
        expected_data = "{'message': 'No User matches the given query.'}"
        self._test_api(APITest("db_external", "get", "/api/users/2/", None, 404, expected_data))

        expected_data = "{'id': 7, 'username': 'test_user', 'first_name': '', 'last_name': '', 'full_name': 'string', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False}"
        self._test_api(
            APITest(
                "db_admin",
                "post",
                "/api/users/",
                {
                    "username": "test_user",
                    "full_name": "string",
                },
                201,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/users/",
                {
                    "username": "test_user",
                    "full_name": "string",
                },
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 7, 'username': 'test_user', 'first_name': '', 'last_name': '', 'full_name': 'changed_string', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False}"
        self._test_api(
            APITest(
                "db_admin",
                "patch",
                "/api/users/7/",
                {"full_name": "changed_string"},
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/users/7/",
                {"full_name": "changed_string"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/users/7/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_admin",
                "delete",
                "/api/users/7/",
                None,
                204,
                None,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You cannot delete yourself'}"
        self._test_api(
            APITest(
                "db_admin",
                "delete",
                "/api/users/1/",
                None,
                400,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': \"You are not allowed to change other users' passwords\"}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/users/1/change_password/",
                {
                    "current_password": "current",
                    "new_password_1": "new",
                    "new_password_2": "new",
                },
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'Current password is incorrect'}"
        self._test_api(
            APITest(
                "db_admin",
                "patch",
                "/api/users/1/change_password/",
                {
                    "current_password": "current",
                    "new_password_1": "new",
                    "new_password_2": "new",
                },
                400,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False, 'has_authorization_groups': True, 'has_product_group_members': False, 'has_product_members': True, 'has_api_tokens': False}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/users/me/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {
            "setting_theme": "dark",
            "setting_list_size": "small",
            "setting_package_info_preference": "ecosyste.ms",
        }
        expected_data = "{'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'dark', 'setting_list_size': 'small', 'setting_package_info_preference': 'ecosyste.ms', 'setting_metrics_timespan': 'Week', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False, 'has_authorization_groups': True, 'has_product_group_members': False, 'has_product_members': True, 'has_api_tokens': False}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/users/my_settings/",
                post_data,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"setting_theme": "medium"}
        expected_data = "{'message': 'Setting theme: \"medium\" is not a valid choice.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/users/my_settings/",
                post_data,
                400,
                expected_data,
            )
        )
