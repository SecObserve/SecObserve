from application.core.models import Product
from application.licenses.models import License_Policy
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationLicensePolicies(TestAuthorizationBase):
    def test_authorization_license_policies(self):
        License_Policy.objects.filter(pk__lt=1000).delete()

        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 1000, 'parent_name': '', 'name': 'public', 'description': '', 'is_public': True, 'ignore_component_types': '', 'parent': None}, {'id': 1001, 'parent_name': '', 'name': 'internal_read_not_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, {'id': 1003, 'parent_name': '', 'name': 'authorization_group_not_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, {'id': 1004, 'parent_name': '', 'name': 'authorization_group_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}]}"
        self._test_api(APITest("db_admin", "get", "/api/license_policies/", None, 200, expected_data))

        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1000, 'parent_name': '', 'name': 'public', 'description': '', 'is_public': True, 'ignore_component_types': '', 'parent': None}, {'id': 1002, 'parent_name': '', 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, {'id': 1003, 'parent_name': '', 'name': 'authorization_group_not_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1000, 'parent_name': '', 'name': 'public', 'description': '', 'is_public': True, 'ignore_component_types': '', 'parent': None}, {'id': 1003, 'parent_name': '', 'name': 'authorization_group_not_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}, {'id': 1004, 'parent_name': '', 'name': 'authorization_group_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}]}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "get",
                "/api/license_policies/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1002, 'parent_name': '', 'is_parent': False, 'is_manager': True, 'has_products': False, 'has_product_groups': False, 'has_items': True, 'has_users': True, 'has_authorization_groups': False, 'name': 'internal_write_manager', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/1002/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/1002/export_json/",
                None,
                200,
                None,
                no_second_user=True,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/1002/export_yaml/",
                None,
                200,
                None,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'No License_Policy matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/1001/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )
        expected_data = "{'message': 'License policy not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/1001/export_json/",
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
                "/api/license_policies/1001/export_yaml/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'No License_Policy matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/99999/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )
        expected_data = "{'message': 'License policy not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_policies/99999/export_json/",
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
                "/api/license_policies/99999/export_yaml/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"name": "new_license_policy"}
        expected_data = "{'id': 1005, 'parent_name': '', 'is_parent': False, 'is_manager': True, 'has_products': False, 'has_product_groups': False, 'has_items': False, 'has_users': True, 'has_authorization_groups': False, 'name': 'new_license_policy', 'description': '', 'is_public': False, 'ignore_component_types': '', 'parent': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policies/",
                post_data,
                201,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"name": "new_license_policy_external"}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_external",
                "post",
                "/api/license_policies/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1002, 'parent_name': '', 'is_parent': False, 'is_manager': True, 'has_products': False, 'has_product_groups': False, 'has_items': True, 'has_users': True, 'has_authorization_groups': False, 'name': 'internal_write_manager', 'description': 'changed', 'is_public': False, 'ignore_component_types': '', 'parent': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/license_policies/1002/",
                {"description": "changed"},
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
                "/api/license_policies/1000/",
                {"description": "changed"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1004, 'parent_name': '', 'is_parent': False, 'is_manager': True, 'has_products': False, 'has_product_groups': False, 'has_items': True, 'has_users': False, 'has_authorization_groups': True, 'name': 'authorization_group_manager', 'description': 'changed', 'is_public': False, 'ignore_component_types': '', 'parent': None}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "patch",
                "/api/license_policies/1004/",
                {"description": "changed"},
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "patch",
                "/api/license_policies/1003/",
                {"description": "changed"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/license_policies/1001/",
                {"description": "changed"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"name": "copied_license_policy"}
        expected_data = "{'id': 1006, 'parent_name': '', 'is_parent': False, 'is_manager': True, 'has_products': False, 'has_product_groups': False, 'has_items': True, 'has_users': True, 'has_authorization_groups': False, 'name': 'copied_license_policy', 'description': 'changed', 'is_public': False, 'ignore_component_types': '', 'parent': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policies/1002/copy/",
                post_data,
                201,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'License policy not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policies/1001/copy/",
                post_data,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_external",
                "post",
                "/api/license_policies/1001/copy/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policies/1002/apply/",
                None,
                204,
                None,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'License policy not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policies/1001/apply/",
                None,
                404,
                None,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/license_policies/1001/apply/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )

        product_1 = Product.objects.get(pk=1)
        license_policy_1000 = License_Policy.objects.get(pk=1000)
        product_1.license_policy = license_policy_1000
        product_1.save()

        self._test_api(
            APITest(
                "db_admin",
                "post",
                "/api/license_policies/apply_product/?product=1",
                None,
                204,
                None,
                no_second_user=False,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_policies/apply_product/?product=1",
                None,
                204,
                None,
                no_second_user=False,
            )
        )

        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/license_policies/apply_product/?product=1",
                None,
                403,
                None,
                no_second_user=False,
            )
        )

        self._test_api(
            APITest(
                "db_external",
                "post",
                "/api/license_policies/apply_product/?product=1",
                None,
                403,
                None,
                no_second_user=False,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/license_policies/1002/",
                None,
                204,
                None,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/license_policies/1000/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_read",
                "delete",
                "/api/license_policies/1001/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_product_group_user",
                "delete",
                "/api/license_policies/1004/",
                None,
                204,
                None,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_product_group_user",
                "delete",
                "/api/license_policies/1003/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )
