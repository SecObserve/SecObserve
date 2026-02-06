# tests/test_licenselynx.py
import unittest
from unittest.mock import patch

from application.licenses.services.licenselynx import (
    apply_licenselynx,
    _get_mapped_licence_string,
    _get_mapped_licence
)
from application.licenses.models import License, License_Component
from licenselynx.licenselynx import LicenseObject
from application.licenses.services.spdx_license_cache import SPDXLicenseCache


class TestLicenseLynx(unittest.TestCase):

    @patch('application.licenses.services.licenselynx.LicenseLynx')
    def test_get_mapped_licence_string_success(self, mock_licenselynx):
        # Setup
        mock_license_object = LicenseObject(id="MIT", src="SPDX")
        mock_licenselynx.map.return_value = mock_license_object
        
        # Execute
        result = _get_mapped_licence_string("MIT License")
        
        # Verify
        self.assertEqual(result, "MIT")
        mock_licenselynx.map.assert_called_once_with("MIT License")

    @patch('application.licenses.services.licenselynx.LicenseLynx')
    def test_get_mapped_licence_string_none(self, mock_licenselynx):
        # Setup
        mock_licenselynx.map.return_value = None
        
        # Execute
        result = _get_mapped_licence_string("Non-existent License")
        
        # Verify
        self.assertIsNone(result)
        mock_licenselynx.map.assert_called_once_with("Non-existent License")

    @patch('application.licenses.services.licenselynx.SPDXLicenseCache')
    @patch('application.licenses.services.licenselynx.LicenseLynx')
    def test_get_mapped_licence_success(self, mock_licenselynx, mock_spdx_cache):
        # Setup
        mock_license_object = LicenseObject(id="MIT", src="SPDX")
        mock_licenselynx.map.return_value = mock_license_object
        
        mock_spdx_license = License(spdx_id="MIT")
        mock_spdx_cache.get.return_value = mock_spdx_license
        
        # Execute
        result = _get_mapped_licence("MIT License", mock_spdx_cache)
        
        # Verify
        self.assertEqual(result, mock_spdx_license)
        mock_licenselynx.map.assert_called_once_with("MIT License")
        mock_spdx_cache.get.assert_called_once_with("MIT")

    @patch('application.licenses.services.licenselynx.SPDXLicenseCache')
    @patch('application.licenses.services.licenselynx.LicenseLynx')
    def test_get_mapped_licence_none(self, mock_licenselynx, mock_spdx_cache):
        # Setup
        mock_licenselynx.map.return_value = None
        mock_spdx_cache.get.return_value = None
        
        # Execute
        result = _get_mapped_licence("Non-existent License", mock_spdx_cache)
        
        # Verify
        self.assertIsNone(result)
        mock_licenselynx.map.assert_called_once_with("Non-existent License")

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_manual_concluded_license_no_change(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = "MIT"
        component.manual_concluded_comment = "Some comment"
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        mock_get_licence_string.assert_not_called()
        mock_get_licence.assert_not_called()
        mock_set_effective.assert_not_called()

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_declared_non_spdx_license(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = "MIT License"
        component.imported_declared_multiple_licenses = None
        component.imported_concluded_non_spdx_license = None
        component.imported_concluded_multiple_licenses = None
        
        # Mock the return value for the _get_mapped_licence function
        mock_mapped_license = License(spdx_id="MIT")
        mock_get_licence.return_value = mock_mapped_license
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertEqual(component.manual_concluded_spdx_license, mock_mapped_license)
        self.assertEqual(component.manual_concluded_comment, "Set by LicenseLynx")
        self.assertEqual(component.manual_concluded_license_name, "MIT")
        mock_get_licence.assert_called_once_with("MIT License", None)
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_declared_non_spdx_license_not_found(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = "MIT License"
        component.imported_declared_multiple_licenses = None
        component.imported_concluded_non_spdx_license = None
        component.imported_concluded_multiple_licenses = None
        
        # Mock the return value for the _get_mapped_licence function
        mock_get_licence.return_value = None
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertIsNone(component.manual_concluded_spdx_license)
        self.assertIsNone(component.manual_concluded_comment)
        self.assertIsNone(component.manual_concluded_license_name)
        mock_get_licence.assert_called_once_with("MIT License", None)
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_declared_multiple_licenses(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = None
        component.imported_declared_multiple_licenses = "MIT, Apache-2.0"
        component.imported_concluded_non_spdx_license = None
        component.imported_concluded_multiple_licenses = None
        
        # Mock the return value for the _get_mapped_licence_string function
        mock_get_licence_string.return_value = "0BSD"
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertEqual(component.imported_declared_multiple_licenses, "0BSD, 0BSD")
        self.assertEqual(component.imported_declared_license_name, "0BSD, 0BSD")
        mock_get_licence_string.assert_called()
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_declared_multiple_licenses_not_found(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = None
        component.imported_declared_multiple_licenses = "MIT, Apache-2.0"
        component.imported_concluded_non_spdx_license = None
        component.imported_concluded_multiple_licenses = None
        
        # Mock the return value for the _get_mapped_licence_string function
        mock_get_licence_string.return_value = None
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertEqual(component.imported_declared_multiple_licenses, "MIT, Apache-2.0")
        self.assertEqual(component.imported_declared_license_name, "MIT, Apache-2.0")
        mock_get_licence_string.assert_called()
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_concluded_non_spdx_license(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = None
        component.imported_declared_multiple_licenses = None
        component.imported_concluded_non_spdx_license = "MIT License"
        component.imported_concluded_multiple_licenses = None
        
        # Mock the return value for the _get_mapped_licence function
        mock_mapped_license = License(spdx_id="MIT")
        mock_get_licence.return_value = mock_mapped_license
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertEqual(component.manual_concluded_spdx_license, mock_mapped_license)
        self.assertEqual(component.manual_concluded_comment, "Set by LicenseLynx")
        self.assertEqual(component.manual_concluded_license_name, "MIT")
        mock_get_licence.assert_called_once_with("MIT License", None)
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_concluded_non_spdx_license_not_found(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = None
        component.imported_declared_multiple_licenses = None
        component.imported_concluded_non_spdx_license = "MIT License"
        component.imported_concluded_multiple_licenses = None
        
        # Mock the return value for the _get_mapped_licence function
        mock_get_licence.return_value = None
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertIsNone(component.manual_concluded_spdx_license)
        self.assertIsNone(component.manual_concluded_comment)
        self.assertIsNone(component.manual_concluded_license_name)
        mock_get_licence.assert_called_once_with("MIT License", None)
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_concluded_multiple_licenses(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = None
        component.imported_declared_multiple_licenses = None
        component.imported_concluded_non_spdx_license = None
        component.imported_concluded_multiple_licenses = "MIT, Apache-2.0"
        
        # Mock the return value for the _get_mapped_licence_string function
        mock_get_licence_string.return_value = "0BSD"
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertEqual(component.imported_concluded_multiple_licenses, "0BSD, 0BSD")
        self.assertEqual(component.imported_concluded_license_name, "0BSD, 0BSD")
        mock_get_licence_string.assert_called()
        mock_set_effective.assert_called_once_with(component)

    @patch('application.licenses.services.licenselynx.set_effective_license')
    @patch('application.licenses.services.licenselynx._get_mapped_licence')
    @patch('application.licenses.services.licenselynx._get_mapped_licence_string')
    def test_apply_licenselynx_imported_concluded_multiple_licenses_not_found(
        self, mock_get_licence_string, mock_get_licence, mock_set_effective
    ):
        # Setup - using actual License_Component class
        component = License_Component()
        component.manual_concluded_license_name = None
        component.manual_concluded_comment = None
        component.imported_declared_non_spdx_license = None
        component.imported_declared_multiple_licenses = None
        component.imported_concluded_non_spdx_license = None
        component.imported_concluded_multiple_licenses = "MIT, Apache-2.0"
        
        # Mock the return value for the _get_mapped_licence_string function
        mock_get_licence_string.return_value = None
        
        # Execute
        apply_licenselynx(component, None)
        
        # Verify
        self.assertEqual(component.imported_concluded_multiple_licenses, "MIT, Apache-2.0")
        self.assertEqual(component.imported_concluded_license_name, "MIT, Apache-2.0")
        mock_get_licence_string.assert_called()
        mock_set_effective.assert_called_once_with(component)
