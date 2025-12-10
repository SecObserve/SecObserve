import unittest
from unittest.mock import patch, MagicMock

from application.licenses.services.spdx_license_cache import SPDXLicenseCache
from application.licenses.models import License


class TestSPDXLicenseCache(unittest.TestCase):
    
    def setUp(self):
        self.cache = SPDXLicenseCache()
    
    def test_get_invalid_spdx_id_returns_none(self):
        """Test that invalid SPDX IDs return None"""
        # Test with invalid characters
        invalid_ids = ["", "invalid/spdx/id", "invalid id", "invalid@id"]
        
        for spdx_id in invalid_ids:
            with self.subTest(spdx_id=spdx_id):
                result = self.cache.get(spdx_id)
                self.assertIsNone(result)
    
    def test_get_valid_spdx_id_cache_hit_returns_license(self):
        """Test that valid SPDX IDs in cache return the cached license"""
        # Set up a mock license
        mock_license = MagicMock(spec=License)
        mock_license.spdx_id = "MIT"
        
        # Add to cache
        self.cache.cache["MIT"] = mock_license
        
        # Test cache hit
        result = self.cache.get("MIT")
        self.assertEqual(result, mock_license)
    
    def test_get_valid_spdx_id_cache_hit_returns_none_for_no_entry(self):
        """Test that valid SPDX IDs with NO_ENTRY in cache return None"""
        # Add NO_ENTRY to cache
        self.cache.cache["MIT"] = SPDXLicenseCache.NO_ENTRY
        
        # Test cache hit with NO_ENTRY
        result = self.cache.get("MIT")
        self.assertIsNone(result)
    
    @patch("application.licenses.services.spdx_license_cache.get_license_by_spdx_id")
    def test_get_valid_spdx_id_cache_miss_license_found(self, mock_get_license):
        """Test that valid SPDX IDs not in cache but found in database return the license"""
        # Set up mock license
        mock_license = MagicMock(spec=License)
        mock_license.spdx_id = "MIT"
        mock_get_license.return_value = mock_license
        
        # Test cache miss with license found
        result = self.cache.get("MIT")
        self.assertEqual(result, mock_license)
        # Verify license was added to cache
        self.assertEqual(self.cache.cache["MIT"], mock_license)
    
    @patch("application.licenses.services.spdx_license_cache.get_license_by_spdx_id")
    def test_get_valid_spdx_id_cache_miss_license_not_found(self, mock_get_license):
        """Test that valid SPDX IDs not in cache and not found in database return None"""
        # Set up mock to return None
        mock_get_license.return_value = None
        
        # Test cache miss with license not found
        result = self.cache.get("MIT")
        self.assertIsNone(result)
        # Verify NO_ENTRY was added to cache
        self.assertEqual(self.cache.cache["MIT"], SPDXLicenseCache.NO_ENTRY)
    
    def test_get_valid_spdx_id_cache_hit_with_string_returns_none(self):
        """Test that valid SPDX IDs with string value in cache return None"""
        # Add a string value (not License) to cache
        self.cache.cache["MIT"] = "some_string_value"
        
        # Test cache hit with string value
        result = self.cache.get("MIT")
        self.assertIsNone(result)
    
    def test_get_valid_spdx_id_cache_hit_with_license_returns_license(self):
        """Test that valid SPDX IDs with License value in cache return the license"""
        # Set up a mock license
        mock_license = MagicMock(spec=License)
        mock_license.spdx_id = "MIT"
        
        # Add to cache
        self.cache.cache["MIT"] = mock_license
        
        # Test cache hit with License value
        result = self.cache.get("MIT")
        self.assertEqual(result, mock_license)
    
    def test_get_valid_spdx_id_various_formats(self):
        """Test that various valid SPDX ID formats work correctly"""
        valid_ids = ["MIT", "Apache-2.0", "BSD-2-Clause", "GPL-3.0", "ISC", "LGPL-3.0"]
        
        # Mock get_license_by_spdx_id to return None for all
        with patch("application.licenses.services.spdx_license_cache.get_license_by_spdx_id") as mock_get_license:
            mock_get_license.return_value = None
            
            for spdx_id in valid_ids:
                with self.subTest(spdx_id=spdx_id):
                    result = self.cache.get(spdx_id)
                    self.assertIsNone(result)
                    # Verify NO_ENTRY was added to cache
                    self.assertEqual(self.cache.cache[spdx_id], SPDXLicenseCache.NO_ENTRY)
    
    def test_cache_is_empty_initially(self):
        """Test that cache is empty initially"""
        self.assertEqual(len(self.cache.cache), 0)
    
    def test_cache_stores_no_entry_correctly(self):
        """Test that NO_ENTRY is stored correctly in cache"""
        # Add NO_ENTRY to cache directly
        self.cache.cache["TEST"] = SPDXLicenseCache.NO_ENTRY
        
        # Verify it's stored correctly
        self.assertEqual(self.cache.cache["TEST"], SPDXLicenseCache.NO_ENTRY)