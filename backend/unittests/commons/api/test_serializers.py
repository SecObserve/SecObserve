from application.commons.api.serializers import SettingsSerializer
from application.commons.models import Settings
from unittests.base_test_case import BaseTestCase

SCANCODEIO_SETTINGS = {
    "scancodeio_base_url": "http://nginx",
    "scancodeio_api_key": "api_key",
    "scancodeio_webhook_base_url": "http://backend:8000",
}

BASE_URL_FIELDS = ["vulnerablecode_base_url", "scancodeio_base_url", "scancodeio_webhook_base_url"]


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

    def test_base_urls_valid(self):
        for url in [
            "",
            "http://nginx",
            "http://backend:8000",
            "http://localhost:8000",
            "http://10.0.0.1",
            "https://scancode.example.com/",
            "https://example.com/scancode",
            "HTTPS://example.com",
        ]:
            for field in BASE_URL_FIELDS:
                serializer = SettingsSerializer(Settings(), data={field: url}, partial=True)

                self.assertTrue(serializer.is_valid(), f"{field}: {url}: {serializer.errors}")

    def test_base_urls_invalid(self):
        for url in [
            "nginx",
            "//nginx",
            "file:///etc/passwd",
            "ftp://example.com",
            "javascript:alert(1)//",
            "http://",
            "http://:8000",
            "http://example.com:port",
            "http://[::1",
            "http://user:password@example.com",
            "http://user@example.com",
            "http://example.com\\@evil.test",
            "http://example.com/?a=b",
            "http://example.com/?",
            "http://example.com/#",
            "http://evil.test/secret#",
            "http://exa mple.com",
        ]:
            for field in BASE_URL_FIELDS:
                serializer = SettingsSerializer(Settings(), data={field: url}, partial=True)

                self.assertFalse(serializer.is_valid(), f"{field}: {url}")
                self.assertEqual(
                    serializer.errors, {field: ["Enter an http(s) URL without credentials, query or fragment."]}
                )

    def test_feature_full_text_search_serialized(self):
        self.assertTrue(SettingsSerializer(Settings(feature_full_text_search=True)).data["feature_full_text_search"])

    def test_feature_full_text_search_not_writable(self):
        serializer = SettingsSerializer(Settings(), data={"feature_full_text_search": True}, partial=True)

        self.assertTrue(serializer.is_valid())
        self.assertNotIn("feature_full_text_search", serializer.validated_data)
