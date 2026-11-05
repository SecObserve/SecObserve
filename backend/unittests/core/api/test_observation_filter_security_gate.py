from unittest.mock import patch

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from application.core.types import Severity
from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin


class TestObservationFailsSecurityGateFilter(ObservationFixtureMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        self.product_1.security_gate_active = True
        self.product_1.security_gate_threshold_critical = 0
        self.product_1.security_gate_threshold_high = 99999
        self.product_1.security_gate_threshold_medium = 99999
        self.product_1.security_gate_threshold_low = 99999
        self.product_1.security_gate_threshold_none = 99999
        self.product_1.security_gate_threshold_unknown = 99999
        self.product_1.security_gate_priority_thresholds = [{"priority": 1, "threshold": 0}]
        self.product_1.save()
        self._observation("crit")
        self._observation("p1", severity=Severity.SEVERITY_MEDIUM, priority=1)
        self._observation("low", severity=Severity.SEVERITY_LOW)
        # A class level patch breaks setUpClass when the whole suite runs
        patcher = patch(
            "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        )
        mock_authentication = patcher.start()
        self.addCleanup(patcher.stop)
        mock_authentication.return_value = self.user_admin, None

    def _titles(self, response):
        return sorted(row["title"] for row in response.data["results"])

    def test_fails_filter_returns_exceeded_severities_and_priorities(self):
        response = APIClient().get(f"/api/observations/?product={self.product_1.pk}&fails_security_gate=true")

        self.assertEqual(self._titles(response), ["crit", "p1"])

    def test_fails_filter_when_gate_passes(self):
        self.product_1.security_gate_threshold_critical = 99999
        self.product_1.security_gate_priority_thresholds = []
        self.product_1.save()

        response = APIClient().get(f"/api/observations/?product={self.product_1.pk}&fails_security_gate=true")

        self.assertEqual(self._titles(response), [])

    def test_fails_filter_without_product_is_noop(self):
        response = APIClient().get("/api/observations/?fails_security_gate=true")

        self.assertEqual(HTTP_200_OK, response.status_code)
        # Other test classes may have loaded more observations, all of ours have to be there
        self.assertLessEqual({"crit", "p1", "low"}, set(self._titles(response)))
