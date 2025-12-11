from unittest.mock import patch

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient

from unittests.base_test_case import BaseTestCase


class TestAuthentication(BaseTestCase):
    def _check_not_authenticated(self, methods: list[str], url: str):
        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertEqual(401, response.status_code)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def _check_api_token_not_authenticated(self, methods: list[str], url: str, mock_authentication):
        mock_authentication.side_effect = AuthenticationFailed("authentication failed message")

        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertEqual(401, response.status_code)
            self.assertEqual("authentication failed message", response.data.get("message"))
            mock_authentication.assert_called_once()
            mock_authentication.reset_mock()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def _check_api_token_authenticated(self, methods: list[str], url: str, mock_authentication):
        mock_authentication.return_value = self.user_admin, None

        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertTrue(response.status_code in [200, 204, 400, 404])
            mock_authentication.assert_called_once()
            mock_authentication.reset_mock()

    @patch("application.access_control.services.jwt_authentication.JWTAuthentication.authenticate")
    def _check_jwt_not_authenticated(self, methods: list[str], url: str, mock_authentication):
        mock_authentication.side_effect = AuthenticationFailed("authentication failed message")

        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertEqual(401, response.status_code)
            self.assertEqual("authentication failed message", response.data.get("message"))
            mock_authentication.assert_called_once()
            mock_authentication.reset_mock()

    @patch("application.access_control.services.jwt_authentication.JWTAuthentication.authenticate")
    def _check_jwt_authenticated(self, methods: list[str], url: str, mock_authentication):
        mock_authentication.return_value = self.user_admin, None

        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertTrue(response.status_code in [200, 204, 400, 404])
            mock_authentication.assert_called_once()
            mock_authentication.reset_mock()

    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication.authenticate")
    def _check_oidc_not_authenticated(self, methods: list[str], url: str, mock_authentication):
        mock_authentication.side_effect = AuthenticationFailed("authentication failed message")

        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertEqual(401, response.status_code)
            # self.assertEqual(
            # "authentication failed message", response.data.get("message")
            # )
            mock_authentication.assert_called_once()
            mock_authentication.reset_mock()

    @patch("application.access_control.services.oidc_authentication.OIDCAuthentication.authenticate")
    def _check_oidc_authenticated(self, methods: list[str], url: str, mock_authentication):
        mock_authentication.return_value = self.user_admin, None

        api_client = APIClient()

        for method in methods:
            if method.lower() == "delete":
                response = api_client.delete(url)
            elif method.lower() == "get":
                response = api_client.get(url)
            elif method.lower() == "patch":
                response = api_client.patch(url)
            elif method.lower() == "post":
                response = api_client.post(url)
            elif method.lower() == "put":
                response = api_client.put(url)
            else:
                raise Exception(f"Unknown method: {method}")

            self.assertTrue(response.status_code in [200, 204, 400, 404])
            mock_authentication.assert_called_once()
            mock_authentication.reset_mock()

    def _check_authentication(self, methods: list[str], url: str):
        self._check_not_authenticated(methods, url)
        self._check_api_token_not_authenticated(methods, url)
        self._check_api_token_authenticated(methods, url)
        self._check_jwt_not_authenticated(methods, url)
        self._check_jwt_authenticated(methods, url)
        self._check_oidc_not_authenticated(methods, url)
        self._check_oidc_authenticated(methods, url)

    @patch("application.access_control.services.current_user.get_current_user")
    def test_authentication(self, mock_user):
        mock_user.return_value = self.user_admin

        self._check_authentication(["get", "post"], "/api/api_configurations/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/api_configurations/1/")

        self._check_authentication(["get"], "/api/vulnerability_checks/")
        self._check_authentication(["get"], "/api/vulnerability_checks/1/")

        self._check_authentication(["get", "post"], "/api/general_rules/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/general_rules/1/")
        self._check_authentication(["post"], "/api/general_rules/1/simulate/")

        self._check_authentication(["get"], "/api/metrics/export_csv/")
        self._check_authentication(["get"], "/api/metrics/export_excel/")
        self._check_authentication(["get"], "/api/metrics/export_codecharta/")
        self._check_authentication(["get"], "/api/metrics/product_metrics_current/")
        self._check_authentication(["get"], "/api/metrics/product_metrics_timeline/")
        self._check_authentication(["get"], "/api/metrics/product_metrics_status/")

        self._check_authentication(["get"], "/api/observations/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/observations/1/")
        self._check_authentication(["patch"], "/api/observations/1/assessment/")
        self._check_authentication(["patch"], "/api/observations/1/remove_assessment/")
        self._check_authentication(["post"], "/api/observations/bulk_assessment/")
        self._check_authentication(["post"], "/api/observations/bulk_approval/")
        self._check_authentication(["get"], "/api/observations/count_reviews/")

        self._check_authentication(["get"], "/api/observation_logs/")
        self._check_authentication(["get"], "/api/observation_logs/1/")
        self._check_authentication(["patch"], "/api/observation_logs/1/approval/")
        self._check_authentication(["post"], "/api/observation_logs/bulk_approval/")
        self._check_authentication(["get"], "/api/observation_logs/count_approvals/")

        self._check_authentication(["get"], "/api/observation_titles/")
        self._check_authentication(["get"], "/api/observation_titles/1/")

        self._check_authentication(["get"], "/api/parsers/")
        self._check_authentication(["get"], "/api/parsers/1/")

        self._check_authentication(["get", "post"], "/api/branches/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/branches/1/")

        self._check_authentication(["get"], "/api/branch_names/")
        self._check_authentication(["get"], "/api/branch_names/1/")

        self._check_authentication(["get", "post"], "/api/services/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/services/1/")

        self._check_authentication(["get"], "/api/service_names/")
        self._check_authentication(["get"], "/api/service_names/1/")

        self._check_authentication(["get", "post"], "/api/product_members/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/product_members/1/")

        self._check_authentication(["get", "post"], "/api/product_rules/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/product_rules/1/")
        self._check_authentication(["post"], "/api/product_rules/1/simulate/")

        self._check_authentication(["get", "post"], "/api/product_groups/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/product_groups/1/")

        self._check_authentication(["get"], "/api/product_group_names/")
        self._check_authentication(["get"], "/api/product_group_names/1/")

        self._check_authentication(["get", "post"], "/api/products/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/products/1/")

        self._check_authentication(["post"], "/api/products/1/apply_rules/")

        self._check_authentication(["post"], "/api/products/1/observations_bulk_assessment/")
        self._check_authentication(["post"], "/api/products/1/observations_bulk_delete/")
        self._check_authentication(["post"], "/api/products/1/observations_bulk_mark_duplicates/")
        self._check_authentication(["post"], "/api/products/1/license_components_bulk_delete/")

        self._check_authentication(["get"], "/api/products/1/export_observations_csv/")
        self._check_authentication(["get"], "/api/products/1/export_observations_excel/")

        self._check_authentication(["get"], "/api/products/1/export_license_components_csv/")
        self._check_authentication(["get"], "/api/products/1/export_license_components_excel/")

        self._check_authentication(["get"], "/api/product_names/")
        self._check_authentication(["get"], "/api/product_names/1/")

        self._check_authentication(["get"], "/api/evidences/1/")

        self._check_authentication(["get"], "/api/components/")
        self._check_authentication(["get"], "/api/components/1/")

        self._check_authentication(["get"], "/api/status/version/")

        self._check_authentication(["get", "post"], "/api/product_api_tokens/")
        self._check_authentication(["delete"], "/api/product_api_tokens/1/")

        self._check_authentication(["get"], "/api/notifications/")
        self._check_authentication(["delete", "get"], "/api/notifications/1/")
        self._check_authentication(["post"], "/api/notifications/1/mark_as_viewed/")
        self._check_authentication(["post"], "/api/notifications/bulk_mark_as_viewed/")

        self._check_authentication(["get"], "/api/licenses/")
        self._check_authentication(["get"], "/api/licenses/1/")

        self._check_authentication(["get"], "/api/license_components/")
        self._check_authentication(["get"], "/api/license_components/1/")

        self._check_authentication(["get"], "/api/license_component_ids/")
        self._check_authentication(["get"], "/api/license_component_ids/1/")

        self._check_authentication(["get"], "/api/license_component_evidences/")
        self._check_authentication(["get"], "/api/license_component_evidences/1/")

        self._check_authentication(["get", "post"], "/api/license_groups/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/license_groups/1/")
        self._check_authentication(["post"], "/api/license_groups/1/copy/")
        self._check_authentication(["post"], "/api/license_groups/1/add_license/")
        self._check_authentication(["post"], "/api/license_groups/1/remove_license/")

        self._check_authentication(["get", "post"], "/api/license_group_members/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/license_group_members/1001/")

        self._check_authentication(["get", "post"], "/api/license_group_authorization_group_members/")
        self._check_authentication(
            ["delete", "get", "put", "patch"],
            "/api/license_group_authorization_group_members/1001/",
        )

        self._check_authentication(["get", "post"], "/api/license_policies/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/license_policies/1/")
        self._check_authentication(["post"], "/api/license_policies/1/copy/")
        self._check_authentication(["post"], "/api/license_policies/1/apply/")
        self._check_authentication(["post"], "/api/license_policies/apply_product/")
        self._check_authentication(["get"], "/api/license_policies/1/export_json/")
        self._check_authentication(["get"], "/api/license_policies/1/export_yaml/")

        self._check_authentication(["get", "post"], "/api/license_policy_items/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/license_policy_items/1001/")

        self._check_authentication(["get", "post"], "/api/license_policy_members/")
        self._check_authentication(["delete", "get", "put", "patch"], "/api/license_policy_members/1001/")

        self._check_authentication(["get", "post"], "/api/license_policy_authorization_group_members/")
        self._check_authentication(
            ["delete", "get", "put", "patch"],
            "/api/license_policy_authorization_group_members/1001/",
        )

        self._check_authentication(["get"], "/api/concluded_licenses/")
        self._check_authentication(["delete", "get"], "/api/concluded_licenses/1/")

        self._check_authentication(["get"], "/api/periodic_tasks/")
        self._check_authentication(["get"], "/api/periodic_tasks/1/")

    def test_authentication_users(self):
        self._check_authentication(["get"], "/api/users/me/")
        self._check_authentication(["get"], "/api/users/")
        self._check_authentication(["get"], "/api/users/1/")
        self._check_authentication(["patch"], "/api/users/my_settings/")

    def test_settings(self):
        self._check_authentication(["get", "patch"], "/api/settings/1/")

    def test_jwt_secret(self):
        self._check_authentication(["post"], "/api/jwt_secret/reset/")
