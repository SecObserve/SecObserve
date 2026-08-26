from unittest.mock import patch

from django.core.management import call_command
from django.utils import timezone
from rest_framework.serializers import ValidationError

from application.access_control.models import User
from application.core.api.serializers_product import (
    ProductGroupSerializer,
    ProductSerializer,
)
from application.core.models import Observation, Observation_Log, Product
from application.core.types import Assessment_Status, Severity, Status
from application.import_observations.models import Parser
from unittests.base_test_case import BaseTestCase


def _create_observation_log_needing_approval(product: Product) -> None:
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


class TestProductObservationLogApprovalsCount(BaseTestCase):
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

    def test_observation_log_approvals_counted_without_any_flag(self):
        product = Product.objects.get(name="db_product_external")
        _create_observation_log_needing_approval(product)

        self.assertEqual(1, ProductSerializer().get_observation_log_approvals(product))

    def test_observation_log_approvals_counted_with_group_flag_only(self):
        product = Product.objects.get(name="db_product_internal")
        product.product_group.assessments_need_approval = True
        product.product_group.save()
        _create_observation_log_needing_approval(product)

        self.assertEqual(1, ProductSerializer().get_observation_log_approvals(product))


class TestAssessmentsNeedApprovalValidation(BaseTestCase):
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

    def test_product_disable_flag_blocked_with_pending_approvals(self):
        product = Product.objects.get(name="db_product_external")
        product.assessments_need_approval = True
        product.save()
        _create_observation_log_needing_approval(product)

        with self.assertRaises(ValidationError) as e:
            ProductSerializer(product).validate({"assessments_need_approval": False})

        self.assertIn(
            "Assessment approval cannot be disabled while 1 assessment(s) are pending approval",
            str(e.exception),
        )

    def test_product_disable_flag_allowed_without_pending_approvals(self):
        product = Product.objects.get(name="db_product_external")
        product.assessments_need_approval = True
        product.save()

        attrs = ProductSerializer(product).validate({"assessments_need_approval": False})

        self.assertEqual({"assessments_need_approval": False}, attrs)

    def test_product_disable_flag_allowed_when_group_flag_on(self):
        product = Product.objects.get(name="db_product_internal")
        product.assessments_need_approval = True
        product.save()
        product.product_group.assessments_need_approval = True
        product.product_group.save()
        _create_observation_log_needing_approval(product)

        attrs = ProductSerializer(product).validate({"assessments_need_approval": False})

        self.assertEqual({"assessments_need_approval": False}, attrs)

    def test_product_move_out_of_group_blocked_with_pending_approvals(self):
        product = Product.objects.get(name="db_product_internal")
        product.product_group.assessments_need_approval = True
        product.product_group.save()
        _create_observation_log_needing_approval(product)

        with self.assertRaises(ValidationError):
            ProductSerializer(product).validate({"product_group": None})

    def test_product_move_to_flag_on_group_allowed(self):
        product = Product.objects.get(name="db_product_external")
        product.assessments_need_approval = True
        product.save()
        product_group = Product.objects.get(name="db_product_group")
        product_group.assessments_need_approval = True
        product_group.save()
        _create_observation_log_needing_approval(product)

        attrs = ProductSerializer(product).validate(
            {"assessments_need_approval": False, "product_group": product_group}
        )

        self.assertEqual(False, attrs["assessments_need_approval"])

    def test_product_patch_without_flag_key_allowed(self):
        product = Product.objects.get(name="db_product_external")
        product.assessments_need_approval = True
        product.save()
        _create_observation_log_needing_approval(product)

        attrs = ProductSerializer(product).validate({"description": "unrelated change"})

        self.assertEqual({"description": "unrelated change"}, attrs)

    def test_create_not_blocked(self):
        attrs = ProductSerializer().validate({"assessments_need_approval": False})

        self.assertEqual({"assessments_need_approval": False}, attrs)

    def test_group_disable_flag_blocked_with_orphaned_pending(self):
        product_group = Product.objects.get(name="db_product_group")
        product_group.assessments_need_approval = True
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        _create_observation_log_needing_approval(product)

        with self.assertRaises(ValidationError) as e:
            ProductGroupSerializer(product_group).validate({"assessments_need_approval": False})

        self.assertIn(
            "Assessment approval cannot be disabled while 1 assessment(s) are pending approval",
            str(e.exception),
        )

    def test_group_disable_flag_allowed_when_member_has_own_flag(self):
        product_group = Product.objects.get(name="db_product_group")
        product_group.assessments_need_approval = True
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        product.assessments_need_approval = True
        product.save()
        _create_observation_log_needing_approval(product)

        attrs = ProductGroupSerializer(product_group).validate({"assessments_need_approval": False})

        self.assertEqual({"assessments_need_approval": False}, attrs)

    def test_group_disable_flag_allowed_without_pending(self):
        product_group = Product.objects.get(name="db_product_group")
        product_group.assessments_need_approval = True
        product_group.save()

        attrs = ProductGroupSerializer(product_group).validate({"assessments_need_approval": False})

        self.assertEqual({"assessments_need_approval": False}, attrs)
