from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)


class TestAuthorizationLicense_Components(TestAuthorizationBase):
    def test_authorization_license_components_product_member(self):
        self._test_authorization_license_components()

    def test_authorization_license_components_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_license_components()

    def _test_authorization_license_components(self):
        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'component_name_version_type': 'internal_component:1.0.0', 'branch_name': '', 'origin_service_name': '', 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'upload_filename': '', 'component_name': 'internal_component', 'component_version': '1.0.0', 'component_name_version': 'internal_component:1.0.0', 'component_purl': '', 'component_purl_type': '', 'component_cpe': '', 'component_cyclonedx_bom_link': '', 'imported_declared_license_name': 'internal license', 'imported_declared_license_expression': '', 'imported_declared_non_spdx_license': 'internal license', 'imported_declared_multiple_licenses': '', 'imported_concluded_license_name': 'No license information', 'imported_concluded_license_expression': '', 'imported_concluded_non_spdx_license': '', 'imported_concluded_multiple_licenses': '', 'manual_concluded_license_name': 'No license information', 'manual_concluded_license_expression': '', 'manual_concluded_non_spdx_license': '', 'manual_concluded_comment': '', 'effective_license_name': 'No license information', 'effective_license_expression': '', 'effective_non_spdx_license': '', 'effective_multiple_licenses': '', 'evaluation_result': 'Allowed', 'numerical_evaluation_result': 1, 'created': '2022-12-15T17:10:35.513000+01:00', 'import_last_seen': '2022-12-15T17:10:35.513000+01:00', 'last_change': '2022-12-15T17:10:35.513000+01:00', 'product': 1, 'branch': None, 'imported_declared_spdx_license': None, 'imported_concluded_spdx_license': None, 'manual_concluded_spdx_license': None, 'effective_spdx_license': None, 'origin_service': None}, {'id': 2, 'component_name_version_type': 'external_component:2.0.0', 'branch_name': '', 'origin_service_name': '', 'identity_hash': 'da3a81cebbfa79d18f0c0ba0046edacb2428d23a93f4b561ddd54b0478d16cb9', 'upload_filename': '', 'component_name': 'external_component', 'component_version': '2.0.0', 'component_name_version': 'external_component:2.0.0', 'component_purl': '', 'component_purl_type': '', 'component_cpe': '', 'component_cyclonedx_bom_link': '', 'imported_declared_license_name': 'external license', 'imported_declared_license_expression': '', 'imported_declared_non_spdx_license': 'external license', 'imported_declared_multiple_licenses': '', 'imported_concluded_license_name': 'No license information', 'imported_concluded_license_expression': '', 'imported_concluded_non_spdx_license': '', 'imported_concluded_multiple_licenses': '', 'manual_concluded_license_name': 'No license information', 'manual_concluded_license_expression': '', 'manual_concluded_non_spdx_license': '', 'manual_concluded_comment': '', 'effective_license_name': 'No license information', 'effective_license_expression': '', 'effective_non_spdx_license': '', 'effective_multiple_licenses': '', 'evaluation_result': 'Review required', 'numerical_evaluation_result': 2, 'created': '2022-12-15T17:10:35.513000+01:00', 'import_last_seen': '2022-12-15T17:10:35.513000+01:00', 'last_change': '2022-12-15T17:10:35.513000+01:00', 'product': 2, 'branch': None, 'imported_declared_spdx_license': None, 'imported_concluded_spdx_license': None, 'manual_concluded_spdx_license': None, 'effective_spdx_license': None, 'origin_service': None}]}"
        self._test_api(APITest("db_admin", "get", "/api/license_components/", None, 200, expected_data))

        expected_data = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 1, 'component_name_version_type': 'internal_component:1.0.0', 'branch_name': '', 'origin_service_name': '', 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'upload_filename': '', 'component_name': 'internal_component', 'component_version': '1.0.0', 'component_name_version': 'internal_component:1.0.0', 'component_purl': '', 'component_purl_type': '', 'component_cpe': '', 'component_cyclonedx_bom_link': '', 'imported_declared_license_name': 'internal license', 'imported_declared_license_expression': '', 'imported_declared_non_spdx_license': 'internal license', 'imported_declared_multiple_licenses': '', 'imported_concluded_license_name': 'No license information', 'imported_concluded_license_expression': '', 'imported_concluded_non_spdx_license': '', 'imported_concluded_multiple_licenses': '', 'manual_concluded_license_name': 'No license information', 'manual_concluded_license_expression': '', 'manual_concluded_non_spdx_license': '', 'manual_concluded_comment': '', 'effective_license_name': 'No license information', 'effective_license_expression': '', 'effective_non_spdx_license': '', 'effective_multiple_licenses': '', 'evaluation_result': 'Allowed', 'numerical_evaluation_result': 1, 'created': '2022-12-15T17:10:35.513000+01:00', 'import_last_seen': '2022-12-15T17:10:35.513000+01:00', 'last_change': '2022-12-15T17:10:35.513000+01:00', 'product': 1, 'branch': None, 'imported_declared_spdx_license': None, 'imported_concluded_spdx_license': None, 'manual_concluded_spdx_license': None, 'effective_spdx_license': None, 'origin_service': None}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'id': 1, 'component_name_version_type': 'internal_component:1.0.0', 'branch_name': '', 'origin_service_name': '', 'license_policy_name': '', 'license_policy_id': 0, 'evidences': [{'id': 1, 'name': 'internal_license_evidence_name'}], 'effective_license_type': '', 'title': 'No license information / internal_component:1.0.0', 'permissions': {<Permissions.VEX_View: 5001>, <Permissions.VEX_Edit: 5002>, <Permissions.VEX_Delete: 5003>, <Permissions.VEX_Create: 5004>, <Permissions.Product_Rule_View: 1301>, <Permissions.Product_Rule_Edit: 1302>, <Permissions.Product_Rule_Delete: 1303>, <Permissions.Product_Rule_Create: 1304>, <Permissions.Product_Rule_Apply: 1305>, <Permissions.Product_Rule_Approval: 1306>, <Permissions.Product_Api_Token_Revoke: 4003>, <Permissions.Product_Api_Token_Create: 4004>, <Permissions.Product_Member_View: 1201>, <Permissions.Product_Member_Edit: 1202>, <Permissions.Product_Member_Delete: 1203>, <Permissions.Product_Member_Create: 1204>, <Permissions.Observation_Log_Approval: 2101>, <Permissions.Api_Configuration_View: 3001>, <Permissions.Api_Configuration_Edit: 3002>, <Permissions.Api_Configuration_Delete: 3003>, <Permissions.Api_Configuration_Create: 3004>, <Permissions.Product_Authorization_Group_Member_View: 1601>, <Permissions.Product_Authorization_Group_Member_Edit: 1602>, <Permissions.Product_Authorization_Group_Member_Delete: 1603>, <Permissions.Product_Authorization_Group_Member_Create: 1604>, <Permissions.Product_View: 1101>, <Permissions.Product_Edit: 1102>, <Permissions.Product_Delete: 1103>, <Permissions.Product_Import_Observations: 1105>, <Permissions.Product_Scan_OSV: 1106>, <Permissions.Observation_View: 2001>, <Permissions.Observation_Edit: 2002>, <Permissions.Observation_Create: 2004>, <Permissions.Observation_Delete: 2003>, <Permissions.Observation_Assessment: 2005>, <Permissions.Concluded_License_View: 7001>, <Permissions.Concluded_License_Edit: 7002>, <Permissions.Concluded_License_Delete: 7003>, <Permissions.Concluded_License_Create: 7004>, <Permissions.Service_View: 1501>, <Permissions.Serice_Edit: 1502>, <Permissions.Service_Delete: 1503>, <Permissions.Service_Create: 1504>, <Permissions.Product_Group_View: 1001>, <Permissions.Product_Group_Edit: 1002>, <Permissions.Product_Group_Delete: 1003>, <Permissions.License_Component_Edit: 6002>, <Permissions.License_Component_Delete: 6003>, <Permissions.Branch_View: 1401>, <Permissions.Branch_Edit: 1402>, <Permissions.Branch_Delete: 1403>, <Permissions.Branch_Create: 1404>}, 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'upload_filename': '', 'component_name': 'internal_component', 'component_version': '1.0.0', 'component_name_version': 'internal_component:1.0.0', 'component_purl': '', 'component_purl_type': '', 'component_cpe': '', 'component_dependencies': '', 'component_cyclonedx_bom_link': '', 'imported_declared_license_name': 'internal license', 'imported_declared_license_expression': '', 'imported_declared_non_spdx_license': 'internal license', 'imported_declared_multiple_licenses': '', 'imported_concluded_license_name': 'No license information', 'imported_concluded_license_expression': '', 'imported_concluded_non_spdx_license': '', 'imported_concluded_multiple_licenses': '', 'manual_concluded_license_name': 'No license information', 'manual_concluded_license_expression': '', 'manual_concluded_non_spdx_license': '', 'manual_concluded_comment': '', 'effective_license_name': 'No license information', 'effective_license_expression': '', 'effective_non_spdx_license': '', 'effective_multiple_licenses': '', 'evaluation_result': 'Allowed', 'numerical_evaluation_result': 1, 'created': '2022-12-15T17:10:35.513000+01:00', 'import_last_seen': '2022-12-15T17:10:35.513000+01:00', 'last_change': '2022-12-15T17:10:35.513000+01:00', 'product': 1, 'branch': None, 'imported_declared_spdx_license': None, 'imported_concluded_spdx_license': None, 'manual_concluded_spdx_license': None, 'effective_spdx_license': None, 'origin_service': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/1/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'message': 'No License_Component matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/2/",
                None,
                404,
                expected_data,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/99999/",
                None,
                404,
                expected_data,
            )
        )

        expected_data = "{'message': 'No component id provided'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/for_component/",
                None,
                400,
                expected_data,
            )
        )

        expected_data = "{'id': 1, 'component_name_version_type': 'internal_component:1.0.0', 'branch_name': '', 'origin_service_name': '', 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'upload_filename': '', 'component_name': 'internal_component', 'component_version': '1.0.0', 'component_name_version': 'internal_component:1.0.0', 'component_purl': '', 'component_purl_type': '', 'component_cpe': '', 'component_cyclonedx_bom_link': '', 'imported_declared_license_name': 'internal license', 'imported_declared_license_expression': '', 'imported_declared_non_spdx_license': 'internal license', 'imported_declared_multiple_licenses': '', 'imported_concluded_license_name': 'No license information', 'imported_concluded_license_expression': '', 'imported_concluded_non_spdx_license': '', 'imported_concluded_multiple_licenses': '', 'manual_concluded_license_name': 'No license information', 'manual_concluded_license_expression': '', 'manual_concluded_non_spdx_license': '', 'manual_concluded_comment': '', 'effective_license_name': 'No license information', 'effective_license_expression': '', 'effective_non_spdx_license': '', 'effective_multiple_licenses': '', 'evaluation_result': 'Allowed', 'numerical_evaluation_result': 1, 'created': '2022-12-15T17:10:35.513000+01:00', 'import_last_seen': '2022-12-15T17:10:35.513000+01:00', 'last_change': '2022-12-15T17:10:35.513000+01:00', 'product': 1, 'branch': None, 'imported_declared_spdx_license': None, 'imported_concluded_spdx_license': None, 'manual_concluded_spdx_license': None, 'effective_spdx_license': None, 'origin_service': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/for_component/?component=4dd012d1d2e18cf07666cc7fe0520da0",
                None,
                200,
                expected_data,
            )
        )

        expected_data = "{'message': 'No Component matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/for_component/?component=25a348829ab6ef7330b97069dab60a40",
                None,
                404,
                expected_data,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/license_components/for_component/?component=abc",
                None,
                404,
                expected_data,
            )
        )

        post_data = {"product": 1}
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/license_components/",
                post_data,
                405,
                None,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/license_components/1/",
                {"title": "changed"},
                405,
                None,
            )
        )

        self._test_api(
            APITest(
                "db_internal_write",
                "delete",
                "/api/license_components/1/",
                None,
                405,
                None,
            )
        )

        patch_data = {"concluded_spdx_license": 1}
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/license_components/1/concluded_license/",
                patch_data,
                200,
                None,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/license_components/1/concluded_license/",
                patch_data,
                403,
                expected_data,
            )
        )
