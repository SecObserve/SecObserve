from unittest.mock import patch

from django.db.models.deletion import RestrictedError

from application.core.models import Branch, Product, Service
from application.licenses.models import License_Component
from application.scancodeio.models import ScanCodeIO_Project
from unittests.base_test_case import BaseTestCase


class TestScanCodeIOSignals(BaseTestCase):
    def setUp(self):
        super().setUp()
        patcher = patch("application.scancodeio.signals.delete_orphaned_scancodeio_project")
        self.addCleanup(patcher.stop)
        self.mock_delete_orphaned = patcher.start()

    def test_delete_product_with_scancodeio_project(self):
        product = Product.objects.create(name="product")
        ScanCodeIO_Project.objects.create(
            product=product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        product.delete()

        self.mock_delete_orphaned.assert_called_once_with("6461408c-726c-4b70-aa7a-c9cc9d1c9685")
        self.assertFalse(ScanCodeIO_Project.objects.exists())

    def test_delete_product_without_scancodeio_project(self):
        product = Product.objects.create(name="product")

        product.delete()

        self.mock_delete_orphaned.assert_not_called()

    def test_delete_product_group_with_scancodeio_project_of_child(self):
        product_group = Product.objects.create(name="product_group", is_product_group=True)
        product = Product.objects.create(name="product", product_group=product_group)
        ScanCodeIO_Project.objects.create(
            product=product, project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685", project_name="project_name"
        )

        product_group.delete()

        self.mock_delete_orphaned.assert_called_once_with("6461408c-726c-4b70-aa7a-c9cc9d1c9685")
        self.assertFalse(ScanCodeIO_Project.objects.exists())

    def test_delete_branch_with_scancodeio_project(self):
        product = Product.objects.create(name="product")
        branch = Branch.objects.create(product=product, name="branch")
        ScanCodeIO_Project.objects.create(
            product=product,
            branch=branch,
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685",
            project_name="project_branch",
            webhook_token_hash="hash_branch",
        )
        ScanCodeIO_Project.objects.create(
            product=product,
            project_uuid="7cbd4e4a-2a1c-4a50-9a4e-2d8f8a8c1f3b",
            project_name="project_product",
            webhook_token_hash="hash_product",
        )

        branch.delete()

        self.mock_delete_orphaned.assert_called_once_with("6461408c-726c-4b70-aa7a-c9cc9d1c9685")
        self.assertEqual(ScanCodeIO_Project.objects.get().project_name, "project_product")

    def test_delete_service_with_scancodeio_project(self):
        product = Product.objects.create(name="product")
        service = Service.objects.create(product=product, name="service")
        ScanCodeIO_Project.objects.create(
            product=product,
            service=service,
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685",
            project_name="project_service",
        )

        service.delete()

        self.mock_delete_orphaned.assert_called_once_with("6461408c-726c-4b70-aa7a-c9cc9d1c9685")
        self.assertFalse(ScanCodeIO_Project.objects.exists())

    def test_delete_service_restricted_by_license_component(self):
        product = Product.objects.create(name="product")
        service = Service.objects.create(product=product, name="service")
        ScanCodeIO_Project.objects.create(
            product=product,
            service=service,
            project_uuid="6461408c-726c-4b70-aa7a-c9cc9d1c9685",
            project_name="project_service",
        )
        License_Component.objects.create(
            product=product, origin_service=service, component_name="component", numerical_evaluation_result=1
        )

        with self.assertRaises(RestrictedError):
            service.delete()

        self.mock_delete_orphaned.assert_not_called()
        self.assertTrue(ScanCodeIO_Project.objects.exists())
