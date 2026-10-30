from unittest.mock import patch

from application.core.models import Product
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
