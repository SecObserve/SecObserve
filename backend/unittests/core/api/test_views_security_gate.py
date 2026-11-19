from unittest.mock import patch

from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin


class TestSecurityGateCounts(ObservationFixtureMixin, BaseTestCase):
    def setUp(self):
        super().setUp()
        # A class level patch breaks setUpClass when the whole suite runs
        patcher = patch(
            "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"
        )
        mock_authentication = patcher.start()
        self.addCleanup(patcher.stop)
        mock_authentication.return_value = self.user_admin, None

    def test_counts_rows_for_configured_gate(self):
        self.product_1.security_gate_active = True
        self.product_1.security_gate_threshold_critical = 0
        self.product_1.security_gate_threshold_high = 99999
        self.product_1.security_gate_threshold_medium = 99999
        self.product_1.security_gate_threshold_low = 99999
        self.product_1.security_gate_threshold_none = 99999
        self.product_1.security_gate_threshold_unknown = 99999
        self.product_1.security_gate_priority_thresholds = [
            {"priority": 1, "threshold": 0},
            {"priority": 3, "threshold": 5},
        ]
        self.product_1.save()
        self._observation("p1", priority=1)

        response = APIClient().get(f"/api/products/{self.product_1.pk}/security_gate_counts/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(
            [row["severity"] for row in response.data[:6]], ["Critical", "High", "Medium", "Low", "None", "Unknown"]
        )
        self.assertEqual(
            response.data[0], {"severity": "Critical", "priority": None, "count": 1, "threshold": 0, "passed": False}
        )
        self.assertEqual(
            response.data[6], {"severity": None, "priority": 1, "count": 1, "threshold": 0, "passed": False}
        )
        self.assertEqual(
            response.data[7], {"severity": None, "priority": 3, "count": 0, "threshold": 5, "passed": True}
        )

    def test_counts_empty_without_gate(self):
        self.product_1.security_gate_active = False
        self.product_1.save()

        response = APIClient().get(f"/api/products/{self.product_1.pk}/security_gate_counts/")

        self.assertEqual(response.data, [])

    def test_counts_empty_for_product_group(self):
        self.product_group_1.is_product_group = True
        self.product_group_1.security_gate_active = True
        self.product_group_1.save()

        response = APIClient().get(f"/api/products/{self.product_group_1.pk}/security_gate_counts/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(response.data, [])
