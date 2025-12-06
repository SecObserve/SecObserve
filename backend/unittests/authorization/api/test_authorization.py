from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional
from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from application.access_control.models import User
from application.metrics.models import Product_Metrics
from unittests.base_test_case import BaseTestCase


@dataclass
class APITest:
    username: str
    method: str
    url: str
    post_data: str
    expected_status_code: int
    expected_data: str
    no_second_user: Optional[bool] = False
    expected_data_product_group: Optional[str] = None


class TestAuthorizationBase(BaseTestCase):
    patch.TEST_PREFIX = (
        "test",
        "setUp",
    )

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(self, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )

        product_metrics = Product_Metrics.objects.get(pk=1)
        product_metrics.date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        product_metrics.save()
        product_metrics = Product_Metrics.objects.get(pk=2)
        product_metrics.date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        product_metrics.save()
        product_metrics = Product_Metrics.objects.get(pk=3)
        product_metrics.date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        product_metrics.save()
        product_metrics = Product_Metrics.objects.get(pk=4)
        product_metrics.date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        product_metrics.save()

        super().setUpClass()

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    @patch("application.core.api.serializers_product.calculate_risk_acceptance_expiry_date")
    def _test_api(self, data: APITest, mock_product_expiry_date, mock_authentication):
        user = User.objects.get(username=data.username)
        mock_authentication.return_value = user, None

        mock_product_expiry_date.return_value = date(2024, 7, 1)

        api_client = APIClient()
        if data.method.lower() == "delete":
            response = api_client.delete(data.url)
        elif data.method.lower() == "get":
            response = api_client.get(data.url)
        elif data.method.lower() == "patch":
            response = api_client.patch(data.url, data.post_data, format="json")
        elif data.method.lower() == "post":
            response = api_client.post(data.url, data.post_data, format="json")
        elif data.method.lower() == "put":
            response = api_client.put(data.url, data.post_data, format="json")
        else:
            raise Exception(f"Unknown method: {data.method}")

        self.assertEqual(data.expected_status_code, response.status_code)
        if data.expected_data:
            self.assertEqual(data.expected_data, str(response.data))

        if (
            not data.no_second_user
            and data.username == "db_internal_write"
            and data.method.lower() != "post"
            and data.method.lower() != "delete"
        ):
            user = User.objects.get(username="db_product_group_user")
            mock_authentication.return_value = user, None

            api_client = APIClient()
            if data.method.lower() == "delete":
                response = api_client.delete(data.url)
            elif data.method.lower() == "get":
                response = api_client.get(data.url)
            elif data.method.lower() == "patch":
                response = api_client.patch(data.url, data.post_data, format="json")
            elif data.method.lower() == "post":
                response = api_client.post(data.url, data.post_data, format="json")
            elif data.method.lower() == "put":
                response = api_client.put(data.url, data.post_data, format="json")
            else:
                raise Exception(f"Unknown method: {data.method}")

            self.assertEqual(data.expected_status_code, response.status_code)
            if data.expected_data_product_group:
                self.assertEqual(data.expected_data_product_group, str(response.data))
            elif data.expected_data:
                self.assertEqual(data.expected_data, str(response.data))
