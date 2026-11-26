from application.access_control.models import (
    Authorization_Group,
    Authorization_Group_Member,
    User,
)
from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)


class TestAuthorizationAuthorizationGroups(TestAuthorizationBase):
    def test_authorization_authorization_groups(self):
        prepare_authorization_groups()

        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 4, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': False, 'name': 'db_group_internal_write', 'oidc_group': ''}, {'id': 5, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': False, 'name': 'db_group_internal_read', 'oidc_group': ''}, {'id': 6, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': False, 'name': 'db_group_external', 'oidc_group': ''}, {'id': 7, 'has_product_group_members': True, 'has_product_members': False, 'has_users': True, 'is_manager': False, 'name': 'db_group_product_group', 'oidc_group': ''}, {'id': 8, 'has_product_group_members': False, 'has_product_members': False, 'has_users': False, 'is_manager': False, 'name': 'db_group_unused', 'oidc_group': ''}]}"
        self._test_api(
            APITest(
                "db_admin",
                "get",
                "/api/authorization_groups/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 4, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': True, 'name': 'db_group_internal_write', 'oidc_group': ''}]}"
        expected_data_product_group = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 7, 'has_product_group_members': True, 'has_product_members': False, 'has_users': True, 'is_manager': False, 'name': 'db_group_product_group', 'oidc_group': ''}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/authorization_groups/",
                None,
                200,
                expected_data,
                expected_data_product_group=expected_data_product_group,
            )
        )
        expected_data = "{'id': 4, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': True, 'name': 'db_group_internal_write', 'oidc_group': ''}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/authorization_groups/4/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )
        expected_data = "{'message': 'No Authorization_Group matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/authorization_groups/99999/",
                None,
                404,
                expected_data,
            )
        )

        expected_data = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 6, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': False, 'name': 'db_group_external', 'oidc_group': ''}]}"
        self._test_api(
            APITest(
                "db_external",
                "get",
                "/api/authorization_groups/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'id': 6, 'has_product_group_members': False, 'has_product_members': True, 'has_users': True, 'is_manager': False, 'name': 'db_group_external', 'oidc_group': ''}"
        self._test_api(
            APITest(
                "db_external",
                "get",
                "/api/authorization_groups/6/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'message': 'No Authorization_Group matches the given query.'}"
        self._test_api(
            APITest(
                "db_external",
                "get",
                "/api/authorization_groups/4/",
                None,
                404,
                expected_data,
            )
        )

        expected_data = "{'id': 9, 'has_product_group_members': False, 'has_product_members': False, 'has_users': False, 'is_manager': False, 'name': 'string', 'oidc_group': 'oidc'}"
        self._test_api(
            APITest(
                "db_admin",
                "post",
                "/api/authorization_groups/",
                {
                    "name": "string",
                    "oidc_group": "oidc",
                },
                201,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 10, 'has_product_group_members': False, 'has_product_members': False, 'has_users': True, 'is_manager': True, 'name': 'string_2', 'oidc_group': 'oidc'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/authorization_groups/",
                {
                    "name": "string_2",
                    "oidc_group": "oidc",
                },
                201,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_external",
                "post",
                "/api/authorization_groups/",
                {
                    "name": "string_3",
                    "oidc_group": "oidc",
                },
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 9, 'has_product_group_members': False, 'has_product_members': False, 'has_users': False, 'is_manager': False, 'name': 'changed_string', 'oidc_group': 'oidc'}"
        self._test_api(
            APITest(
                "db_admin",
                "patch",
                "/api/authorization_groups/9/",
                {"name": "changed_string"},
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 10, 'has_product_group_members': False, 'has_product_members': False, 'has_users': True, 'is_manager': True, 'name': 'changed_string_2', 'oidc_group': 'oidc'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/authorization_groups/10/",
                {"name": "changed_string_2"},
                200,
                expected_data,
                no_second_user=True,
            )
        )

        Authorization_Group_Member.objects.create(
            authorization_group=Authorization_Group.objects.get(id=10),
            user=User.objects.get(username="db_internal_read"),
            is_manager=False,
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/authorization_groups/10/",
                {"name": "changed_string_2"},
                403,
                expected_data,
                no_second_user=True,
            )
        )

        self._test_api(
            APITest(
                "db_internal_read",
                "delete",
                "/api/authorization_groups/10/",
                None,
                403,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = None

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/authorization_groups/10/",
                None,
                204,
                expected_data,
                no_second_user=True,
            )
        )

    def test_authorization_authorization_group_names(self):
        prepare_authorization_groups()

        expected_data = "{'count': 5, 'next': None, 'previous': None, 'results': [{'id': 4, 'name': 'db_group_internal_write'}, {'id': 5, 'name': 'db_group_internal_read'}, {'id': 6, 'name': 'db_group_external'}, {'id': 7, 'name': 'db_group_product_group'}, {'id': 8, 'name': 'db_group_unused'}]}"
        self._test_api(APITest("db_admin", "get", "/api/authorization_group_names/", None, 200, expected_data))

        expected_data = (
            "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 6, 'name': 'db_group_external'}]}"
        )
        self._test_api(APITest("db_external", "get", "/api/authorization_group_names/", None, 200, expected_data))

        expected_data = "{'id': 6, 'name': 'db_group_external'}"
        self._test_api(APITest("db_external", "get", "/api/authorization_group_names/6/", None, 200, expected_data))

        expected_data = "{'message': 'No Authorization_Group matches the given query.'}"
        self._test_api(APITest("db_external", "get", "/api/authorization_group_names/4/", None, 404, expected_data))
