from unittest.mock import ANY, patch

from django.core.management import call_command
from rest_framework.test import APIClient

from application.access_control.models import User
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase


class TestImport(BaseTestCase):
    def setUp(self):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )
        super().setUpClass()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_too_many_attributes(self, mock_authenticate):
        user = User.objects.get(username="db_admin")
        mock_authenticate.return_value = user, None

        patch_data = {
            "manual_concluded_non_spdx_license": "Non SPDX",
            "manual_concluded_license_expression": "Expression",
        }
        api_client = APIClient()
        response = api_client.patch("/api/license_components/1/concluded_license/", patch_data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            str(response.data), "{'message': 'Non field errors: Only one concluded license field may be set.'}"
        )

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_license_component_not_found(self, mock_authenticate):
        user = User.objects.get(username="db_admin")
        mock_authenticate.return_value = user, None

        patch_data = {"manual_concluded_non_spdx_license": "Non SPDX"}
        api_client = APIClient()
        response = api_client.patch("/api/license_components/99999/concluded_license/", patch_data, format="json")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(str(response.data), "{'message': 'License component 99999 not found.'}")

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_spdx_license_not_found(self, mock_authenticate):
        user = User.objects.get(username="db_admin")
        mock_authenticate.return_value = user, None

        patch_data = {"manual_concluded_spdx_license": 99999}
        api_client = APIClient()
        response = api_client.patch("/api/license_components/1/concluded_license/", patch_data, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data), "{'message': 'SPDX license 99999 not found.'}")

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.licenses.api.views.save_concluded_license")
    def test_spdx_license_success(self, mock_save_concluded_license, mock_authenticate):
        user = User.objects.get(username="db_admin")
        mock_authenticate.return_value = user, None

        patch_data = {"manual_concluded_spdx_license": 1}
        api_client = APIClient()
        response = api_client.patch("/api/license_components/1/concluded_license/", patch_data, format="json")

        self.assertEqual(response.status_code, 200)
        mock_save_concluded_license.assert_called_once_with(License_Component.objects.get(pk=1))
