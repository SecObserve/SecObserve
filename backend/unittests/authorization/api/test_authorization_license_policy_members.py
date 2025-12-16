from application.licenses.models import License_Policy
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationLicensePolicyMembers(TestAuthorizationBase):
    def test_authorization_license_policy_members(self):
        License_Policy.objects.filter(pk__lt=1000).delete()

        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1001, 'license_policy_data': {'id': 1001, 'parent_name': '', 'name': 'internal_read_not_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 3, 'username': 'db_internal_read', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_read', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'setting_list_properties': '', 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:25:06+01:00', 'has_password': False}, 'is_manager': False, 'license_policy': 1001, 'user': 3}, {'id': 1002, 'license_policy_data': {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'setting_list_properties': '', 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, 'is_manager': True, 'license_policy': 1002, 'user': 2}, {'id': 1003, 'license_policy_data': {'id': 1001, 'parent_name': '', 'name': 'internal_read_not_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 4, 'username': 'db_external', 'first_name': '', 'last_name': '', 'full_name': 'db_external', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': True, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'permissions': [], 'setting_list_properties': '', 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-12T19:48:08.514000+01:00', 'has_password': False}, 'is_manager': False, 'license_policy': 1001, 'user': 4}]}"
        self._test_api(
            APITest(
                "db_admin",
                "get",
                "/api/license_policy_members/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 1002, 'license_policy_data': {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'setting_list_properties': '', 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, 'is_manager': True, 'license_policy': 1002, 'user': 2}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policy_members/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1002, 'license_policy_data': {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 2, 'username': 'db_internal_write', 'first_name': '', 'last_name': '', 'full_name': 'db_internal_write', 'email': '', 'is_active': True, 'is_superuser': False, 'is_external': False, 'setting_theme': 'light', 'setting_list_size': 'medium', 'setting_package_info_preference': 'open/source/insights', 'permissions': [<Permissions.Product_Create: 1104>, <Permissions.Product_Group_Create: 1004>], 'setting_list_properties': '', 'oidc_groups_hash': '', 'is_oidc_user': False, 'date_joined': '2022-12-07T20:24:53+01:00', 'has_password': False}, 'is_manager': True, 'license_policy': 1002, 'user': 2}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policy_members/1002/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )
        expected_data = "{'message': 'No License_Policy_Member matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policy_members/1001/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policy_members/99999/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"license_policy": 1002, "user": 6, "is_manager": False}
        expected_data = "{'id': 1004, 'license_policy_data': {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 6, 'username': 'db_product_group_user', 'full_name': 'db_product_group_user'}, 'is_manager': False, 'license_policy': 1002, 'user': 6}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policy_members/",
                post_data,
                201,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"license_policy": 1000, "user": 6, "is_manager": False}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policy_members/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"license_policy": 1001, "user": 6, "is_manager": False}
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/license_policy_members/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1004, 'license_policy_data': {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, 'user_data': {'id': 6, 'username': 'db_product_group_user', 'full_name': 'db_product_group_user'}, 'is_manager': True, 'license_policy': 1002, 'user': 6}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/license_policy_members/1004/",
                {"is_manager": "True"},
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/license_policy_members/1001/",
                {"is_manager": "True"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/license_policy_members/1004/",
                None,
                204,
                None,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_read",
                "delete",
                "/api/license_policy_members/1001/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )
