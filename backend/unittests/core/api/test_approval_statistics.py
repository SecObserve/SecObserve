from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from rest_framework.test import APIClient

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Observation,
    Observation_Log,
    Product,
    Product_Member,
)
from application.core.services.approval_statistics import get_approval_statistics
from application.core.types import Assessment_Status
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase

AUTHENTICATE = "application.access_control.services.api_token_authentication.APITokenAuthentication.authenticate"


class TestApprovalStatistics(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create(username="statistics_admin", is_superuser=True)
        self.reader = User.objects.create(username="statistics_reader")
        self.maintainer = User.objects.create(username="statistics_maintainer")
        assessor = User.objects.create(username="statistics_assessor")
        approver_a = User.objects.create(username="statistics_a", full_name="A")
        approver_b = User.objects.create(username="statistics_b", full_name="B")
        self.product = Product.objects.create(name="statistics_product")
        Product_Member.objects.create(product=self.product, user=self.reader, role=Roles.Reader)
        Product_Member.objects.create(product=self.product, user=self.maintainer, role=Roles.Maintainer)
        observation = Observation.objects.create(
            product=self.product,
            title="statistics_observation",
            parser=Parser.objects.create(name="statistics_parser", type="SCA", source="File"),
            import_last_seen=datetime(2026, 10, 27, tzinfo=timezone.utc),
        )
        for approver, assessment_status, hours in [
            (approver_a, Assessment_Status.ASSESSMENT_STATUS_APPROVED, 2),
            (approver_a, Assessment_Status.ASSESSMENT_STATUS_REJECTED, 4),
            (approver_b, Assessment_Status.ASSESSMENT_STATUS_APPROVED_WITH_EDITS, 1),
            (None, Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL, 0),
        ]:
            log = Observation_Log.objects.create(
                observation=observation, user=assessor, comment="c", assessment_status=assessment_status
            )
            if approver:
                log.approval_user = approver
                log.approval_date = log.created + timedelta(hours=hours)
                log.save()

    def test_statistics(self):
        statistics = get_approval_statistics(Observation_Log.objects.filter(observation__product=self.product))

        self.assertEqual(["A", "B"], [entry["approval_user_full_name"] for entry in statistics])
        self.assertEqual((1, 0, 1, 2, 3.0), self._counts(statistics[0]))
        self.assertEqual((0, 1, 0, 1, 1.0), self._counts(statistics[1]))

    @patch(AUTHENTICATE)
    def test_api_permissions(self, mock_authenticate):
        for user, query, status_code in [
            (self.superuser, "", 200),
            (self.maintainer, "", 403),
            (self.maintainer, f"?product={self.product.pk}", 200),
            (self.reader, f"?product={self.product.pk}", 403),
        ]:
            with self.subTest(user=user.username, query=query):
                mock_authenticate.return_value = user, None

                response = APIClient().get("/api/observation_logs/approval_statistics/" + query)

                self.assertEqual(status_code, response.status_code)

    def _counts(self, entry):
        return (
            entry["approved"],
            entry["approved_with_edits"],
            entry["rejected"],
            entry["total"],
            entry["average_decision_hours"],
        )
