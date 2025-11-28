from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)
from unittests.authorization.services.test_authorization import (
    prepare_authorization_groups,
)


class TestAuthorizationObservations(TestAuthorizationBase):
    def test_authorization_observations_product_member(self):
        self._test_authorization_observations()

    def test_authorization_observations_product_authorization_group_member(self):
        prepare_authorization_groups()
        self._test_authorization_observations()

    def _test_authorization_observations(self):
        expected_data = "{'count': 2, 'next': None, 'previous': None, 'results': [{'id': 1, 'product_data': {'id': 1, 'product_group_name': 'db_product_group', 'name': 'db_product_internal', 'description': '', 'purl': '', 'cpe23': '', 'repository_prefix': '', 'repository_branch_housekeeping_active': None, 'repository_branch_housekeeping_keep_inactive_days': None, 'repository_branch_housekeeping_exempt_branches': '', 'security_gate_passed': True, 'security_gate_active': None, 'security_gate_threshold_critical': None, 'security_gate_threshold_high': None, 'security_gate_threshold_medium': None, 'security_gate_threshold_low': None, 'security_gate_threshold_none': None, 'security_gate_threshold_unknown': None, 'apply_general_rules': True, 'notification_ms_teams_webhook': '', 'notification_slack_webhook': '', 'notification_email_to': '', 'issue_tracker_active': False, 'issue_tracker_type': '', 'issue_tracker_base_url': '', 'issue_tracker_username': '', 'issue_tracker_api_key': '', 'issue_tracker_project_id': '', 'issue_tracker_labels': '', 'issue_tracker_issue_type': '', 'issue_tracker_status_closed': '', 'issue_tracker_minimum_severity': '', 'last_observation_change': '2022-12-16T17:13:18.283000+01:00', 'assessments_need_approval': False, 'product_rules_need_approval': False, 'risk_acceptance_expiry_active': None, 'risk_acceptance_expiry_days': None, 'osv_enabled': True, 'osv_linux_distribution': '', 'osv_linux_release': '', 'automatic_osv_scanning_enabled': False, 'has_cloud_resource': False, 'has_component': False, 'has_docker_image': False, 'has_endpoint': False, 'has_kubernetes_resource': False, 'has_source': False, 'has_potential_duplicates': False, 'product_group': 3, 'repository_default_branch': 1, 'license_policy': None}, 'branch_name': 'db_branch_internal_dev', 'parser_data': {'id': 1, 'name': 'db_parser_file', 'type': 'DAST', 'source': 'File', 'sbom': False, 'module_name': '', 'class_name': ''}, 'scanner_name': 'db_parser', 'origin_component_name_version': '', 'origin_source_file_short': '', 'origin_source_file_url': None, 'vulnerability_id_aliases': [], 'cve_found_in': [], 'title': 'db_observation_internal', 'description': '', 'recommendation': '', 'current_severity': 'Medium', 'parser_severity': 'Medium', 'rule_severity': '', 'assessment_severity': '', 'current_status': 'Duplicate', 'parser_status': 'Open', 'vex_status': '', 'rule_status': 'Duplicate', 'assessment_status': '', 'scanner_observation_id': '', 'vulnerability_id': '', 'origin_component_name': '', 'origin_component_version': '', 'origin_component_purl': '', 'origin_component_purl_type': '', 'origin_component_cpe': '', 'origin_component_cyclonedx_bom_link': '', 'origin_docker_image_name': '', 'origin_docker_image_tag': '', 'origin_docker_image_name_tag': '', 'origin_docker_image_name_tag_short': '', 'origin_docker_image_digest': '', 'origin_endpoint_url': '', 'origin_endpoint_scheme': '', 'origin_endpoint_hostname': '', 'origin_endpoint_port': None, 'origin_endpoint_path': '', 'origin_endpoint_params': '', 'origin_endpoint_query': '', 'origin_endpoint_fragment': '', 'origin_service_name': 'db_service_internal_backend', 'origin_source_file': '', 'origin_source_line_start': None, 'origin_source_line_end': None, 'origin_cloud_provider': '', 'origin_cloud_account_subscription_project': '', 'origin_cloud_resource': '', 'origin_cloud_resource_type': '', 'origin_cloud_qualified_resource': '', 'origin_kubernetes_cluster': '', 'origin_kubernetes_namespace': '', 'origin_kubernetes_resource_type': '', 'origin_kubernetes_resource_name': '', 'origin_kubernetes_qualified_resource': '', 'cvss3_score': None, 'cvss3_vector': '', 'cvss4_score': None, 'cvss4_vector': '', 'cwe': None, 'epss_score': None, 'epss_percentile': None, 'found': None, 'scanner': 'db_parser', 'upload_filename': 'parser.json', 'api_configuration_name': '', 'import_last_seen': '2022-12-15T17:14:20.870000+01:00', 'created': '2022-12-15T17:10:35.513000+01:00', 'modified': '2022-12-16T17:13:18.282000+01:00', 'last_observation_log': '2022-12-16T17:13:18.281000+01:00', 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'issue_tracker_issue_id': '', 'issue_tracker_issue_closed': False, 'has_potential_duplicates': False, 'current_vex_justification': '', 'parser_vex_justification': '', 'vex_vex_justification': '', 'rule_vex_justification': '', 'assessment_vex_justification': '', 'risk_acceptance_expiry_date': None, 'product': 1, 'branch': 1, 'parser': 1, 'origin_service': 1, 'general_rule': None, 'product_rule': 1, 'vex_statement': None}, {'id': 2, 'product_data': {'id': 2, 'product_group_name': '', 'name': 'db_product_external', 'description': '', 'purl': '', 'cpe23': '', 'repository_prefix': '', 'repository_branch_housekeeping_active': None, 'repository_branch_housekeeping_keep_inactive_days': None, 'repository_branch_housekeeping_exempt_branches': '', 'security_gate_passed': None, 'security_gate_active': False, 'security_gate_threshold_critical': None, 'security_gate_threshold_high': None, 'security_gate_threshold_medium': None, 'security_gate_threshold_low': None, 'security_gate_threshold_none': None, 'security_gate_threshold_unknown': None, 'apply_general_rules': True, 'notification_ms_teams_webhook': '', 'notification_slack_webhook': '', 'notification_email_to': '', 'issue_tracker_active': False, 'issue_tracker_type': '', 'issue_tracker_base_url': '', 'issue_tracker_username': '', 'issue_tracker_api_key': '', 'issue_tracker_project_id': '', 'issue_tracker_labels': '', 'issue_tracker_issue_type': '', 'issue_tracker_status_closed': '', 'issue_tracker_minimum_severity': '', 'last_observation_change': '2022-12-16T17:13:18.283000+01:00', 'assessments_need_approval': False, 'product_rules_need_approval': False, 'risk_acceptance_expiry_active': None, 'risk_acceptance_expiry_days': None, 'osv_enabled': True, 'osv_linux_distribution': '', 'osv_linux_release': '', 'automatic_osv_scanning_enabled': False, 'has_cloud_resource': False, 'has_component': False, 'has_docker_image': False, 'has_endpoint': False, 'has_kubernetes_resource': False, 'has_source': False, 'has_potential_duplicates': False, 'product_group': None, 'repository_default_branch': 3, 'license_policy': None}, 'branch_name': '', 'parser_data': {'id': 1, 'name': 'db_parser_file', 'type': 'DAST', 'source': 'File', 'sbom': False, 'module_name': '', 'class_name': ''}, 'scanner_name': 'db_parser', 'origin_component_name_version': '', 'origin_source_file_short': '', 'origin_source_file_url': None, 'vulnerability_id_aliases': [], 'cve_found_in': [], 'title': 'db_observation_internal', 'description': '', 'recommendation': '', 'current_severity': 'Medium', 'parser_severity': 'Medium', 'rule_severity': '', 'assessment_severity': '', 'current_status': 'False positive', 'parser_status': 'Open', 'vex_status': '', 'rule_status': 'False positive', 'assessment_status': '', 'scanner_observation_id': '', 'vulnerability_id': '', 'origin_component_name': '', 'origin_component_version': '', 'origin_component_purl': '', 'origin_component_purl_type': '', 'origin_component_cpe': '', 'origin_component_cyclonedx_bom_link': '', 'origin_docker_image_name': '', 'origin_docker_image_tag': '', 'origin_docker_image_name_tag': '', 'origin_docker_image_name_tag_short': '', 'origin_docker_image_digest': '', 'origin_endpoint_url': '', 'origin_endpoint_scheme': '', 'origin_endpoint_hostname': '', 'origin_endpoint_port': None, 'origin_endpoint_path': '', 'origin_endpoint_params': '', 'origin_endpoint_query': '', 'origin_endpoint_fragment': '', 'origin_service_name': '', 'origin_source_file': '', 'origin_source_line_start': None, 'origin_source_line_end': None, 'origin_cloud_provider': '', 'origin_cloud_account_subscription_project': '', 'origin_cloud_resource': '', 'origin_cloud_resource_type': '', 'origin_cloud_qualified_resource': '', 'origin_kubernetes_cluster': '', 'origin_kubernetes_namespace': '', 'origin_kubernetes_resource_type': '', 'origin_kubernetes_resource_name': '', 'origin_kubernetes_qualified_resource': '', 'cvss3_score': None, 'cvss3_vector': '', 'cvss4_score': None, 'cvss4_vector': '', 'cwe': None, 'epss_score': None, 'epss_percentile': None, 'found': None, 'scanner': 'db_parser', 'upload_filename': 'parser.json', 'api_configuration_name': '', 'import_last_seen': '2022-12-15T17:14:20.876000+01:00', 'created': '2022-12-15T17:10:35.521000+01:00', 'modified': '2022-12-16T17:13:18.283000+01:00', 'last_observation_log': '2022-12-16T17:13:18.283000+01:00', 'identity_hash': 'da3a81cebbfa79d18f0c0ba0046edacb2428d23a93f4b561ddd54b0478d16cb9', 'issue_tracker_issue_id': '', 'issue_tracker_issue_closed': False, 'has_potential_duplicates': False, 'current_vex_justification': '', 'parser_vex_justification': '', 'vex_vex_justification': '', 'rule_vex_justification': '', 'assessment_vex_justification': '', 'risk_acceptance_expiry_date': None, 'product': 2, 'branch': None, 'parser': 1, 'origin_service': None, 'general_rule': None, 'product_rule': 2, 'vex_statement': None}]}"
        self._test_api(APITest("db_admin", "get", "/api/observations/", None, 200, expected_data))

        expected_data = "{'count': 1, 'next': None, 'previous': None, 'results': [{'id': 1, 'product_data': {'id': 1, 'product_group_name': 'db_product_group', 'name': 'db_product_internal', 'description': '', 'purl': '', 'cpe23': '', 'repository_prefix': '', 'repository_branch_housekeeping_active': None, 'repository_branch_housekeeping_keep_inactive_days': None, 'repository_branch_housekeeping_exempt_branches': '', 'security_gate_passed': True, 'security_gate_active': None, 'security_gate_threshold_critical': None, 'security_gate_threshold_high': None, 'security_gate_threshold_medium': None, 'security_gate_threshold_low': None, 'security_gate_threshold_none': None, 'security_gate_threshold_unknown': None, 'apply_general_rules': True, 'notification_ms_teams_webhook': '', 'notification_slack_webhook': '', 'notification_email_to': '', 'issue_tracker_active': False, 'issue_tracker_type': '', 'issue_tracker_base_url': '', 'issue_tracker_username': '', 'issue_tracker_api_key': '', 'issue_tracker_project_id': '', 'issue_tracker_labels': '', 'issue_tracker_issue_type': '', 'issue_tracker_status_closed': '', 'issue_tracker_minimum_severity': '', 'last_observation_change': '2022-12-16T17:13:18.283000+01:00', 'assessments_need_approval': False, 'product_rules_need_approval': False, 'risk_acceptance_expiry_active': None, 'risk_acceptance_expiry_days': None, 'osv_enabled': True, 'osv_linux_distribution': '', 'osv_linux_release': '', 'automatic_osv_scanning_enabled': False, 'has_cloud_resource': False, 'has_component': False, 'has_docker_image': False, 'has_endpoint': False, 'has_kubernetes_resource': False, 'has_source': False, 'has_potential_duplicates': False, 'product_group': 3, 'repository_default_branch': 1, 'license_policy': None}, 'branch_name': 'db_branch_internal_dev', 'parser_data': {'id': 1, 'name': 'db_parser_file', 'type': 'DAST', 'source': 'File', 'sbom': False, 'module_name': '', 'class_name': ''}, 'scanner_name': 'db_parser', 'origin_component_name_version': '', 'origin_source_file_short': '', 'origin_source_file_url': None, 'vulnerability_id_aliases': [], 'cve_found_in': [], 'title': 'db_observation_internal', 'description': '', 'recommendation': '', 'current_severity': 'Medium', 'parser_severity': 'Medium', 'rule_severity': '', 'assessment_severity': '', 'current_status': 'Duplicate', 'parser_status': 'Open', 'vex_status': '', 'rule_status': 'Duplicate', 'assessment_status': '', 'scanner_observation_id': '', 'vulnerability_id': '', 'origin_component_name': '', 'origin_component_version': '', 'origin_component_purl': '', 'origin_component_purl_type': '', 'origin_component_cpe': '', 'origin_component_cyclonedx_bom_link': '', 'origin_docker_image_name': '', 'origin_docker_image_tag': '', 'origin_docker_image_name_tag': '', 'origin_docker_image_name_tag_short': '', 'origin_docker_image_digest': '', 'origin_endpoint_url': '', 'origin_endpoint_scheme': '', 'origin_endpoint_hostname': '', 'origin_endpoint_port': None, 'origin_endpoint_path': '', 'origin_endpoint_params': '', 'origin_endpoint_query': '', 'origin_endpoint_fragment': '', 'origin_service_name': 'db_service_internal_backend', 'origin_source_file': '', 'origin_source_line_start': None, 'origin_source_line_end': None, 'origin_cloud_provider': '', 'origin_cloud_account_subscription_project': '', 'origin_cloud_resource': '', 'origin_cloud_resource_type': '', 'origin_cloud_qualified_resource': '', 'origin_kubernetes_cluster': '', 'origin_kubernetes_namespace': '', 'origin_kubernetes_resource_type': '', 'origin_kubernetes_resource_name': '', 'origin_kubernetes_qualified_resource': '', 'cvss3_score': None, 'cvss3_vector': '', 'cvss4_score': None, 'cvss4_vector': '', 'cwe': None, 'epss_score': None, 'epss_percentile': None, 'found': None, 'scanner': 'db_parser', 'upload_filename': 'parser.json', 'api_configuration_name': '', 'import_last_seen': '2022-12-15T17:14:20.870000+01:00', 'created': '2022-12-15T17:10:35.513000+01:00', 'modified': '2022-12-16T17:13:18.282000+01:00', 'last_observation_log': '2022-12-16T17:13:18.281000+01:00', 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'issue_tracker_issue_id': '', 'issue_tracker_issue_closed': False, 'has_potential_duplicates': False, 'current_vex_justification': '', 'parser_vex_justification': '', 'vex_vex_justification': '', 'rule_vex_justification': '', 'assessment_vex_justification': '', 'risk_acceptance_expiry_date': None, 'product': 1, 'branch': 1, 'parser': 1, 'origin_service': 1, 'general_rule': None, 'product_rule': 1, 'vex_statement': None}]}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/observations/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'id': 1, 'product_data': {'id': 1, 'permissions': {<Permissions.VEX_View: 5001>, <Permissions.VEX_Edit: 5002>, <Permissions.VEX_Delete: 5003>, <Permissions.VEX_Create: 5004>, <Permissions.Product_Rule_View: 1301>, <Permissions.Product_Rule_Edit: 1302>, <Permissions.Product_Rule_Delete: 1303>, <Permissions.Product_Rule_Create: 1304>, <Permissions.Product_Rule_Apply: 1305>, <Permissions.Product_Rule_Approval: 1306>, <Permissions.Product_Api_Token_Revoke: 4003>, <Permissions.Product_Api_Token_Create: 4004>, <Permissions.Product_Member_View: 1201>, <Permissions.Product_Member_Edit: 1202>, <Permissions.Product_Member_Delete: 1203>, <Permissions.Product_Member_Create: 1204>, <Permissions.Observation_Log_Approval: 2101>, <Permissions.Api_Configuration_View: 3001>, <Permissions.Api_Configuration_Edit: 3002>, <Permissions.Api_Configuration_Delete: 3003>, <Permissions.Api_Configuration_Create: 3004>, <Permissions.Product_Authorization_Group_Member_View: 1601>, <Permissions.Product_Authorization_Group_Member_Edit: 1602>, <Permissions.Product_Authorization_Group_Member_Delete: 1603>, <Permissions.Product_Authorization_Group_Member_Create: 1604>, <Permissions.Product_View: 1101>, <Permissions.Product_Edit: 1102>, <Permissions.Product_Delete: 1103>, <Permissions.Product_Import_Observations: 1105>, <Permissions.Product_Scan_OSV: 1106>, <Permissions.Observation_View: 2001>, <Permissions.Observation_Edit: 2002>, <Permissions.Observation_Create: 2004>, <Permissions.Observation_Delete: 2003>, <Permissions.Observation_Assessment: 2005>, <Permissions.Concluded_License_View: 7001>, <Permissions.Concluded_License_Edit: 7002>, <Permissions.Concluded_License_Delete: 7003>, <Permissions.Concluded_License_Create: 7004>, <Permissions.Service_View: 1501>, <Permissions.Serice_Edit: 1502>, <Permissions.Service_Delete: 1503>, <Permissions.Service_Create: 1504>, <Permissions.Product_Group_View: 1001>, <Permissions.Product_Group_Edit: 1002>, <Permissions.Product_Group_Delete: 1003>, <Permissions.License_Component_Edit: 6002>, <Permissions.License_Component_Delete: 6003>, <Permissions.Branch_View: 1401>, <Permissions.Branch_Edit: 1402>, <Permissions.Branch_Delete: 1403>, <Permissions.Branch_Create: 1404>}, 'product_group_assessments_need_approval': False, 'product_group_product_rules_need_approval': False, 'risk_acceptance_expiry_date_calculated': datetime.date(2024, 7, 1), 'name': 'db_product_internal', 'description': '', 'is_product_group': False, 'purl': '', 'cpe23': '', 'repository_prefix': '', 'repository_branch_housekeeping_active': None, 'repository_branch_housekeeping_keep_inactive_days': None, 'repository_branch_housekeeping_exempt_branches': '', 'security_gate_passed': True, 'security_gate_active': None, 'security_gate_threshold_critical': None, 'security_gate_threshold_high': None, 'security_gate_threshold_medium': None, 'security_gate_threshold_low': None, 'security_gate_threshold_none': None, 'security_gate_threshold_unknown': None, 'apply_general_rules': True, 'notification_ms_teams_webhook': '', 'notification_slack_webhook': '', 'notification_email_to': '', 'issue_tracker_active': False, 'issue_tracker_type': '', 'issue_tracker_base_url': '', 'issue_tracker_username': '', 'issue_tracker_api_key': '', 'issue_tracker_project_id': '', 'issue_tracker_labels': '', 'issue_tracker_issue_type': '', 'issue_tracker_status_closed': '', 'issue_tracker_minimum_severity': '', 'last_observation_change': '2022-12-16T17:13:18.283000+01:00', 'assessments_need_approval': False, 'new_observations_in_review': False, 'product_rules_need_approval': False, 'risk_acceptance_expiry_active': None, 'risk_acceptance_expiry_days': None, 'osv_enabled': True, 'osv_linux_distribution': '', 'osv_linux_release': '', 'automatic_osv_scanning_enabled': False, 'has_cloud_resource': False, 'has_component': False, 'has_docker_image': False, 'has_endpoint': False, 'has_kubernetes_resource': False, 'has_source': False, 'has_potential_duplicates': False, 'product_group': 3, 'repository_default_branch': 1, 'license_policy': None}, 'branch_name': 'db_branch_internal_dev', 'parser_data': {'id': 1, 'name': 'db_parser_file', 'type': 'DAST', 'source': 'File', 'sbom': False, 'module_name': '', 'class_name': ''}, 'references': [], 'evidences': [{'id': 1, 'name': 'db_evidence_internal'}], 'origin_source_file_url': None, 'issue_tracker_issue_url': None, 'assessment_needs_approval': None, 'vulnerability_id_aliases': [], 'cve_found_in': [], 'title': 'db_observation_internal', 'description': '', 'recommendation': '', 'current_severity': 'Medium', 'parser_severity': 'Medium', 'rule_severity': '', 'assessment_severity': '', 'current_status': 'Duplicate', 'parser_status': 'Open', 'vex_status': '', 'rule_status': 'Duplicate', 'assessment_status': '', 'scanner_observation_id': '', 'vulnerability_id': '', 'origin_component_name': '', 'origin_component_version': '', 'origin_component_name_version': '', 'origin_component_purl': '', 'origin_component_purl_type': '', 'origin_component_cpe': '', 'origin_component_dependencies': '', 'origin_component_cyclonedx_bom_link': '', 'origin_docker_image_name': '', 'origin_docker_image_tag': '', 'origin_docker_image_name_tag': '', 'origin_docker_image_name_tag_short': '', 'origin_docker_image_digest': '', 'origin_endpoint_url': '', 'origin_endpoint_scheme': '', 'origin_endpoint_hostname': '', 'origin_endpoint_port': None, 'origin_endpoint_path': '', 'origin_endpoint_params': '', 'origin_endpoint_query': '', 'origin_endpoint_fragment': '', 'origin_service_name': 'db_service_internal_backend', 'origin_source_file': '', 'origin_source_line_start': None, 'origin_source_line_end': None, 'origin_cloud_provider': '', 'origin_cloud_account_subscription_project': '', 'origin_cloud_resource': '', 'origin_cloud_resource_type': '', 'origin_cloud_qualified_resource': '', 'origin_kubernetes_cluster': '', 'origin_kubernetes_namespace': '', 'origin_kubernetes_resource_type': '', 'origin_kubernetes_resource_name': '', 'origin_kubernetes_qualified_resource': '', 'cvss3_score': None, 'cvss3_vector': '', 'cvss4_score': None, 'cvss4_vector': '', 'cwe': None, 'epss_score': None, 'epss_percentile': None, 'found': None, 'scanner': 'db_parser', 'upload_filename': 'parser.json', 'api_configuration_name': '', 'import_last_seen': '2022-12-15T17:14:20.870000+01:00', 'created': '2022-12-15T17:10:35.513000+01:00', 'modified': '2022-12-16T17:13:18.282000+01:00', 'last_observation_log': '2022-12-16T17:13:18.281000+01:00', 'identity_hash': '12b30c8b800bd9607d01a3cd2f1cd72af4b8c948b2e7831a48bfc2589616f0be', 'issue_tracker_issue_id': '', 'issue_tracker_issue_closed': False, 'has_potential_duplicates': False, 'current_vex_justification': '', 'parser_vex_justification': '', 'vex_vex_justification': '', 'rule_vex_justification': '', 'assessment_vex_justification': '', 'risk_acceptance_expiry_date': None, 'product': 1, 'branch': 1, 'parser': 1, 'origin_service': 1, 'general_rule': None, 'product_rule': 1, 'vex_statement': None}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/observations/1/",
                None,
                200,
                expected_data,
            )
        )
        expected_data = "{'message': 'No Observation matches the given query.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/observations/2/",
                None,
                404,
                expected_data,
            )
        )
        self._test_api(
            APITest(
                "db_internal_write",
                "get",
                "/api/observations/99999/",
                None,
                404,
                expected_data,
            )
        )

        post_data = {"product": 1}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "post",
                "/api/observations/",
                post_data,
                403,
                expected_data,
            )
        )
        expected_data = "{'message': 'Title: This field is required.'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "post",
                "/api/observations/",
                post_data,
                400,
                expected_data,
            )
        )

        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/observations/1/",
                {"title": "changed"},
                403,
                expected_data,
            )
        )
        expected_data = "{'message': 'Non field errors: Only manual observations can be updated'}"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/observations/1/",
                {"title": "changed"},
                400,
                expected_data,
            )
        )

        post_data = {"comment": "reason for assessment"}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/observations/1/assessment/",
                post_data,
                403,
                expected_data,
            )
        )
        expected_data = "{'message': 'Observation 99999 not found'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/observations/99999/assessment/",
                post_data,
                404,
                expected_data,
            )
        )
        expected_data = "None"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/observations/1/assessment/",
                post_data,
                200,
                expected_data,
            )
        )

        post_data = {"comment": "reason for assessment removal"}
        expected_data = "{'message': 'You do not have permission to perform this action.'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/observations/1/remove_assessment/",
                post_data,
                403,
                expected_data,
            )
        )
        expected_data = "{'message': 'Observation 99999 not found'}"
        self._test_api(
            APITest(
                "db_internal_read",
                "patch",
                "/api/observations/99999/remove_assessment/",
                post_data,
                404,
                expected_data,
            )
        )
        expected_data = "None"
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/observations/1/remove_assessment/",
                post_data,
                200,
                expected_data,
            )
        )
