from unittest.mock import patch

from django.core.cache import cache
from rest_framework.test import APIClient

from application.access_control.api.views import LoginRateThrottle
from unittests.base_test_case import BaseTestCase

AUTHENTICATE_URL = "/api/authentication/authenticate/"
CREATE_TOKEN_URL = "/api/authentication/create_user_api_token/"


@patch.object(LoginRateThrottle, "rate", "2/minute", create=True)
class TestLoginThrottle(BaseTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.api_client = APIClient()

    def _post(self, url: str, username: str = "alice"):
        return self.api_client.post(url, {"username": username, "password": "wrong"}, format="json")

    def test_authenticate_throttled_per_username(self):
        self.assertNotEqual(429, self._post(AUTHENTICATE_URL).status_code)
        self.assertNotEqual(429, self._post(AUTHENTICATE_URL).status_code)

        response = self._post(AUTHENTICATE_URL)

        self.assertEqual(429, response.status_code)
        self.assertIn("Retry-After", response)

    def test_username_case_counts_together(self):
        self._post(AUTHENTICATE_URL, "alice")
        self._post(AUTHENTICATE_URL, "ALICE")

        self.assertEqual(429, self._post(AUTHENTICATE_URL, "Alice").status_code)

    def test_username_variants_count_together(self):
        for variant in [" alice ", "ALICE", "Álice", "al\u00adice"]:
            with self.subTest(variant=variant):
                cache.clear()
                self._post(AUTHENTICATE_URL, "alice")
                self._post(AUTHENTICATE_URL, variant)

                self.assertEqual(429, self._post(AUTHENTICATE_URL, "alice").status_code)

    def test_other_username_unaffected(self):
        for _ in range(3):
            self._post(AUTHENTICATE_URL, "alice")

        self.assertNotEqual(429, self._post(AUTHENTICATE_URL, "bob").status_code)

    def test_no_username_not_throttled(self):
        for _ in range(5):
            response = self.api_client.post(AUTHENTICATE_URL, {"password": "wrong"}, format="json")
            self.assertNotEqual(429, response.status_code)

    def test_non_string_username_not_throttled(self):
        for _ in range(5):
            response = self.api_client.post(AUTHENTICATE_URL, {"username": ["a"], "password": "x"}, format="json")
            self.assertNotEqual(429, response.status_code)

    def test_malformed_body_bad_request(self):
        response = self.api_client.post(AUTHENTICATE_URL, "{not json", content_type="application/json")

        self.assertEqual(400, response.status_code)

    def test_create_token_throttled(self):
        self._post(CREATE_TOKEN_URL)
        self._post(CREATE_TOKEN_URL)

        self.assertEqual(429, self._post(CREATE_TOKEN_URL).status_code)

    def test_create_token_whitespace_variant_throttled(self):
        self._post(CREATE_TOKEN_URL, "alice")
        self._post(CREATE_TOKEN_URL, " alice")

        self.assertEqual(429, self._post(CREATE_TOKEN_URL, "alice ").status_code)

    def test_endpoints_share_the_username_counter(self):
        self._post(AUTHENTICATE_URL)
        self._post(CREATE_TOKEN_URL)

        self.assertEqual(429, self._post(AUTHENTICATE_URL).status_code)
