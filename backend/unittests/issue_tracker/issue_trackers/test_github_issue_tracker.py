from unittest.mock import patch

from requests import Response
from requests.exceptions import HTTPError

from application.core.types import Severity, Status
from application.issue_tracker.issue_trackers.base_issue_tracker import Issue
from application.issue_tracker.issue_trackers.github_issue_tracker import (
    GitHubIssueTracker,
)
from unittests.base_test_case import BaseTestCase


class TestGitHubIssueTracker(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.observation_1.pk = 1
        self.observation_1.current_severity = Severity.SEVERITY_CRITICAL
        self.observation_1.description = "description_1"
        self.observation_1.product.issue_tracker_project_id = "gh_project_1"
        self.observation_1.product.issue_tracker_labels = "label_1, label_2"
        self.observation_1.product.issue_tracker_api_key = "api_key_1"

    @patch("requests.post")
    def test_create_issue(self, post_mock):
        class MockResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return {"number": "gh_1"}

        response = MockResponse()
        post_mock.return_value = response

        issue_tracker = GitHubIssueTracker()
        issue_id = issue_tracker.create_issue(self.observation_1)

        post_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"title": "Critical vulnerability: \\"observation_1\\"", "body": "description_1\\n\\n**Branch:** branch_1\\n\\n**SecObserve observation:** [/#/observations/1/show](/#/observations/1/show)", "labels": ["label_1", "label_2"]}',
            timeout=60,
        )
        self.assertEqual("gh_1", issue_id)

    @patch("requests.post")
    def test_create_issue_exception(self, post_mock):
        response = Response()
        response.status_code = 500
        response.reason = "unknown reason"
        response.url = "https://api.github.com/repos/gh_project_1/issues"
        post_mock.return_value = response
        with self.assertRaises(HTTPError) as e:
            issue_tracker = GitHubIssueTracker()
            issue_tracker.create_issue(self.observation_1)

        self.assertEqual(
            "500 Server Error: unknown reason for url: https://api.github.com/repos/gh_project_1/issues",
            str(e.exception),
        )
        post_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"title": "Critical vulnerability: \\"observation_1\\"", "body": "description_1\\n\\n**Branch:** branch_1\\n\\n**SecObserve observation:** [/#/observations/1/show](/#/observations/1/show)", "labels": ["label_1", "label_2"]}',
            timeout=60,
        )

    @patch("requests.get")
    def test_get_issue_exception(self, get_mock):
        response = Response()
        response.status_code = 500
        response.reason = "unknown reason"
        response.url = "https://api.github.com/repos/gh_project_1/issues/gh_1"
        get_mock.return_value = response
        with self.assertRaises(HTTPError) as e:
            issue_tracker = GitHubIssueTracker()
            issue_tracker.get_issue(self.observation_1.product, "gh_1")

        self.assertEqual(
            "500 Server Error: unknown reason for url: https://api.github.com/repos/gh_project_1/issues/gh_1",
            str(e.exception),
        )
        get_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            timeout=60,
        )

    @patch("requests.get")
    def test_get_issue_not_found(self, get_mock):
        get_mock.return_value.status_code = 404
        issue_tracker = GitHubIssueTracker()
        issue = issue_tracker.get_issue(self.observation_1.product, "gh_1")
        self.assertIsNone(issue)
        get_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            timeout=60,
        )

    @patch("requests.get")
    def test_get_issue_success(self, get_mock):
        get_mock.return_value.status_code = 200
        get_mock.return_value.json.return_value = {
            "number": "gh_1",
            "title": "title_1",
            "body": "description_1",
            "labels": [{"name": "label_1"}, {"name": "label_2"}],
        }
        issue_tracker = GitHubIssueTracker()
        issue = issue_tracker.get_issue(self.observation_1.product, "gh_1")
        expected_issue = Issue(
            id="gh_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        self.assertEqual(expected_issue, issue)
        get_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            timeout=60,
        )

    @patch("requests.patch")
    def test_update_issue_no_id(self, patch_mock):
        issue_tracker = GitHubIssueTracker()
        issue = issue_tracker.update_issue(self.observation_1, None)
        self.assertIsNone(issue)
        patch_mock.assert_not_called()

    @patch("requests.patch")
    def test_update_issue_exception(self, patch_mock):
        response = Response()
        response.status_code = 404
        response.reason = "unknown reason"
        response.url = "https://api.github.com/repos/gh_project_1/issues/gh_1"
        patch_mock.return_value = response
        self.observation_1.issue_tracker_issue_id = "gh_1"
        with self.assertRaises(HTTPError) as e:
            issue_tracker = GitHubIssueTracker()
            self.observation_1.product.issue_tracker_labels = "label_2,label_3"
            issue = Issue(
                id="gh_1",
                title="title_1",
                description="description_1",
                labels="label_1,label_2",
            )
            issue_tracker.update_issue(self.observation_1, issue)

        self.assertEqual(
            "404 Client Error: unknown reason for url: https://api.github.com/repos/gh_project_1/issues/gh_1",
            str(e.exception),
        )
        patch_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"title": "Critical vulnerability: \\"observation_1\\"", "body": "description_1\\n\\n**Branch:** branch_1\\n\\n**SecObserve observation:** [/#/observations/1/show](/#/observations/1/show)", "state": "open", "labels": ["label_2", "label_3", "label_1"]}',
            timeout=60,
        )

    @patch("requests.patch")
    def test_update_issue_success(self, patch_mock):
        patch_mock.return_value.status_code = 200
        self.observation_1.issue_tracker_issue_id = "gh_1"
        issue_tracker = GitHubIssueTracker()
        self.observation_1.product.issue_tracker_labels = "label_2,label_3"
        issue = Issue(
            id="gh_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )

        issue_tracker.update_issue(self.observation_1, issue)

        patch_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"title": "Critical vulnerability: \\"observation_1\\"", "body": "description_1\\n\\n**Branch:** branch_1\\n\\n**SecObserve observation:** [/#/observations/1/show](/#/observations/1/show)", "state": "open", "labels": ["label_2", "label_3", "label_1"]}',
            timeout=60,
        )

    @patch("requests.patch")
    def test_close_issue_no_id(self, patch_mock):
        issue_tracker = GitHubIssueTracker()
        issue = issue_tracker.close_issue(self.observation_1, None)
        self.assertIsNone(issue)
        patch_mock.assert_not_called()

    @patch("requests.patch")
    def test_close_issue_exception(self, patch_mock):
        response = Response()
        response.status_code = 404
        response.reason = "unknown reason"
        response.url = "https://api.github.com/repos/gh_project_1/issues/gh_1"
        patch_mock.return_value = response
        self.observation_1.issue_tracker_issue_id = "gh_1"
        self.observation_1.product.issue_tracker_labels = "label_2,label_3"
        self.observation_1.current_status = Status.STATUS_RESOLVED
        with self.assertRaises(HTTPError) as e:
            issue_tracker = GitHubIssueTracker()
            issue = Issue(
                id="gh_1",
                title="title_1",
                description="description_1",
                labels="label_1,label_2",
            )
            issue_tracker.close_issue(self.observation_1, issue)

        self.assertEqual(
            "404 Client Error: unknown reason for url: https://api.github.com/repos/gh_project_1/issues/gh_1",
            str(e.exception),
        )
        patch_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"title": "Critical vulnerability: \\"observation_1\\"", "body": "description_1\\n\\n**Branch:** branch_1\\n\\n**SecObserve observation:** [/#/observations/1/show](/#/observations/1/show)\\n\\n**Observation status:** Resolved", "state": "closed", "labels": ["label_2", "label_3", "label_1"]}',
            timeout=60,
        )

    @patch("requests.patch")
    def test_close_issue_success(self, patch_mock):
        patch_mock.return_value.status_code = 200
        self.observation_1.issue_tracker_issue_id = "gh_1"
        self.observation_1.product.issue_tracker_labels = "label_2,label_3"
        self.observation_1.current_status = Status.STATUS_RESOLVED
        issue_tracker = GitHubIssueTracker()
        issue = Issue(
            id="gh_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )

        issue_tracker.close_issue(self.observation_1, issue)

        patch_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"title": "Critical vulnerability: \\"observation_1\\"", "body": "description_1\\n\\n**Branch:** branch_1\\n\\n**SecObserve observation:** [/#/observations/1/show](/#/observations/1/show)\\n\\n**Observation status:** Resolved", "state": "closed", "labels": ["label_2", "label_3", "label_1"]}',
            timeout=60,
        )

    @patch("requests.patch")
    def test_close_issue_for_deleted_observation_exception(self, patch_mock):
        response = Response()
        response.status_code = 404
        response.reason = "unknown reason"
        response.url = "https://api.github.com/repos/gh_project_1/issues/gh_1"
        patch_mock.return_value = response
        self.observation_1.product.issue_tracker_labels = "label_2,label_3"
        with self.assertRaises(HTTPError) as e:
            issue_tracker = GitHubIssueTracker()
            issue = Issue(
                id="gh_1",
                title="title_1",
                description="description_1",
                labels="label_1,label_2",
            )
            issue_tracker.close_issue_for_deleted_observation(self.observation_1.product, issue)

        self.assertEqual(
            "404 Client Error: unknown reason for url: https://api.github.com/repos/gh_project_1/issues/gh_1",
            str(e.exception),
        )
        patch_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"body": "**--- Observation has been deleted ---**\\n\\ndescription_1", "state": "closed", "labels": ["label_2", "label_3", "label_1"]}',
            timeout=60,
        )

    @patch("requests.patch")
    def test_close_issue_for_deleted_observation_success(self, patch_mock):
        patch_mock.return_value.status_code = 200
        self.observation_1.product.issue_tracker_labels = "label_2,label_3"
        issue_tracker = GitHubIssueTracker()
        issue = Issue(
            id="gh_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )

        issue_tracker.close_issue_for_deleted_observation(self.observation_1.product, issue)

        patch_mock.assert_called_once_with(
            url="https://api.github.com/repos/gh_project_1/issues/gh_1",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": "Bearer api_key_1",
            },
            data='{"body": "**--- Observation has been deleted ---**\\n\\ndescription_1", "state": "closed", "labels": ["label_2", "label_3", "label_1"]}',
            timeout=60,
        )

    def test_get_frontend_issue_url(self):
        issue_tracker = GitHubIssueTracker()
        frontend_issue_url = issue_tracker.get_frontend_issue_url(self.observation_1.product, "gh_1")
        self.assertEqual("https://github.com/gh_project_1/issues/gh_1", frontend_issue_url)

    @patch("requests.post")
    def test_create_issue_github_enterprise(self, post_mock):
        self.observation_1.product.issue_tracker_base_url = "https://github.example.com/api/v3"
        post_mock.return_value.raise_for_status.return_value = None
        post_mock.return_value.json.return_value = {"number": "gh_1"}

        issue_tracker = GitHubIssueTracker()
        issue_id = issue_tracker.create_issue(self.observation_1)

        self.assertEqual("gh_1", issue_id)
        self.assertEqual(
            "https://github.example.com/api/v3/repos/gh_project_1/issues",
            post_mock.call_args.kwargs["url"],
        )

    def test_get_issue_tracker_base_url_github_com(self):
        self.observation_1.product.issue_tracker_base_url = "https://api.github.com"
        issue_tracker = GitHubIssueTracker()
        self.assertEqual(
            "https://api.github.com/repos/gh_project_1/issues",
            issue_tracker._get_issue_tracker_base_url(self.observation_1.product),
        )

    def test_get_frontend_issue_url_github_enterprise(self):
        self.observation_1.product.issue_tracker_base_url = "https://github.example.com/api/v3/"
        issue_tracker = GitHubIssueTracker()
        frontend_issue_url = issue_tracker.get_frontend_issue_url(self.observation_1.product, "gh_1")
        self.assertEqual("https://github.example.com/gh_project_1/issues/gh_1", frontend_issue_url)
