from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)


class TestAuthorizationBranches(TestAuthorizationBase):
    def test_authorization_branches_product_member(self):
        self._test_authorization_branches()

    def _test_authorization_branches_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_branches()

    def _test_authorization_branches(self):
        expected_data = "{'count': 3, 'next': None, 'previous': None, 'results': [{'id': 1, 'name_with_product': 'db_branch_internal_dev (db_product_internal)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'db_branch_internal_dev', 'is_default_branch': True, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}, {'id': 2, 'name_with_product': 'db_branch_internal_main (db_product_internal)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'db_branch_internal_main', 'is_default_branch': False, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}, {'id': 3, 'name_with_product': 'db_branch_external (db_product_external)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'db_branch_external', 'is_default_branch': True, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 2}]}"
        self._test_api(APITest("db_admin", "get", "/api/branches/", None, 200, expected_data))

        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'name_with_product': 'db_branch_internal_dev (db_product_internal)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'db_branch_internal_dev', 'is_default_branch': True, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}, {'id': 2, 'name_with_product': 'db_branch_internal_main (db_product_internal)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'db_branch_internal_main', 'is_default_branch': False, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/branches/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'id': 1, 'name_with_product': 'db_branch_internal_dev (db_product_internal)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'db_branch_internal_dev', 'is_default_branch': True, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/branches/1/",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'message': 'No Branch matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/branches/3/",
                None,
                404,
                expected_data,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/branches/99999/",
                None,
                404,
                expected_data,
            )
        )

        post_data = {"name": "string", "product": 1}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/branches/",
                post_data,
                403,
                expected_data,
            )
        )

        expected_data = "{'id': 4, 'name_with_product': 'string (db_product_internal)', 'name': 'string', 'is_default_branch': False, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/branches/",
                post_data,
                201,
                expected_data,
            )
        )

        post_data = {"name": "changed"}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/branches/1/",
                post_data,
                403,
                expected_data,
            )
        )

        expected_data = "{'id': 1, 'name_with_product': 'changed (db_product_internal)', 'open_critical_observation_count': 0, 'open_high_observation_count': 0, 'open_medium_observation_count': 0, 'open_low_observation_count': 0, 'open_none_observation_count': 0, 'open_unknown_observation_count': 0, 'forbidden_licenses_count': 0, 'review_required_licenses_count': 0, 'unknown_licenses_count': 0, 'allowed_licenses_count': 0, 'ignored_licenses_count': 0, 'name': 'changed', 'is_default_branch': True, 'last_import': None, 'housekeeping_protect': False, 'purl': '', 'cpe23': '', 'osv_linux_distribution': '', 'osv_linux_release': '', 'product': 1}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/branches/1/",
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
                "/api/branches/1/",
                None,
                403,
                expected_data,
            )
        )

        expected_data = "{'message': 'You cannot delete the default branch of a product.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/branches/1/",
                None,
                400,
                expected_data,
            )
        )
