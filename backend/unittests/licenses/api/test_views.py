from unittest.mock import ANY, patch

from django.core.management import call_command
from rest_framework.test import APIClient

from application.access_control.models import User
from application.licenses.models import License, License_Component, License_Group
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


class TestLicenseScancodeCategories(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create(username="test_scancode_categories@example.com")
        License.objects.create(spdx_id="Test-Category-1", name="Test 1", scancode_category="Permissive")
        copyleft = License.objects.create(spdx_id="Test-Category-2", name="Test 2", scancode_category="Copyleft")
        License.objects.create(spdx_id="Test-Category-3", name="Test 3", scancode_category="Permissive")
        License.objects.create(spdx_id="Test-Category-4", name="Test 4", scancode_category="")
        self.license_group = License_Group.objects.create(name="Test category group", is_public=True)
        self.license_group.licenses.add(copyleft)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_scancode_categories(self, mock_authenticate):
        mock_authenticate.return_value = self.user, None

        response = APIClient().get("/api/licenses/scancode_categories/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual({"scancode_categories": ["Copyleft", "Permissive"]}, response.data)

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_scancode_categories_license_group(self, mock_authenticate):
        mock_authenticate.return_value = self.user, None

        response = APIClient().get(f"/api/licenses/scancode_categories/?license_groups={self.license_group.pk}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual({"scancode_categories": ["Copyleft"]}, response.data)
