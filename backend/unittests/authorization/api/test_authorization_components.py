from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)


class TestAuthorizationComponents(TestAuthorizationBase):
    def test_authorization_components_product_member(self):
        self._test_authorization_components()

    def test_authorization_components_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_components()

    def _test_authorization_components(self):
        # The superuser sees all components: with an observation and a license (1), with a license
        # only (2), without any observation or license (3) and with an observation only (4).
        # Components 1 and 2 have an inactive observation in addition.
        expected_data = "{'count': 4, 'next': None, 'previous': None, 'results': [{'id': 1, 'has_active_observations': True, 'has_inactive_observations': True, 'has_licenses': True, 'identity_hash': '3aac376e96aec05c7ac55d6e938228e2e983dff95801c63e0b93f13203a50345', 'name': 'internal_component', 'version': '1.0.0', 'name_version': 'internal_component:1.0.0', 'type': '', 'purl': '', 'purl_type': 'npm', 'purl_namespace': ''}, {'id': 2, 'has_active_observations': False, 'has_inactive_observations': True, 'has_licenses': True, 'identity_hash': '19de944bd2436a9bae5221bc32e079e1ecc2dbf9ee3954e398bec8ebf78bc3ab', 'name': 'external_component', 'version': '2.0.0', 'name_version': 'external_component:2.0.0', 'type': '', 'purl': '', 'purl_type': '', 'purl_namespace': ''}, {'id': 3, 'has_active_observations': False, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '4390291ad7af75eefca71dc2d03b9d72bcd5a7974a951c9285d47a79f69d37f4', 'name': 'unused_component', 'version': '3.0.0', 'name_version': 'unused_component:3.0.0', 'type': '', 'purl': '', 'purl_type': '', 'purl_namespace': ''}, {'id': 4, 'has_active_observations': True, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '04ded96e2cd9245aa36a311503fdfdac366c7143b24b40b619fc7c299f34ead3', 'name': 'internal_observation_component', 'version': '4.0.0', 'name_version': 'internal_observation_component:4.0.0', 'type': '', 'purl': '', 'purl_type': 'pypi', 'purl_namespace': ''}]}"
        self._test_api(APITest("db_admin", "get", "/api/components/", None, 200, expected_data))

        # A member of the internal product sees component 1 because of its license component and
        # component 4 because of its active observation. The active observation of component 1
        # belongs to the external product, so has_active_observations is False here, while its inactive
        # observation belongs to the internal product.
        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'has_active_observations': False, 'has_inactive_observations': True, 'has_licenses': True, 'identity_hash': '3aac376e96aec05c7ac55d6e938228e2e983dff95801c63e0b93f13203a50345', 'name': 'internal_component', 'version': '1.0.0', 'name_version': 'internal_component:1.0.0', 'type': '', 'purl': '', 'purl_type': 'npm', 'purl_namespace': ''}, {'id': 4, 'has_active_observations': True, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '04ded96e2cd9245aa36a311503fdfdac366c7143b24b40b619fc7c299f34ead3', 'name': 'internal_observation_component', 'version': '4.0.0', 'name_version': 'internal_observation_component:4.0.0', 'type': '', 'purl': '', 'purl_type': 'pypi', 'purl_namespace': ''}]}"
        self._test_api(APITest("db_internal_write", "get", "/api/components/", None, 200, expected_data))

        # A member of the external product sees component 1 because of its active observation and
        # component 2 because of its license component. The license component and the inactive
        # observation of component 1 belong to the internal product, so has_licenses and
        # has_inactive_observations are False here.
        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'has_active_observations': True, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '3aac376e96aec05c7ac55d6e938228e2e983dff95801c63e0b93f13203a50345', 'name': 'internal_component', 'version': '1.0.0', 'name_version': 'internal_component:1.0.0', 'type': '', 'purl': '', 'purl_type': 'npm', 'purl_namespace': ''}, {'id': 2, 'has_active_observations': False, 'has_inactive_observations': True, 'has_licenses': True, 'identity_hash': '19de944bd2436a9bae5221bc32e079e1ecc2dbf9ee3954e398bec8ebf78bc3ab', 'name': 'external_component', 'version': '2.0.0', 'name_version': 'external_component:2.0.0', 'type': '', 'purl': '', 'purl_type': '', 'purl_namespace': ''}]}"
        self._test_api(
            APITest(
                "db_external",
                "get",
                "/api/components/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 1, 'has_active_observations': False, 'has_inactive_observations': True, 'has_licenses': True, 'identity_hash': '3aac376e96aec05c7ac55d6e938228e2e983dff95801c63e0b93f13203a50345', 'name': 'internal_component', 'version': '1.0.0', 'name_version': 'internal_component:1.0.0', 'type': '', 'purl': '', 'purl_type': 'npm', 'purl_namespace': ''}"
        self._test_api(APITest("db_internal_write", "get", "/api/components/1/", None, 200, expected_data))

        expected_data = "{'id': 1, 'has_active_observations': True, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '3aac376e96aec05c7ac55d6e938228e2e983dff95801c63e0b93f13203a50345', 'name': 'internal_component', 'version': '1.0.0', 'name_version': 'internal_component:1.0.0', 'type': '', 'purl': '', 'purl_type': 'npm', 'purl_namespace': ''}"
        self._test_api(
            APITest(
                "db_external",
                "get",
                "/api/components/1/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'id': 4, 'has_active_observations': True, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '04ded96e2cd9245aa36a311503fdfdac366c7143b24b40b619fc7c299f34ead3', 'name': 'internal_observation_component', 'version': '4.0.0', 'name_version': 'internal_observation_component:4.0.0', 'type': '', 'purl': '', 'purl_type': 'pypi', 'purl_namespace': ''}"
        self._test_api(APITest("db_internal_write", "get", "/api/components/4/", None, 200, expected_data))

        expected_data = "{'id': 3, 'has_active_observations': False, 'has_inactive_observations': False, 'has_licenses': False, 'identity_hash': '4390291ad7af75eefca71dc2d03b9d72bcd5a7974a951c9285d47a79f69d37f4', 'name': 'unused_component', 'version': '3.0.0', 'name_version': 'unused_component:3.0.0', 'type': '', 'purl': '', 'purl_type': '', 'purl_namespace': ''}"
        self._test_api(
            APITest(
                "db_admin",
                "get",
                "/api/components/3/",
                None,
                200,
                expected_data,
                no_second_user=True,
            )
        )

        expected_data = "{'message': 'No Component matches the given query.'}"
        self._test_api(APITest("db_internal_write", "get", "/api/components/2/", None, 404, expected_data))
        self._test_api(APITest("db_internal_write", "get", "/api/components/3/", None, 404, expected_data))
        self._test_api(APITest("db_internal_write", "get", "/api/components/99999/", None, 404, expected_data))

        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'name_version': 'internal_component:1.0.0'}, {'id': 4, 'name_version': 'internal_observation_component:4.0.0'}]}"
        self._test_api(APITest("db_internal_write", "get", "/api/component_names/", None, 200, expected_data))

        post_data = {"name": "new_component"}
        self._test_api(APITest("db_internal_write", "post", "/api/components/", post_data, 405, None))

        self._test_api(APITest("db_internal_write", "patch", "/api/components/1/", {"name": "changed"}, 405, None))

        self._test_api(APITest("db_internal_write", "delete", "/api/components/1/", None, 405, None))
