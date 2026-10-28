from unittest.mock import MagicMock, patch

import requests

from application.import_observations.models import Api_Configuration
from application.import_observations.parsers.dependency_track.parser import (
    DependencyTrack,
)
from unittests.base_test_case import BaseTestCase


def _response(findings: list[dict], total_count: str | None) -> MagicMock:
    response = MagicMock()
    response.json.return_value = findings
    response.headers = {"X-Total-Count": total_count} if total_count is not None else {}
    return response


def _findings(start: int, count: int) -> list[dict]:
    return [{"vulnerability": {"vulnId": f"CVE-2026-{i:04d}"}} for i in range(start, start + count)]


class TestDependencyTrackParser(BaseTestCase):
    def setUp(self) -> None:
        self.api_configuration = Api_Configuration(
            base_url="https://dtrack.example.com",
            api_key="api_key",
            project_key="project_uuid",
            verify_ssl=True,
        )
        super().setUp()

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_invalid_connection(self, mock_requests: MagicMock) -> None:
        mock_requests.get.side_effect = requests.exceptions.ConnectionError("[Errno 111] Connection refused")

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertFalse(result)
        self.assertEqual(["Cannot access Dependency Track API, see backend log for details"], messages)
        self.assertFalse(data)

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_single_page(self, mock_requests: MagicMock) -> None:
        findings = _findings(0, 3)
        mock_requests.get.return_value = _response(findings, "3")

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertTrue(result)
        self.assertFalse(messages)
        self.assertEqual(findings, data)
        mock_requests.get.assert_called_once_with(
            "https://dtrack.example.com/api/v1/finding/project/project_uuid?suppressed=false",
            headers={"X-Api-Key": "api_key"},
            params={"pageNumber": 1, "pageSize": 100},
            timeout=60,
            verify=True,
            allow_redirects=False,
        )

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_multiple_pages(self, mock_requests: MagicMock) -> None:
        page_1 = _findings(0, 100)
        page_2 = _findings(100, 89)
        mock_requests.get.side_effect = [_response(page_1, "189"), _response(page_2, "189")]

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertTrue(result)
        self.assertFalse(messages)
        self.assertEqual(page_1 + page_2, data)
        self.assertEqual(2, mock_requests.get.call_count)
        self.assertEqual(
            [get_call.kwargs["params"] for get_call in mock_requests.get.call_args_list],
            [{"pageNumber": 1, "pageSize": 100}, {"pageNumber": 2, "pageSize": 100}],
        )

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_no_total_count_header(self, mock_requests: MagicMock) -> None:
        findings = _findings(0, 150)
        mock_requests.get.return_value = _response(findings, None)

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertTrue(result)
        self.assertFalse(messages)
        self.assertEqual(findings, data)
        mock_requests.get.assert_called_once()

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_empty_page_stops_paging(self, mock_requests: MagicMock) -> None:
        page_1 = _findings(0, 100)
        mock_requests.get.side_effect = [_response(page_1, "150"), _response([], "150")]

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertTrue(result)
        self.assertFalse(messages)
        self.assertEqual(page_1, data)
        self.assertEqual(2, mock_requests.get.call_count)

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_dependency_track_4_all_findings_in_one_response(self, mock_requests: MagicMock) -> None:
        findings = _findings(0, 150)
        mock_requests.get.return_value = _response(findings, "150")

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertTrue(result)
        self.assertFalse(messages)
        self.assertEqual(findings, data)
        mock_requests.get.assert_called_once()

    @patch("application.import_observations.parsers.dependency_track.parser.requests")
    def test_error_on_second_page(self, mock_requests: MagicMock) -> None:
        page_2 = MagicMock()
        page_2.status_code = 500
        page_2.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Server Error", response=page_2)
        mock_requests.get.side_effect = [_response(_findings(0, 100), "150"), page_2]

        result, messages, data = DependencyTrack().check_connection(self.api_configuration)

        self.assertFalse(result)
        self.assertEqual(["Cannot access Dependency Track API: HTTP status 500"], messages)
        self.assertFalse(data)
