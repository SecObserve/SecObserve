from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from application.core.models import Product
from application.licenses.models import License, License_Component
from application.licenses.services.license_component import (
    save_concluded_license,
    set_effective_license,
)
from application.licenses.types import NO_LICENSE_INFORMATION
from unittests.base_test_case import BaseTestCase


class TestLicenseComponent(BaseTestCase):
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

    def test_set_effective_license_with_concluded_license(self):
        """
        Test that when concluded_license_name is not NO_LICENSE_INFORMATION,
        the effective license is set from the concluded license.
        """
        # Arrange
        license_obj = License.objects.first()
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            # Set concluded license fields
            manual_concluded_license_name="MIT",
            manual_concluded_spdx_license=license_obj,
            manual_concluded_license_expression="MIT expression",
            manual_concluded_non_spdx_license="MIT non-spdx",
            # Set imported concluded license fields (should be ignored)
            imported_concluded_license_name="Apache-2.0",
            imported_concluded_spdx_license=None,
            imported_concluded_license_expression="Apache-2.0 expression",
            imported_concluded_non_spdx_license="Apache-2.0 non-spdx",
            imported_concluded_multiple_licenses="Apache-2.0, GPL-2.0",
            # Set imported declared license fields (should be ignored)
            imported_declared_license_name="GPL-3.0",
            imported_declared_spdx_license=None,
            imported_declared_license_expression="GPL-3.0 expression",
            imported_declared_non_spdx_license="GPL-3.0 non-spdx",
            imported_declared_multiple_licenses="GPL-3.0, BSD-3-Clause",
        )

        # Act
        set_effective_license(component)

        # Assert
        self.assertEqual(component.effective_license_name, "MIT")
        self.assertEqual(component.effective_spdx_license, license_obj)
        self.assertEqual(component.effective_license_expression, "MIT expression")
        self.assertEqual(component.effective_non_spdx_license, "MIT non-spdx")
        self.assertEqual(component.effective_multiple_licenses, "")

    def test_set_effective_license_with_imported_concluded_license(self):
        """
        Test that when concluded_license_name is NO_LICENSE_INFORMATION but
        imported_concluded_license_name is not, the effective license is set from
        the imported concluded license.
        """
        # Arrange
        license_obj = License.objects.first()
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            # Set concluded license fields to NO_LICENSE_INFORMATION
            manual_concluded_license_name=NO_LICENSE_INFORMATION,
            manual_concluded_spdx_license=None,
            manual_concluded_license_expression="",
            manual_concluded_non_spdx_license="",
            # Set imported concluded license fields
            imported_concluded_license_name="Apache-2.0",
            imported_concluded_spdx_license=license_obj,
            imported_concluded_license_expression="Apache-2.0 expression",
            imported_concluded_non_spdx_license="Apache-2.0 non-spdx",
            imported_concluded_multiple_licenses="Apache-2.0, GPL-2.0",
            # Set imported declared license fields (should be ignored)
            imported_declared_license_name="GPL-3.0",
            imported_declared_spdx_license=None,
            imported_declared_license_expression="GPL-3.0 expression",
            imported_declared_non_spdx_license="GPL-3.0 non-spdx",
            imported_declared_multiple_licenses="GPL-3.0, BSD-3-Clause",
        )

        # Act
        set_effective_license(component)

        # Assert
        self.assertEqual(component.effective_license_name, "Apache-2.0")
        self.assertEqual(component.effective_spdx_license, license_obj)
        self.assertEqual(component.effective_license_expression, "Apache-2.0 expression")
        self.assertEqual(component.effective_non_spdx_license, "Apache-2.0 non-spdx")
        self.assertEqual(component.effective_multiple_licenses, "Apache-2.0, GPL-2.0")

    def test_set_effective_license_with_imported_declared_license(self):
        """
        Test that when both concluded_license_name and imported_concluded_license_name
        are NO_LICENSE_INFORMATION but imported_declared_license_name is not,
        the effective license is set from the imported declared license.
        """
        # Arrange
        license_obj = License.objects.first()
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            # Set concluded license fields to NO_LICENSE_INFORMATION
            manual_concluded_license_name=NO_LICENSE_INFORMATION,
            manual_concluded_spdx_license=None,
            manual_concluded_license_expression="",
            manual_concluded_non_spdx_license="",
            # Set imported concluded license fields to NO_LICENSE_INFORMATION
            imported_concluded_license_name=NO_LICENSE_INFORMATION,
            imported_concluded_spdx_license=None,
            imported_concluded_license_expression="",
            imported_concluded_non_spdx_license="",
            imported_concluded_multiple_licenses="",
            # Set imported declared license fields
            imported_declared_license_name="GPL-3.0",
            imported_declared_spdx_license=license_obj,
            imported_declared_license_expression="GPL-3.0 expression",
            imported_declared_non_spdx_license="GPL-3.0 non-spdx",
            imported_declared_multiple_licenses="GPL-3.0, BSD-3-Clause",
        )

        # Act
        set_effective_license(component)

        # Assert
        self.assertEqual(component.effective_license_name, "GPL-3.0")
        self.assertEqual(component.effective_spdx_license, license_obj)
        self.assertEqual(component.effective_license_expression, "GPL-3.0 expression")
        self.assertEqual(component.effective_non_spdx_license, "GPL-3.0 non-spdx")
        self.assertEqual(component.effective_multiple_licenses, "GPL-3.0, BSD-3-Clause")

    def test_set_effective_license_with_no_license_information(self):
        """
        Test that when all license names are NO_LICENSE_INFORMATION,
        the effective license remains NO_LICENSE_INFORMATION.
        """
        # Arrange
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            # Set all license fields to NO_LICENSE_INFORMATION
            manual_concluded_license_name=NO_LICENSE_INFORMATION,
            manual_concluded_spdx_license=None,
            manual_concluded_license_expression="",
            manual_concluded_non_spdx_license="",
            imported_concluded_license_name=NO_LICENSE_INFORMATION,
            imported_concluded_spdx_license=None,
            imported_concluded_license_expression="",
            imported_concluded_non_spdx_license="",
            imported_concluded_multiple_licenses="",
            imported_declared_license_name=NO_LICENSE_INFORMATION,
            imported_declared_spdx_license=None,
            imported_declared_license_expression="",
            imported_declared_non_spdx_license="",
            imported_declared_multiple_licenses="",
        )

        # Act
        set_effective_license(component)

        # Assert
        self.assertEqual(component.effective_license_name, NO_LICENSE_INFORMATION)
        self.assertIsNone(component.effective_spdx_license)
        self.assertEqual(component.effective_license_expression, "")
        self.assertEqual(component.effective_non_spdx_license, "")
        self.assertEqual(component.effective_multiple_licenses, "")

    @patch("application.licenses.services.license_component.update_concluded_license")
    @patch("application.licenses.services.license_component.get_license_policy")
    def test_save_concluded_license_with_spdx_license(self, mock_get_license_policy, mock_update_concluded_license):
        """
        Test save_concluded_license when a concluded_spdx_license is provided.
        """
        # Arrange
        mock_get_license_policy.return_value = None  # No license policy
        license_obj = License.objects.first()
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            manual_concluded_spdx_license=license_obj,
        )

        # Act
        with patch.object(component, "save") as mock_save:
            save_concluded_license(component)

        # Assert
        self.assertEqual(component.manual_concluded_license_name, license_obj.spdx_id)
        mock_update_concluded_license.assert_called_once_with(component)
        mock_get_license_policy.assert_called_once_with(component.product)
        mock_save.assert_called_once()

    @patch("application.licenses.services.license_component.update_concluded_license")
    @patch("application.licenses.services.license_component.get_license_policy")
    @patch("application.licenses.services.license_component.get_spdx_licensing")
    def test_save_concluded_license_with_valid_license_expression(
        self, mock_get_spdx_licensing, mock_get_license_policy, mock_update_concluded_license
    ):
        """
        Test save_concluded_license when a valid concluded_license_expression is provided.
        """
        # Arrange
        mock_get_license_policy.return_value = None  # No license policy

        # Mock the licensing validation
        mock_licensing = MagicMock()
        mock_expression_info = MagicMock()
        mock_expression_info.errors = []
        mock_expression_info.normalized_expression = "MIT OR Apache-2.0"
        mock_licensing.validate.return_value = mock_expression_info
        mock_get_spdx_licensing.return_value = mock_licensing

        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            manual_concluded_license_expression="MIT OR Apache-2.0",
        )

        # Act
        with patch.object(component, "save") as mock_save:
            save_concluded_license(component)

        # Assert
        self.assertEqual(component.manual_concluded_license_name, "MIT OR Apache-2.0")
        mock_licensing.validate.assert_called_once_with("MIT OR Apache-2.0", strict=True)
        mock_update_concluded_license.assert_called_once_with(component)
        mock_get_license_policy.assert_called_once_with(component.product)
        mock_save.assert_called_once()

    @patch("application.licenses.services.license_component.update_concluded_license")
    @patch("application.licenses.services.license_component.get_license_policy")
    @patch("application.licenses.services.license_component.get_spdx_licensing")
    def test_save_concluded_license_with_invalid_license_expression(
        self, mock_get_spdx_licensing, mock_get_license_policy, mock_update_concluded_license
    ):
        """
        Test save_concluded_license when an invalid concluded_license_expression is provided.
        """
        # Arrange
        # Mock the licensing validation to return errors
        mock_licensing = MagicMock()
        mock_expression_info = MagicMock()
        mock_expression_info.errors = ["Invalid license expression"]
        mock_licensing.validate.return_value = mock_expression_info
        mock_get_spdx_licensing.return_value = mock_licensing

        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            manual_concluded_license_expression="INVALID-LICENSE",
        )

        # Act & Assert
        with self.assertRaises(ValidationError):
            save_concluded_license(component)

        # Verify the validation was called
        mock_licensing.validate.assert_called_once_with("INVALID-LICENSE", strict=True)
        # These should not be called due to the validation error
        mock_update_concluded_license.assert_not_called()
        mock_get_license_policy.assert_not_called()

    @patch("application.licenses.services.license_component.update_concluded_license")
    @patch("application.licenses.services.license_component.get_license_policy")
    def test_save_concluded_license_with_non_spdx_license(self, mock_get_license_policy, mock_update_concluded_license):
        """
        Test save_concluded_license when a concluded_non_spdx_license is provided.
        """
        # Arrange
        mock_get_license_policy.return_value = None  # No license policy
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            manual_concluded_non_spdx_license="Custom License",
        )

        # Act
        with patch.object(component, "save") as mock_save:
            save_concluded_license(component)

        # Assert
        self.assertEqual(component.manual_concluded_license_name, "Custom License")
        mock_update_concluded_license.assert_called_once_with(component)
        mock_get_license_policy.assert_called_once_with(component.product)
        mock_save.assert_called_once()

    @patch("application.licenses.services.license_component.update_concluded_license")
    @patch("application.licenses.services.license_component.get_license_policy")
    def test_save_concluded_license_with_no_license_info(self, mock_get_license_policy, mock_update_concluded_license):
        """
        Test save_concluded_license when no license information is provided.
        """
        # Arrange
        mock_get_license_policy.return_value = None  # No license policy
        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
        )

        # Act
        with patch.object(component, "save") as mock_save:
            save_concluded_license(component)

        # Assert
        self.assertEqual(component.manual_concluded_license_name, NO_LICENSE_INFORMATION)
        mock_update_concluded_license.assert_called_once_with(component)
        mock_get_license_policy.assert_called_once_with(component.product)
        mock_save.assert_called_once()

    @patch("application.licenses.services.license_component.update_concluded_license")
    @patch("application.licenses.services.license_component.get_license_policy")
    @patch("application.licenses.services.license_component.get_license_evaluation_results_for_product")
    @patch("application.licenses.services.license_component.apply_license_policy_to_component")
    @patch("application.licenses.services.license_component.get_comma_separated_as_list")
    def test_save_concluded_license_with_license_policy(
        self,
        mock_get_comma_separated,
        mock_apply_policy,
        mock_get_results,
        mock_get_license_policy,
        mock_update_concluded_license,
    ):
        """
        Test save_concluded_license when a license policy exists for the product.
        """
        # Arrange
        mock_license_policy = MagicMock()
        mock_license_policy.ignore_component_types = "type1,type2"
        mock_get_license_policy.return_value = mock_license_policy

        mock_evaluation_results = {"result1": "value1"}
        mock_get_results.return_value = mock_evaluation_results

        mock_get_comma_separated.return_value = ["type1", "type2"]

        component = License_Component(
            product=Product.objects.get(pk=1),
            component_name="test_component",
            component_version="1.0.0",
            component_name_version="test_component:1.0.0",
            manual_concluded_non_spdx_license="Custom License",
        )

        # Act
        with patch.object(component, "save") as mock_save:
            save_concluded_license(component)

        # Assert
        self.assertEqual(component.manual_concluded_license_name, "Custom License")
        mock_update_concluded_license.assert_called_once_with(component)
        mock_get_license_policy.assert_called_once_with(component.product)
        mock_get_results.assert_called_once_with(component.product)
        mock_get_comma_separated.assert_called_once_with(mock_license_policy.ignore_component_types)
        mock_apply_policy.assert_called_once_with(component, mock_evaluation_results, ["type1", "type2"])
        mock_save.assert_called_once()
