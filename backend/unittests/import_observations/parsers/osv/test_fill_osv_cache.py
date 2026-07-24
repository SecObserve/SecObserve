import os
from datetime import datetime, timezone
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests

from application.import_observations.models import OSV_Cache

# Adjust these imports based on your actual file structure
from application.import_observations.parsers.osv.parser import (
    OSV_MAX_RETRIES,
    OSV_Vulnerability,
    OSVParser,
    _create_osv_session,
    _get_osv_max_threads,
)


class TestOSVParserCache(TestCase):
    def setUp(self):
        self.parser = OSVParser()
        self.now = datetime(2023, 1, 1, tzinfo=timezone.utc)

    @patch("application.import_observations.models.OSV_Cache.objects")
    @patch("requests.Session.get")
    def test_fill_osv_cache_invalidation_and_deletion(self, mock_get, mock_objects):
        """
        Scenario: Cache has stale data.
        Verifies the .filter(...).delete() chain works and triggers a refresh.
        """
        # 1. Setup Input: We have an update for CVE-OLD
        new_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        old_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        vuln = OSV_Vulnerability(id="CVE-OLD", modified=new_date)

        # 2. Mock behavior for the stale data check
        stale_item = MagicMock(spec=OSV_Cache)
        stale_item.osv_id = "CVE-OLD"
        stale_item.modified = old_date

        # This mocks the first filter call: OSV_Cache.objects.filter(osv_id__in=...)
        # We make it return a list of items for the logic that builds valid/invalid IDs
        mock_objects.filter.return_value = [stale_item]

        # 3. Mock the Chained Deletion
        # For the line: OSV_Cache.objects.filter(osv_id__in=invalid_ids).delete()
        # We need a dedicated mock to represent the QuerySet returned by the second filter call
        mock_queryset = MagicMock()
        mock_objects.filter.side_effect = [
            [stale_item],  # First call: returns list for ID processing
            mock_queryset,  # Second call: returns the QuerySet for .delete()
        ]

        # 4. Mock API for refresh
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "CVE-OLD"}'
        mock_get.return_value = mock_response

        # Execute
        self.parser._fill_osv_cache([vuln])

        # Assertions
        # Verify the deletion was actually called on the filtered QuerySet
        mock_queryset.delete.assert_called_once()

        # Verify the API was called to get the fresh data
        self.assertTrue(mock_get.called)
        self.assertEqual(mock_objects.bulk_create.call_count, 1)

    @patch("application.import_observations.models.OSV_Cache.objects")
    @patch("requests.Session.get")
    def test_fill_osv_cache_mixed_state(self, mock_get, mock_objects):
        """
        Scenario: One valid cache hit, one missing (must fetch).
        """
        v1 = OSV_Vulnerability(id="CVE-VALID", modified=self.now)
        v2 = OSV_Vulnerability(id="CVE-MISSING", modified=self.now)

        # Mock DB: Only CVE-VALID exists
        valid_item = MagicMock(spec=OSV_Cache)
        valid_item.osv_id = "CVE-VALID"
        valid_item.modified = self.now
        valid_item.data = '{"id": "CVE-VALID"}'

        # Setup side_effect to handle multiple filter calls
        # 1st: The lookup of existing items
        # 2nd: The deletion filter (which will be empty in this case)
        mock_queryset_delete = MagicMock()
        mock_objects.filter.side_effect = [[valid_item], mock_queryset_delete]  # Initial lookup  # Deletion call

        # Mock API for the missing one
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"id": "CVE-MISSING"}'
        mock_get.return_value = mock_response

        # Execute
        result = self.parser._fill_osv_cache([v1, v2])

        # Assertions
        self.assertIn("CVE-VALID", result)
        self.assertIn("CVE-MISSING", result)
        self.assertEqual(mock_get.call_count, 1)  # Only called for CVE-MISSING

    @patch("application.import_observations.models.OSV_Cache.objects")
    @patch("requests.Session.get")
    def test_fill_osv_cache_propagates_persistent_error(self, mock_get, mock_objects):
        """
        Scenario: api.osv.dev keeps failing with the SSL EOF seen in production. Once the
        retrying session has given up, the error must propagate so that an incomplete scan
        is never silently recorded (bulk_create must not run).
        """
        vuln = OSV_Vulnerability(id="UBUNTU-CVE-2021-22924", modified=self.now)

        mock_objects.filter.side_effect = [[], MagicMock()]  # Nothing cached  # Deletion call

        mock_get.side_effect = requests.exceptions.SSLError("EOF occurred in violation of protocol")

        with self.assertRaises(requests.exceptions.SSLError):
            self.parser._fill_osv_cache([vuln])

        mock_objects.bulk_create.assert_not_called()


class TestOSVSession(TestCase):
    def test_session_is_configured_with_retries(self):
        # The retry/backoff itself lives in urllib3 (and is covered by urllib3's own tests);
        # here we verify our wiring: the adapter mounted for api.osv.dev carries the expected
        # Retry policy for GET requests and transient status codes.
        session = _create_osv_session()
        try:
            adapter = session.get_adapter("https://api.osv.dev/v1/vulns/CVE-2021-22924")
            retries = adapter.max_retries
            self.assertEqual(retries.total, OSV_MAX_RETRIES)
            self.assertIn("GET", retries.allowed_methods)
            self.assertIn(503, retries.status_forcelist)
        finally:
            session.close()


class TestOSVMaxThreads(TestCase):
    def test_default_when_env_unset(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OSV_MAX_THREADS", None)
            self.assertEqual(_get_osv_max_threads(), 32)

    @patch.dict(os.environ, {"OSV_MAX_THREADS": "8"})
    def test_reads_env_override(self):
        self.assertEqual(_get_osv_max_threads(), 8)
