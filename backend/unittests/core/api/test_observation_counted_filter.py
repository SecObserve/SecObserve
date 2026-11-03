from unittest.mock import patch

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin


class TestObservationCountedBySecurityGateFilter(ObservationFixtureMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_1.security_gate_active = True
        self.product_1.security_gate_advanced = True
        self.product_1.security_gate_conditions = {"default": [{"known_exploited": True}]}
        self.product_1.save()
        self.kev = self._observation("kev", cve_found_in="CISA KEV")
        self.plain = self._observation("plain")
        # A class level patch breaks setUpClass when the whole suite runs
        patcher = patch(
            "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        )
        mock_authentication = patcher.start()
        self.addCleanup(patcher.stop)
        mock_authentication.return_value = self.user_admin, None

    def _titles(self, response):
        return sorted(row["title"] for row in response.data["results"])

    def test_counted_filter_applies_rules(self):
        response = APIClient().get(f"/api/observations/?product={self.product_1.pk}&counted_by_security_gate=true")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(self._titles(response), ["kev"])

    def test_counted_filter_false_is_noop(self):
        response = APIClient().get(f"/api/observations/?product={self.product_1.pk}&counted_by_security_gate=false")

        self.assertEqual(self._titles(response), ["kev", "plain"])

    def test_counted_filter_without_product_is_noop(self):
        response = APIClient().get("/api/observations/?counted_by_security_gate=true")

        self.assertEqual(HTTP_200_OK, response.status_code)
        # Other test classes may have loaded more observations, both of ours have to be there
        self.assertLessEqual({"kev", "plain"}, set(self._titles(response)))
