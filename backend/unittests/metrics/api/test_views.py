from datetime import datetime, timezone
from unittest.mock import patch

from django.test import override_settings
from rest_framework.status import HTTP_200_OK
from rest_framework.test import APIClient

from application.metrics.models import Product_Metrics_Status
from unittests.base_test_case import BaseTestCase


class TestProductMetricsStatusView(BaseTestCase):
    @override_settings(TIME_ZONE="Asia/Ho_Chi_Minh")
    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_last_calculated_in_time_zone(self, mock_authentication):
        mock_authentication.return_value = self.user_internal, None
        Product_Metrics_Status(last_calculated=datetime(2026, 3, 10, 20, 0, tzinfo=timezone.utc)).save()

        response = APIClient().get("/api/metrics/product_metrics_status/")

        self.assertEqual(HTTP_200_OK, response.status_code)
        self.assertEqual(
            {"last_calculated": "2026-03-11T03:00:00+07:00", "calculation_interval": 5},
            response.json(),
        )
