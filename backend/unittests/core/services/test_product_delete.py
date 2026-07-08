from unittest.mock import patch

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Observation,
    Product,
    Product_Delete_Request,
    Product_Member,
)
from application.core.services.product_delete import (
    approve_product_delete_request,
    force_delete_product,
    reject_product_delete_request,
    request_product_delete,
    undo_product_delete_request,
)
from application.core.types import Status
from application.import_observations.models import Parser
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from unittests.base_test_case import BaseTestCase


class TestProductDelete(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner = User.objects.create(username="owner@example.com")
        self.maintainer = User.objects.create(username="maintainer@example.com")
        self.writer = User.objects.create(username="writer@example.com")
        self.parser = Parser.objects.create(name="parser")

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_force_delete_product_deletes_blocking_records(self, mock_issue_tracker):
        product = self._create_product_with_records("product")

        force_delete_product(product, "product")

        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(0, Observation.objects.filter(product_id=product.pk).count())
        self.assertEqual(0, License_Component.objects.filter(product_id=product.pk).count())
        mock_issue_tracker.assert_called_once()

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_force_delete_product_rejects_wrong_confirmation(self, mock_issue_tracker):
        product = self._create_product_with_records("product")

        with self.assertRaises(ValidationError):
            force_delete_product(product, "wrong")

        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(1, Observation.objects.filter(product=product).count())
        self.assertEqual(1, License_Component.objects.filter(product=product).count())
        mock_issue_tracker.assert_not_called()

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_force_delete_product_group_deletes_child_products(self, mock_issue_tracker):
        product_group = Product.objects.create(name="product_group", is_product_group=True)
        child_product = self._create_product_with_records("product", product_group)

        force_delete_product(product_group, "product_group")

        self.assertFalse(Product.objects.filter(pk=product_group.pk).exists())
        self.assertFalse(Product.objects.filter(pk=child_product.pk).exists())
        self.assertEqual(0, Observation.objects.filter(product_id=child_product.pk).count())
        self.assertEqual(0, License_Component.objects.filter(product_id=child_product.pk).count())
        mock_issue_tracker.assert_called_once()

    @patch("application.core.services.product_delete.send_product_delete_request_notification")
    def test_maintainer_requests_product_delete(self, mock_notification):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)

        delete_request = request_product_delete(product, self.maintainer)

        self.assertEqual(product, delete_request.product)
        self.assertEqual(self.maintainer, delete_request.user)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        mock_notification.assert_called_once_with(delete_request)

    def test_duplicate_delete_request_is_rejected(self):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        request_product_delete(product, self.maintainer)

        with self.assertRaises(ValidationError):
            request_product_delete(product, self.maintainer)

        self.assertEqual(1, Product_Delete_Request.objects.filter(product=product).count())

    def test_owner_delete_request_is_rejected(self):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)

        with self.assertRaises(ValidationError):
            request_product_delete(product, self.owner)

    def test_writer_delete_request_is_rejected(self):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.writer, role=Roles.Writer)

        with self.assertRaises(PermissionDenied):
            request_product_delete(product, self.writer)

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_approve_product_delete_request_deletes_product(self, mock_issue_tracker):
        product = self._create_product_with_records("product")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        request_product_delete(product, self.maintainer)

        approve_product_delete_request(product, "product")

        self.assertFalse(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(0, Product_Delete_Request.objects.filter(product_id=product.pk).count())
        mock_issue_tracker.assert_called_once()

    def test_reject_product_delete_request_keeps_product(self):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        request_product_delete(product, self.maintainer)

        reject_product_delete_request(product)

        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(0, Product_Delete_Request.objects.filter(product=product).count())

    def test_undo_product_delete_request_keeps_product(self):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        request_product_delete(product, self.maintainer)

        undo_product_delete_request(product, self.maintainer)

        self.assertTrue(Product.objects.filter(pk=product.pk).exists())
        self.assertEqual(0, Product_Delete_Request.objects.filter(product=product).count())

    def test_undo_product_delete_request_for_other_user_is_rejected(self):
        product = Product.objects.create(name="product")
        Product_Member.objects.create(product=product, user=self.maintainer, role=Roles.Maintainer)
        request_product_delete(product, self.maintainer)

        with self.assertRaises(PermissionDenied):
            undo_product_delete_request(product, self.writer)

        self.assertEqual(1, Product_Delete_Request.objects.filter(product=product).count())

    def _create_product_with_records(self, name: str, product_group: Product = None) -> Product:
        product = Product.objects.create(name=name, product_group=product_group)
        Observation.objects.create(
            title=f"{name}_observation",
            product=product,
            parser=self.parser,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
        )
        License_Component.objects.create(
            identity_hash=f"{name}_license_component",
            product=product,
            component_name=f"{name}_component",
            component_name_version=f"{name}_component:1.0.0",
            evaluation_result=License_Policy_Evaluation_Result.RESULT_UNKNOWN,
            numerical_evaluation_result=License_Policy_Evaluation_Result.NUMERICAL_RESULTS[
                License_Policy_Evaluation_Result.RESULT_UNKNOWN
            ],
        )
        return product
