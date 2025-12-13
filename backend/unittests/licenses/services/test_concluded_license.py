from unittest.mock import patch

from django.core.management import call_command

from application.access_control.models import User
from application.core.models import Product
from application.licenses.models import Concluded_License, License, License_Component
from application.licenses.services.concluded_license import (
    ConcludeLicenseApplicator,
    update_concluded_license,
)
from application.licenses.types import NO_LICENSE_INFORMATION
from unittests.base_test_case import BaseTestCase


class TestConcludedLicense(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        call_command(
            "loaddata",
            [
                "unittests/fixtures/initial_license_data.json",
                "unittests/fixtures/unittests_fixtures.json",
                "unittests/fixtures/unittests_license_fixtures.json",
            ],
        )

        super().setUpClass()

    def setUp(self):
        super().setUp()
        self.license_obj = License.objects.first()

        self.product_indirect = Product.objects.get(pk=2)
        self.product_indirect.product_group = Product.objects.get(name="db_product_group")
        self.product_indirect.save()

        self.product_direct = Product.objects.get(pk=1)
        self.product_direct.product_group = Product.objects.get(name="db_product_group")
        self.product_direct.save()

        self.component = License_Component(
            product=self.product_direct,
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            component_purl_type="npm",
            effective_spdx_license=None,
            effective_license_expression="",
            effective_non_spdx_license="",
        )
        self.db_user = User.objects.get(username="db_admin")

    def test_apply_concluded_license_no_product_group_exact_match_spdx_license(self):
        """
        Test apply_concluded_license when there's an exact match for the component
        with a concluded_spdx_license.
        """
        # Arrange
        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_spdx_license=self.license_obj,
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertEqual(self.component.manual_concluded_spdx_license, self.license_obj)
        self.assertEqual(self.component.manual_concluded_license_name, self.license_obj.spdx_id)
        self.assertEqual(self.component.manual_concluded_comment, f"Set manually by {str(concluded_license.user)}")
        self.assertEqual(self.component.manual_concluded_license_expression, "")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

        # Clean up
        concluded_license.delete()

    def test_apply_concluded_license_with_product_group_exact_match_spdx_license(self):
        """
        Test apply_concluded_license when there's an exact match for the component
        with a concluded_spdx_license for another product in the same product_group.
        """
        # Arrange
        concluded_license = Concluded_License.objects.create(
            product=self.product_indirect,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_spdx_license=self.license_obj,
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertEqual(self.component.manual_concluded_spdx_license, self.license_obj)
        self.assertEqual(self.component.manual_concluded_license_name, self.license_obj.spdx_id)
        self.assertEqual(
            self.component.manual_concluded_comment,
            f"Copied from product {self.product_indirect.name}, set by {str(concluded_license.user)}",
        )
        self.assertEqual(self.component.manual_concluded_license_expression, "")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

        # Clean up
        concluded_license.delete()

    def test_apply_concluded_license_exact_match_license_expression(self):
        """
        Test apply_concluded_license when there's an exact match for the component
        with a concluded_license_expression.
        """
        # Arrange
        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_license_expression="MIT OR Apache-2.0",
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertIsNone(self.component.manual_concluded_spdx_license)
        self.assertEqual(self.component.manual_concluded_license_name, "MIT OR Apache-2.0")
        self.assertEqual(self.component.manual_concluded_license_expression, "MIT OR Apache-2.0")
        self.assertEqual(self.component.manual_concluded_comment, f"Set manually by {str(concluded_license.user)}")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

        # Clean up
        concluded_license.delete()

    def test_apply_concluded_license_exact_match_non_spdx_license(self):
        """
        Test apply_concluded_license when there's an exact match for the component
        with a concluded_non_spdx_license.
        """
        # Arrange
        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_non_spdx_license="Custom License",
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertIsNone(self.component.manual_concluded_spdx_license)
        self.assertEqual(self.component.manual_concluded_license_name, "Custom License")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "Custom License")
        self.assertEqual(self.component.manual_concluded_comment, f"Set manually by {str(concluded_license.user)}")
        self.assertEqual(self.component.manual_concluded_license_expression, "")

        # Clean up
        concluded_license.delete()

    def test_apply_concluded_license_name_no_product_group_match_different_version(self):
        """
        Test apply_concluded_license when there's a match by name but not version.
        """
        # Arrange
        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="2.0.0",  # Different version
            manual_concluded_spdx_license=self.license_obj,
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertEqual(self.component.manual_concluded_spdx_license, self.license_obj)
        self.assertEqual(self.component.manual_concluded_license_name, self.license_obj.spdx_id)
        self.assertEqual(
            self.component.manual_concluded_comment,
            f"Copied from version {concluded_license.component_version}, set by {str(concluded_license.user)}",
        )
        self.assertEqual(self.component.manual_concluded_license_expression, "")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

        # Clean up
        concluded_license.delete()

    def test_apply_concluded_license_name_with_product_group_match_different_version(self):
        """
        Test apply_concluded_license when there's a match by name but not version.
        """
        # Arrange
        concluded_license = Concluded_License.objects.create(
            product=self.product_indirect,
            component_purl_type="npm",
            component_name="test_component",
            component_version="2.0.0",  # Different version
            manual_concluded_spdx_license=self.license_obj,
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertEqual(self.component.manual_concluded_spdx_license, self.license_obj)
        self.assertEqual(self.component.manual_concluded_license_name, self.license_obj.spdx_id)
        self.assertEqual(
            self.component.manual_concluded_comment,
            f"Copied from product {self.product_indirect} and version {concluded_license.component_version}, set by {str(concluded_license.user)}",
        )
        self.assertEqual(self.component.manual_concluded_license_expression, "")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

        # Clean up
        concluded_license.delete()

    def test_apply_concluded_license_group_no_match(self):
        """
        Test apply_concluded_license when there's no match at all.
        """
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert
        self.assertIsNone(self.component.manual_concluded_spdx_license)
        self.assertEqual(self.component.manual_concluded_license_name, NO_LICENSE_INFORMATION)
        self.assertEqual(self.component.manual_concluded_comment, "")
        self.assertEqual(self.component.manual_concluded_license_expression, "")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

    def test_apply_concluded_license_no_change_needed(self):
        """
        Test apply_concluded_license when the effective license already matches the concluded license.
        """
        # Arrange
        self.component.effective_spdx_license = self.license_obj

        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_spdx_license=self.license_obj,
            user=self.db_user,
        )
        concluded_license_applicator = ConcludeLicenseApplicator(self.product_direct)

        # Act
        concluded_license_applicator.apply_concluded_license(self.component)

        # Assert - No changes should be made
        self.assertIsNone(self.component.manual_concluded_spdx_license)
        self.assertEqual(self.component.manual_concluded_license_name, NO_LICENSE_INFORMATION)
        self.assertEqual(self.component.manual_concluded_comment, "")
        self.assertEqual(self.component.manual_concluded_license_expression, "")
        self.assertEqual(self.component.manual_concluded_non_spdx_license, "")

        # Clean up
        concluded_license.delete()

    @patch("application.licenses.services.concluded_license.get_current_user")
    def test_update_concluded_license_delete_existing(self, mock_get_current_user):
        """
        Test update_concluded_license when concluded_license_name is NO_LICENSE_INFORMATION
        and a concluded license exists.
        """
        # Arrange
        mock_get_current_user.return_value = self.db_user

        self.component.manual_concluded_license_name = NO_LICENSE_INFORMATION

        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_spdx_license=self.license_obj,
            user=self.db_user,
        )

        # Act
        update_concluded_license(self.component)

        # Assert
        with self.assertRaises(Concluded_License.DoesNotExist):
            Concluded_License.objects.get(
                product=self.product_direct,
                component_purl_type="npm",
                component_name="test_component",
                component_version="1.0.0",
            )

    @patch("application.licenses.services.concluded_license.get_current_user")
    def test_update_concluded_license_no_existing_to_delete(self, mock_get_current_user):
        """
        Test update_concluded_license when concluded_license_name is NO_LICENSE_INFORMATION
        and no concluded license exists.
        """
        # Arrange
        mock_get_current_user.return_value = self.db_user

        self.component.manual_concluded_license_name = NO_LICENSE_INFORMATION

        # Act - This should not raise an exception
        update_concluded_license(self.component)

        # Assert
        self.assertEqual(
            Concluded_License.objects.filter(
                product=self.product_direct,
                component_purl_type="npm",
                component_name="test_component",
                component_version="1.0.0",
            ).count(),
            0,
        )

    @patch("application.licenses.services.concluded_license.get_current_user")
    def test_update_concluded_license_create_new(self, mock_get_current_user):
        """
        Test update_concluded_license when concluded_license_name is not NO_LICENSE_INFORMATION
        and no concluded license exists.
        """
        # Arrange
        mock_get_current_user.return_value = self.db_user

        self.component.manual_concluded_license_name = "MIT"
        self.component.manual_concluded_spdx_license = self.license_obj
        self.component.manual_concluded_license_expression = ""
        self.component.manual_concluded_non_spdx_license = ""

        # Act
        update_concluded_license(self.component)

        # Assert
        concluded_license = Concluded_License.objects.get(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
        )

        self.assertEqual(concluded_license.manual_concluded_spdx_license, self.license_obj)
        self.assertEqual(concluded_license.manual_concluded_license_expression, "")
        self.assertEqual(concluded_license.manual_concluded_non_spdx_license, "")
        self.assertEqual(concluded_license.user, self.db_user)
        self.assertEqual(self.component.manual_concluded_comment, f"Set manually by {str(self.db_user)}")

        # Clean up
        concluded_license.delete()

    @patch("application.licenses.services.concluded_license.get_current_user")
    def test_update_concluded_license_update_existing(self, mock_get_current_user):
        """
        Test update_concluded_license when concluded_license_name is not NO_LICENSE_INFORMATION
        and a concluded license exists.
        """
        # Arrange
        mock_get_current_user.return_value = self.db_user

        self.component.manual_concluded_license_name = "MIT"
        self.component.manual_concluded_spdx_license = self.license_obj
        self.component.manual_concluded_license_expression = ""
        self.component.manual_concluded_non_spdx_license = ""

        # Create an existing concluded license with different values
        concluded_license = Concluded_License.objects.create(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
            manual_concluded_license_expression="Apache-2.0",  # Different from component
            user=self.user_admin,  # Different user
        )

        # Act
        update_concluded_license(self.component)

        # Assert
        updated_license = Concluded_License.objects.get(
            product=self.product_direct,
            component_purl_type="npm",
            component_name="test_component",
            component_version="1.0.0",
        )

        self.assertEqual(updated_license.manual_concluded_spdx_license, self.license_obj)
        self.assertEqual(updated_license.manual_concluded_license_expression, "")
        self.assertEqual(updated_license.manual_concluded_non_spdx_license, "")
        self.assertEqual(updated_license.user, self.db_user)  # Should be updated to current user
        self.assertEqual(self.component.manual_concluded_comment, f"Set manually by {str(self.db_user)}")

        # Clean up
        updated_license.delete()
