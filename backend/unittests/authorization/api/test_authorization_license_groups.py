from unittest.mock import patch

from application.licenses.models import License_Group, License_Policy
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationLicenseGroups(TestAuthorizationBase):
    def test_authorization_license_groups(self):
        License_Policy.objects.all().delete()
        License_Group.objects.filter(pk__lt=1000).delete()

        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 1000, 'name': 'public', 'description': '', 'is_public': True}, {'id': 1001, 'name': 'internal_read_not_manager', 'description': '', 'is_public': False}, {'id': 1002, 'name': 'internal_write_manager', 'description': '', 'is_public': False}, {'id': 1003, 'name': 'authorization_group_not_manager', 'description': '', 'is_public': False}, {'id': 1004, 'name': 'authorization_group_manager', 'description': '', 'is_public': False}]}"
        self._test_api(APITest("db_admin", "get", "/api/license_groups/", None, 200, expected_data))

        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1000, 'name': 'public', 'description': '', 'is_public': True}, {'id': 1002, 'name': 'internal_write_manager', 'description': '', 'is_public': False}, {'id': 1003, 'name': 'authorization_group_not_manager', 'description': '', 'is_public': False}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_groups/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1000, 'name': 'public', 'description': '', 'is_public': True}, {'id': 1003, 'name': 'authorization_group_not_manager', 'description': '', 'is_public': False}, {'id': 1004, 'name': 'authorization_group_manager', 'description': '', 'is_public': False}]}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "get",
                "/api/license_groups/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1002, 'is_manager': True, 'is_in_license_policy': False, 'has_licenses': True, 'has_users': True, 'has_authorization_groups': False, 'name': 'internal_write_manager', 'description': '', 'is_public': False}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_groups/1002/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )
        expected_data = "{'message': 'No License_Group matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_groups/1001/",
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
                "/api/license_groups/99999/",
                None,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"name": "new_license_group"}
        expected_data = "{'id': 1005, 'is_manager': True, 'is_in_license_policy': False, 'has_licenses': False, 'has_users': True, 'has_authorization_groups': False, 'name': 'new_license_group', 'description': '', 'is_public': False}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/",
                post_data,
                201,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"name": "new_license_group_external"}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_external",
                "post",
                "/api/license_groups/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1002, 'is_manager': True, 'is_in_license_policy': False, 'has_licenses': True, 'has_users': True, 'has_authorization_groups': False, 'name': 'internal_write_manager', 'description': 'changed', 'is_public': False}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/license_groups/1002/",
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
                "/api/license_groups/1000/",
                {"description": "changed"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1004, 'is_manager': True, 'is_in_license_policy': False, 'has_licenses': False, 'has_users': False, 'has_authorization_groups': True, 'name': 'authorization_group_manager', 'description': 'changed', 'is_public': False}"
        self._test_api(
            APITest(
                "db_product_group_user",
                "patch",
                "/api/license_groups/1004/",
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
                "/api/license_groups/1003/",
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
                "/api/license_groups/1001/",
                {"description": "changed"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"name": "copied_license_group"}
        expected_data = "{'id': 1006, 'is_manager': True, 'is_in_license_policy': False, 'has_licenses': True, 'has_users': True, 'has_authorization_groups': False, 'name': 'copied_license_group', 'description': 'changed', 'is_public': False}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/1002/copy/",
                post_data,
                201,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'License group not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/1001/copy/",
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
                "/api/license_groups/1001/copy/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"license": 10}
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/1002/add_license/",
                post_data,
                204,
                None,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'License group not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/1001/add_license/",
                post_data,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You are not a manager of this license group'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/license_groups/1001/add_license/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        post_data = {"license": 10}
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/1002/remove_license/",
                post_data,
                204,
                None,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'License group not found'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_groups/1001/remove_license/",
                post_data,
                404,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You are not a manager of this license group'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/license_groups/1001/remove_license/",
                post_data,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/license_groups/1002/",
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
                "/api/license_groups/1000/",
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
                "/api/license_groups/1001/",
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
                "/api/license_groups/1004/",
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
                "/api/license_groups/1003/",
                None,
                403,
                None,
                no_second_user=True,
            )
        )
