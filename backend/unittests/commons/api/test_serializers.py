from application.commons.api.serializers import SettingsSerializer
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase

SCANCODEIO_SETTINGS = {
    "scancodeio_base_url": "http://nginx",
    "scancodeio_api_key": "api_key",
    "scancodeio_webhook_base_url": "http://backend:8000",
}


class TestSettingsSerializer(BaseTestCase):
    def test_scancodeio_enabled_with_all_settings(self):
        serializer = SettingsSerializer(
            Settings(), data={"feature_scancodeio_integration": True, **SCANCODEIO_SETTINGS}, partial=True
        )

        self.assertTrue(serializer.is_valid())

    def test_scancodeio_enabled_without_settings(self):
        serializer = SettingsSerializer(
            Settings(),
            data={
                "feature_scancodeio_integration": True,
                "scancodeio_base_url": "",
                "scancodeio_api_key": "",
                "scancodeio_webhook_base_url": "",
            },
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            serializer.errors,
            {
                "scancodeio_base_url": [
                    "ScanCode.io base URL is required when the ScanCode.io integration is enabled."
                ],
                "scancodeio_api_key": ["ScanCode.io API key is required when the ScanCode.io integration is enabled."],
                "scancodeio_webhook_base_url": [
                    "SecObserve URL for ScanCode.io webhooks is required when the ScanCode.io integration is enabled."
                ],
            },
        )

    def test_scancodeio_enabled_with_one_setting_missing(self):
        serializer = SettingsSerializer(
            Settings(),
            data={"feature_scancodeio_integration": True, **SCANCODEIO_SETTINGS, "scancodeio_api_key": ""},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(list(serializer.errors.keys()), ["scancodeio_api_key"])

    def test_scancodeio_disabled_without_settings(self):
        serializer = SettingsSerializer(
            Settings(),
            data={
                "feature_scancodeio_integration": False,
                "scancodeio_base_url": "",
                "scancodeio_api_key": "",
                "scancodeio_webhook_base_url": "",
            },
            partial=True,
        )

        self.assertTrue(serializer.is_valid())

    def test_scancodeio_partial_update_with_stored_settings(self):
        serializer = SettingsSerializer(
            Settings(**SCANCODEIO_SETTINGS), data={"feature_scancodeio_integration": True}, partial=True
        )

        self.assertTrue(serializer.is_valid())

    def test_scancodeio_partial_update_without_stored_settings(self):
        serializer = SettingsSerializer(Settings(), data={"feature_scancodeio_integration": True}, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            set(serializer.errors.keys()),
            {"scancodeio_base_url", "scancodeio_api_key", "scancodeio_webhook_base_url"},
        )

    def test_scancodeio_partial_update_clearing_setting_of_enabled_integration(self):
        serializer = SettingsSerializer(
            Settings(feature_scancodeio_integration=True, **SCANCODEIO_SETTINGS),
            data={"scancodeio_base_url": ""},
            partial=True,
        )

        self.assertFalse(serializer.is_valid())
        self.assertEqual(list(serializer.errors.keys()), ["scancodeio_base_url"])
