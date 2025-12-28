from unittests.authorization.api.test_authorization import (
    APITest,
    TestAuthorizationBase,
)


class TestAuthorizationSettings(TestAuthorizationBase):

    def test_authorization_settings(self):
        expected_data = "{'id': 1, 'security_gate_active': True, 'security_gate_threshold_critical': 0, 'security_gate_threshold_high': 0, 'security_gate_threshold_medium': 99999, 'security_gate_threshold_low': 99999, 'security_gate_threshold_none': 99999, 'security_gate_threshold_unknown': 99999, 'jwt_validity_duration_user': 168, 'jwt_validity_duration_superuser': 24, 'internal_users': '', 'base_url_frontend': '', 'exception_ms_teams_webhook': '', 'exception_slack_webhook': '', 'exception_rate_limit': 3600, 'email_from': '', 'exception_email_to': '', 'background_product_metrics_interval_minutes': 5, 'background_epss_import_crontab_minute': 0, 'background_epss_import_crontab_hour': 3, 'branch_housekeeping_crontab_minute': 0, 'branch_housekeeping_crontab_hour': 2, 'branch_housekeeping_active': True, 'branch_housekeeping_keep_inactive_days': 30, 'branch_housekeeping_exempt_branches': '', 'feature_vex': False, 'vex_justification_style': 'CSAF/OpenVEX', 'feature_disable_user_login': False, 'feature_general_rules_need_approval': False, 'risk_acceptance_expiry_days': 30, 'risk_acceptance_expiry_crontab_minute': 0, 'risk_acceptance_expiry_crontab_hour': 1, 'feature_automatic_api_import': True, 'api_import_crontab_minute': 0, 'api_import_crontab_hour': 4, 'password_validator_minimum_length': 8, 'password_validator_attribute_similarity': True, 'password_validator_common_passwords': True, 'password_validator_not_numeric': True, 'feature_license_management': True, 'license_import_crontab_minute': 30, 'license_import_crontab_hour': 1, 'feature_automatic_osv_scanning': True, 'feature_exploit_information': True, 'exploit_information_max_age_years': 10, 'periodic_task_max_entries': 10, 'oidc_clock_skew': 0}"
        self._test_api(APITest("db_admin", "get", "/api/settings/1/", None, 200, expected_data))

        self._test_api(APITest("db_internal_write", "get", "/api/settings/1/", None, 403, None))

        post_data = {"security_gate_threshold_critical": 1234}
        expected_data = "{'id': 1, 'security_gate_active': True, 'security_gate_threshold_critical': 1234, 'security_gate_threshold_high': 0, 'security_gate_threshold_medium': 99999, 'security_gate_threshold_low': 99999, 'security_gate_threshold_none': 99999, 'security_gate_threshold_unknown': 99999, 'jwt_validity_duration_user': 168, 'jwt_validity_duration_superuser': 24, 'internal_users': '', 'base_url_frontend': '', 'exception_ms_teams_webhook': '', 'exception_slack_webhook': '', 'exception_rate_limit': 3600, 'email_from': '', 'exception_email_to': '', 'background_product_metrics_interval_minutes': 5, 'background_epss_import_crontab_minute': 0, 'background_epss_import_crontab_hour': 3, 'branch_housekeeping_crontab_minute': 0, 'branch_housekeeping_crontab_hour': 2, 'branch_housekeeping_active': True, 'branch_housekeeping_keep_inactive_days': 30, 'branch_housekeeping_exempt_branches': '', 'feature_vex': False, 'vex_justification_style': 'CSAF/OpenVEX', 'feature_disable_user_login': False, 'feature_general_rules_need_approval': False, 'risk_acceptance_expiry_days': 30, 'risk_acceptance_expiry_crontab_minute': 0, 'risk_acceptance_expiry_crontab_hour': 1, 'feature_automatic_api_import': True, 'api_import_crontab_minute': 0, 'api_import_crontab_hour': 4, 'password_validator_minimum_length': 8, 'password_validator_attribute_similarity': True, 'password_validator_common_passwords': True, 'password_validator_not_numeric': True, 'feature_license_management': True, 'license_import_crontab_minute': 30, 'license_import_crontab_hour': 1, 'feature_automatic_osv_scanning': True, 'feature_exploit_information': True, 'exploit_information_max_age_years': 10, 'periodic_task_max_entries': 10, 'oidc_clock_skew': 0}"
        self._test_api(
            APITest(
                "db_admin",
                "patch",
                "/api/settings/1/",
                post_data,
                200,
                expected_data,
            )
        )

        post_data = {"security_gate_threshold_critical": 1234}
        self._test_api(
            APITest(
                "db_internal_write",
                "patch",
                "/api/settings/1/",
                post_data,
                403,
                None,
            )
        )
