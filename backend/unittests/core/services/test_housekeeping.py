from datetime import timedelta
from unittest.mock import Mock, call, patch

from django.core.management import call_command
from django.utils import timezone

from application.commons.models import Settings
from application.core.models import Branch, Component, Product
from application.core.services.housekeeping import (
    delete_inactive_branches_for_product,
    delete_orphaned_components,
    housekeeping,
)
from application.licenses.models import License_Component
from unittests.base_test_case import BaseTestCase


class TestHousekeeping(BaseTestCase):
    def setUp(self) -> None:
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        branch = Branch.objects.get(name="db_branch_internal_dev")
        branch.last_import = timezone.now() - timedelta(days=10)
        branch.save()
        branch = Branch.objects.get(name="db_branch_internal_main")
        branch.last_import = timezone.now() - timedelta(days=10)
        branch.save()

        product = Product.objects.get(name="db_product_internal")
        product.product_group = None
        product.save()

        return super().setUp()

    @patch("application.core.services.housekeeping.delete_orphaned_components")
    @patch("application.core.services.housekeeping.delete_inactive_branches_for_product")
    def test_delete_inactive_branches(
        self, mock_delete_inactive_branches_for_product: Mock, mock_delete_orphaned_components: Mock
    ):
        mock_delete_inactive_branches_for_product.return_value = 2
        mock_delete_orphaned_components.return_value = 3

        message = housekeeping()

        self.assertEqual(message, "Deleted 4 inactive branches in 2 products.\nDeleted 3 orphaned components.")
        mock_delete_orphaned_components.assert_called_once()
        expected_calls = [
            call(Product.objects.get(name="db_product_internal")),
            call(Product.objects.get(name="db_product_external")),
        ]
        mock_delete_inactive_branches_for_product.assert_has_calls(expected_calls)
        self.assertEqual(mock_delete_inactive_branches_for_product.call_count, 2)

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_delete(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_keep_inactive_days = 9
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_dev")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

        try:
            Branch.objects.get(name="db_branch_internal_main")
            self.fail("Branch should have been deleted")
        except Branch.DoesNotExist:
            pass

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_not_active(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_keep_inactive_days = 9
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_too_early(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_keep_inactive_days = 11
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_exempt(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_keep_inactive_days = 9
        settings.branch_housekeeping_exempt_branches = "db_branch_internal_m.*"
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_not_active(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_keep_inactive_days = 9
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        product.repository_branch_housekeeping_active = False
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_specific_delete(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product_group = Product.objects.get(name="db_product_group")
        product_group.repository_branch_housekeeping_active = None
        product_group.repository_branch_housekeeping_keep_inactive_days = 11
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        product.product_group = product_group
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 9
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            self.fail("Branch should have been deleted")
        except Branch.DoesNotExist:
            pass

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_specific_too_early(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 11
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_specific_exempt(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 9
        product.repository_branch_housekeeping_exempt_branches = "db_branch_internal_m.*"
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_specific_protected(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product = Product.objects.get(name="db_product_internal")
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 9
        product.save()
        branch = Branch.objects.get(name="db_branch_internal_main")
        branch.housekeeping_protect = True
        branch.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_group_not_active(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product_group = Product.objects.get(name="db_product_group")
        product_group.repository_branch_housekeeping_active = False
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        product.product_group = product_group
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 9
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_group_too_early(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product_group = Product.objects.get(name="db_product_group")
        product_group.repository_branch_housekeeping_active = True
        product_group.repository_branch_housekeeping_keep_inactive_days = 11
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        product.product_group = product_group
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 11
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_group_exempt(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product_group = Product.objects.get(name="db_product_group")
        product_group.repository_branch_housekeeping_active = True
        product_group.repository_branch_housekeeping_keep_inactive_days = 9
        product_group.repository_branch_housekeeping_exempt_branches = "db_branch_internal_m.*"
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        product.product_group = product_group
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 9
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            pass
        except Branch.DoesNotExist:
            self.fail("Branch should not have been deleted")

    @patch("application.commons.models.Settings.load")
    def test_delete_inactive_branches_for_product_product_group_delete(self, mock_settings_load):
        settings = Settings()
        settings.branch_housekeeping_active = False
        mock_settings_load.return_value = settings

        product_group = Product.objects.get(name="db_product_group")
        product_group.repository_branch_housekeeping_active = True
        product_group.repository_branch_housekeeping_keep_inactive_days = 9
        product_group.save()
        product = Product.objects.get(name="db_product_internal")
        product.product_group = product_group
        product.repository_branch_housekeeping_active = True
        product.repository_branch_housekeeping_keep_inactive_days = 11
        product.save()

        delete_inactive_branches_for_product(product)

        try:
            Branch.objects.get(name="db_branch_internal_main")
            self.fail("Branch should have been deleted")
        except Branch.DoesNotExist:
            pass

    def test_delete_orphaned_components(self):
        num_deleted_components = delete_orphaned_components()

        self.assertEqual(num_deleted_components, 1)
        self.assertFalse(Component.objects.filter(name_version="unused_component:3.0.0").exists())
        self.assertEqual(Component.objects.count(), 3)

    def test_delete_orphaned_components_with_license_component(self):
        License_Component.objects.create(
            identity_hash="db_identity_hash_unused_component",
            product=Product.objects.get(name="db_product_internal"),
            component=Component.objects.get(name_version="unused_component:3.0.0"),
            component_name="unused_component",
            component_version="3.0.0",
            component_name_version="unused_component:3.0.0",
            numerical_evaluation_result=5,
        )

        num_deleted_components = delete_orphaned_components()

        self.assertEqual(num_deleted_components, 0)
        self.assertEqual(Component.objects.count(), 4)
