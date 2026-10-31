from datetime import datetime, timezone
from io import StringIO
from unittest.mock import patch

from defusedcsv import csv
from rest_framework.test import APIClient

from application.access_control.models import User
from application.commons.models import Settings
from application.core.models import Observation, Observation_Log, Product
from application.core.services.export_observation_logs import COLUMNS
from application.core.types import Assessment_Status
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase

HEADERS = [column.header for column in COLUMNS]


class TestExportObservationLogs(BaseTestCase):
    def setUp(self):
        super().setUp()
        settings = Settings.load()
        settings.base_url_frontend = "https://secobserve.example.com"
        settings.save()

        self.admin = User.objects.create(username="admin_log_export", full_name="Admin", is_superuser=True)
        assessor = User.objects.create(username="assessor_log_export", full_name="Assessor")
        parser = Parser.objects.create(name="parser_log_export", type="SCA", source="File")
        product = Product.objects.create(name="product_log_export")
        observation = Observation.objects.create(
            product=product,
            title="observation_log_export",
            parser=parser,
            import_last_seen=datetime(2026, 10, 27, tzinfo=timezone.utc),
        )
        self.decided = Observation_Log.objects.create(
            observation=observation,
            user=assessor,
            comment="approver comment",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS,
            approval_user=self.admin,
            assessor_values={"comment": "assessor comment"},
        )
        Observation_Log.objects.create(observation=observation, user=assessor, comment="auto approved")

    @patch("application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate")
    def test_api_export_csv_with_filter(self, mock_authenticate):
        mock_authenticate.return_value = self.admin, None

        response = APIClient().get("/api/observation_logs/export_csv/?decided=true")

        self.assertEqual(200, response.status_code)
        rows = list(csv.reader(StringIO(response.content.decode())))
        self.assertEqual(HEADERS, rows[0])
        self.assertEqual(2, len(rows))
        row = dict(zip(HEADERS, rows[1]))
        self.assertEqual("Admin", row["Approver"])
        self.assertEqual('{"comment": "assessor comment"}', row["Values of the assessor"])
        self.assertEqual(
            f"https://secobserve.example.com/#/observation_logs/{self.decided.pk}/show", row["Assessment URL"]
        )
