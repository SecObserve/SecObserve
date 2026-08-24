from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone

from application.access_control.models import User
from application.core.api.serializers_product import ProductGroupSerializer
from application.core.models import Observation, Observation_Log, Product
from application.core.types import Assessment_Status, Severity, Status
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase


class TestProductGroupObservationLogApprovals(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )
        super().setUpClass()

    def _create_observation_log_needing_approval(self, product: Product) -> None:
        observation = Observation.objects.create(
            title="observation_log_approval",
            product=product,
            parser=Parser.objects.first(),
            parser_severity=Severity.SEVERITY_HIGH,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )
        Observation_Log.objects.create(
            observation=observation,
            user=User.objects.get(username="db_admin"),
            severity=Severity.SEVERITY_HIGH,
            status=Status.STATUS_OPEN,
            comment="needs approval",
            assessment_status=Assessment_Status.ASSESSMENT_STATUS_NEEDS_APPROVAL,
        )

    def test_observation_log_approvals(self):
        product_group = Product.objects.get(name="db_product_group")
        product = Product.objects.filter(product_group=product_group).first()
        self._create_observation_log_needing_approval(product)
        serializer = ProductGroupSerializer()

        # Approvals are not required, neither by the product group nor by one of its products
        self.assertEqual(0, serializer.get_observation_log_approvals(product_group))

        # Approvals are required by a product of the group individually
        product.assessments_need_approval = True
        product.save()
        self.assertEqual(1, serializer.get_observation_log_approvals(product_group))

        # Approvals are required by the product group
        product.assessments_need_approval = False
        product.save()
        product_group.assessments_need_approval = True
        product_group.save()
        self.assertEqual(1, serializer.get_observation_log_approvals(product_group))
