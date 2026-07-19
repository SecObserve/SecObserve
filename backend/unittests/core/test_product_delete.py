from unittest.mock import patch

from django.db import transaction
from django.db.models.deletion import RestrictedError
from django.db.models.signals import post_delete
from django.utils import timezone

from application.access_control.models import User
from application.authorization.services.roles_permissions import Roles
from application.core.models import (
    Branch,
    Observation,
    Product,
    Product_Member,
    Service,
)
from application.core.types import Status
from application.import_observations.models import Api_Configuration, Parser
from application.licenses.models import License_Component
from application.licenses.types import License_Policy_Evaluation_Result
from application.rules.models import Rule
from application.vex.models import OpenVEX
from unittests.base_test_case import BaseTestCase


class TestProductDeleteCascade(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.owner = User.objects.create(username="delete-owner@example.com")
        self.external_user = User.objects.create(username="delete-external@example.com", is_external=True)
        self.parser = Parser.objects.create(name="delete-parser")

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_delete_product_cascades_all_product_records_after_commit(self, mock_issue_tracker) -> None:
        product = self._create_product_with_records("product")
        product_id = product.pk

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            product.delete()

        self.assertFalse(Product.objects.filter(pk=product_id).exists())
        self.assertFalse(Observation.objects.filter(product_id=product_id).exists())
        self.assertFalse(License_Component.objects.filter(product_id=product_id).exists())
        self.assertFalse(Branch.objects.filter(product_id=product_id).exists())
        self.assertFalse(Service.objects.filter(product_id=product_id).exists())
        self.assertFalse(Product_Member.objects.filter(product_id=product_id).exists())
        self.assertFalse(Api_Configuration.objects.filter(product_id=product_id).exists())
        self.assertFalse(Rule.objects.filter(product_id=product_id).exists())
        self.assertFalse(OpenVEX.objects.filter(product_id=product_id).exists())
        self.assertEqual(1, len(callbacks))
        mock_issue_tracker.assert_called_once()

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_delete_product_group_cascades_multiple_children_after_commit(self, mock_issue_tracker) -> None:
        product_group = Product.objects.create(name="product_group", is_product_group=True)
        self._add_blocking_records(product_group, "product_group")
        first_child = self._create_product_with_records("first_child", product_group)
        second_child = self._create_product_with_records("second_child", product_group)
        deleted_ids = [product_group.pk, first_child.pk, second_child.pk]

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            product_group.delete()

        self.assertFalse(Product.objects.filter(pk__in=deleted_ids).exists())
        self.assertFalse(Observation.objects.filter(product_id__in=deleted_ids).exists())
        self.assertFalse(License_Component.objects.filter(product_id__in=deleted_ids).exists())
        self.assertEqual(3, len(callbacks))
        self.assertEqual(3, mock_issue_tracker.call_count)

    def test_related_records_remain_protected_outside_product_cascade(self) -> None:
        product = self._create_product_with_records("protected_relations")

        for related_object in (
            Branch.objects.get(product=product),
            Service.objects.get(product=product),
            Rule.objects.get(product=product),
        ):
            with self.subTest(model=related_object._meta.label):  # pylint: disable=protected-access
                with self.assertRaises(RestrictedError):
                    related_object.delete()

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_product_delete_signal_failure_rolls_back_cascade(self, mock_issue_tracker) -> None:
        product = self._create_product_with_records("product")
        product_id = product.pk

        def fail_after_dependents(sender: type[Product], instance: Product, **_kwargs: object) -> None:
            del sender
            if instance.pk == product_id:
                raise RuntimeError("product cascade failed")

        dispatch_uid = "test_product_delete_signal_failure_rolls_back_cascade"
        post_delete.connect(fail_after_dependents, sender=Product, weak=False, dispatch_uid=dispatch_uid)
        try:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaisesRegex(RuntimeError, "product cascade failed"):
                    with transaction.atomic():
                        product.delete()
        finally:
            post_delete.disconnect(sender=Product, dispatch_uid=dispatch_uid)

        self.assertTrue(Product.objects.filter(pk=product_id).exists())
        self.assertTrue(Observation.objects.filter(product_id=product_id).exists())
        self.assertTrue(License_Component.objects.filter(product_id=product_id).exists())
        self.assertEqual([], callbacks)
        mock_issue_tracker.assert_not_called()

    @patch("application.core.signals.push_deleted_observation_to_issue_tracker")
    def test_group_delete_signal_failure_rolls_back_cascade(self, mock_issue_tracker) -> None:
        product_group = Product.objects.create(name="product_group", is_product_group=True)
        first_child = self._create_product_with_records("first_child", product_group)
        second_child = self._create_product_with_records("second_child", product_group)
        deleted_ids = [product_group.pk, first_child.pk, second_child.pk]

        def fail_during_product_cascade(sender: type[Product], instance: Product, **_kwargs: object) -> None:
            del sender
            if instance.pk == second_child.pk:
                raise RuntimeError("child cascade failed")

        dispatch_uid = "test_group_delete_signal_failure_rolls_back_cascade"
        post_delete.connect(fail_during_product_cascade, sender=Product, weak=False, dispatch_uid=dispatch_uid)
        try:
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                with self.assertRaisesRegex(RuntimeError, "child cascade failed"):
                    with transaction.atomic():
                        product_group.delete()
        finally:
            post_delete.disconnect(sender=Product, dispatch_uid=dispatch_uid)

        self.assertEqual(3, Product.objects.filter(pk__in=deleted_ids).count())
        self.assertTrue(Observation.objects.filter(product_id=first_child.pk).exists())
        self.assertTrue(License_Component.objects.filter(product_id=first_child.pk).exists())
        self.assertEqual([], callbacks)
        mock_issue_tracker.assert_not_called()

    def _create_product_with_records(self, name: str, product_group: Product | None = None) -> Product:
        product = Product.objects.create(name=name, product_group=product_group)
        branch = Branch.objects.create(name=f"{name}_branch", product=product)
        product.refresh_from_db()
        service = Service.objects.create(name=f"{name}_service", product=product)
        Product_Member.objects.create(product=product, user=self.owner, role=Roles.Owner)
        Api_Configuration.objects.create(
            name=f"{name}_api_configuration",
            product=product,
            parser=self.parser,
            automatic_import_branch=branch,
            automatic_import_service=service,
        )
        rule = Rule.objects.create(name=f"{name}_rule", product=product)
        OpenVEX.objects.create(
            user=self.external_user,
            product=product,
            document_id_prefix=f"{name}_prefix",
            document_base_id=f"{name}_base",
            version=1,
            id_namespace=f"https://example.com/{name}",
            author="SecObserve",
        )
        self._add_blocking_records(product, name, branch, service, rule)
        return product

    def _add_blocking_records(
        self,
        product: Product,
        name: str,
        branch: Branch | None = None,
        service: Service | None = None,
        rule: Rule | None = None,
    ) -> None:
        Observation.objects.create(
            title=f"{name}_observation",
            product=product,
            branch=branch,
            parser=self.parser,
            parser_status=Status.STATUS_OPEN,
            import_last_seen=timezone.now(),
            origin_service=service,
            product_rule=rule,
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
            origin_service=service,
        )
