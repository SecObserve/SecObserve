from unittest.mock import patch

from django.core.management import call_command
from rest_framework.test import APIClient

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import Product
from unittests.base_test_case import BaseTestCase


@patch("application.scancodeio.api.views.create_scancodeio_project")
@patch("application.scancodeio.api.views.Settings.load")
@patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
class TestCreateScanCodeIOProjectView(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpTestData(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
            ],
        )

    def _post(self, username: str, product_id: int, mock_authenticate):
        mock_authenticate.return_value = User.objects.get(username=username), None
        api_client = APIClient()
        return api_client.post(f"/api/products/{product_id}/create_scancodeio_project/")

    def test_product_not_found(self, mock_authenticate, mock_settings_load, mock_create):
        mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_admin", 99999, mock_authenticate)

        self.assertEqual(response.status_code, 404)
        mock_create.assert_not_called()

    def test_no_permission(self, mock_authenticate, mock_settings_load, mock_create):
        mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_internal_read", 1, mock_authenticate)

        self.assertEqual(response.status_code, 403)
        mock_create.assert_not_called()

    def test_feature_disabled(self, mock_authenticate, mock_settings_load, mock_create):
        mock_settings_load.return_value = Settings(feature_scancodeio_integration=False)

        response = self._post("db_internal_write", 1, mock_authenticate)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(str(response.data), "{'message': 'ScanCode.io integration is not enabled'}")
        mock_create.assert_not_called()

    def test_success(self, mock_authenticate, mock_settings_load, mock_create):
        mock_settings_load.return_value = Settings(feature_scancodeio_integration=True)

        response = self._post("db_internal_write", 1, mock_authenticate)

        self.assertEqual(response.status_code, 204)
        mock_create.assert_called_once_with(Product.objects.get(pk=1))
