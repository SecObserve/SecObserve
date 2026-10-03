from datetime import datetime, timezone

from rest_framework.test import APIClient

from application.access_control.models import User
from application.core.models import Observation, Product
from application.core.types import Status
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase


class TestObservationLastObservationLogFilter(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.api_client = APIClient()
        self.api_client.force_authenticate(
            user=User.objects.create(username="last_log_filter@example.com", is_superuser=True)
        )
        self.product = Product.objects.create(name="last_log_filter_product")
        parser = Parser.objects.create(name="last_log_filter_parser")
        for title, last_observation_log in (
            ("obs_before", datetime(2026, 9, 30, 21, 59, 59, tzinfo=timezone.utc)),
            ("obs_first", datetime(2026, 9, 30, 22, 0, 0, tzinfo=timezone.utc)),
            ("obs_last", datetime(2026, 10, 1, 21, 59, 59, tzinfo=timezone.utc)),
            ("obs_after", datetime(2026, 10, 1, 22, 0, 0, tzinfo=timezone.utc)),
        ):
            observation = Observation.objects.create(
                title=title,
                product=self.product,
                parser=parser,
                parser_status=Status.STATUS_OPEN,
                import_last_seen=last_observation_log,
            )
            Observation.objects.filter(pk=observation.pk).update(last_observation_log=last_observation_log)

    def _titles(self, query: str) -> list[str]:
        # Other tests' observations stay in the database, the product keeps them out
        response = self.api_client.get(f"/api/observations/?product={self.product.pk}&ordering=id&{query}")
        self.assertEqual(200, response.status_code, response.data)
        return [observation["title"] for observation in response.data["results"]]

    def test_bounds_are_inclusive(self) -> None:
        self.assertEqual(
            ["obs_first", "obs_last"],
            self._titles(
                "last_observation_log_after=2026-09-30T22:00:00Z&last_observation_log_before=2026-10-01T21:59:59Z"
            ),
        )

    def test_one_bound_is_enough(self) -> None:
        self.assertEqual(["obs_last", "obs_after"], self._titles("last_observation_log_after=2026-10-01T21:59:59Z"))
        self.assertEqual(["obs_before", "obs_first"], self._titles("last_observation_log_before=2026-09-30T22:00:00Z"))

    def test_invalid_date_is_rejected(self) -> None:
        response = self.api_client.get("/api/observations/?last_observation_log_after=yesterday")

        self.assertEqual(400, response.status_code, response.data)
        self.assertIn("Enter a valid date/time.", response.data["message"])

    def test_export_applies_the_filter(self) -> None:
        response = self.api_client.get(
            f"/api/observations/export_csv/?product={self.product.pk}"
            "&last_observation_log_after=2026-09-30T22:00:00Z&last_observation_log_before=2026-10-01T21:59:59Z"
        )

        self.assertEqual(200, response.status_code)
        content = response.content.decode()
        self.assertIn("obs_first", content)
        self.assertIn("obs_last", content)
        self.assertNotIn("obs_before", content)
        self.assertNotIn("obs_after", content)

    def test_openapi_documents_both_parameters(self) -> None:
        response = self.api_client.get("/api/oa3/schema/?format=json")

        self.assertEqual(200, response.status_code)
        parameters = {
            parameter["name"]: parameter
            for parameter in response.data["paths"]["/api/observations/"]["get"]["parameters"]
        }
        for name in ("last_observation_log_after", "last_observation_log_before"):
            self.assertEqual("date-time", parameters[name]["schema"]["format"])
