from dataclasses import dataclass
from unittest.mock import patch

from application.core.types import Severity, Status
from application.issue_tracker.issue_trackers.base_issue_tracker import Issue
from application.issue_tracker.issue_trackers.jira_issue_tracker import JiraIssueTracker
from unittests.base_test_case import BaseTestCase


@dataclass
class JiraIssueFields:
    summary: str
    description: str
    labels: list
    status: str


@dataclass
class JiraIssue:
    key: str
    fields: JiraIssueFields

    def update(self, summary: str, description: str) -> None:
        self.fields.summary = summary
        self.fields.description = description


class TestJiraIssueTracker(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.observation_1.pk = 1
        self.observation_1.current_severity = Severity.SEVERITY_CRITICAL
        self.observation_1.description = "description_1"
        self.observation_1.product.issue_tracker_project_id = "jira_project_1"
        self.observation_1.product.issue_tracker_base_url = "https://jira.com"
        self.observation_1.product.issue_tracker_labels = "label_1, label_2"
        self.observation_1.product.issue_tracker_api_key = "api_key_1"
        self.observation_1.product.issue_tracker_username = "username_1"
        self.observation_1.product.issue_tracker_status_closed = "Closed"

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.create_issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.get_base_url_frontend")
    @patch("application.core.models.Observation.save")
    def test_create_issue(self, save_mock, base_url_mock, create_issue_mock, jira_mock):
        self.observation_1.product.issue_tracker_issue_type = "Vulnerability"
        self.observation_1.description = "description_1\n\n**Snippet**: ```codeblock```"
        base_url_mock.return_value = "https://secobserve.com/"
        create_issue_mock.return_value = JiraIssue(
            key="jira_issue_1",
            fields=JiraIssueFields(
                summary="title_1",
                description="description_1\n\n*Snippet*: {code}codeblock{code}\n\n*Branch:* branch_1\n\n*SecObserve observation:* https://secobserve.com/#/observations/1/show",
                labels=["label_1", "label_2"],
                status="Open",
            ),
        )

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_id = issue_tracker.create_issue(self.observation_1)

        create_issue_mock.assert_called_once_with(
            project="jira_project_1",
            summary='Critical vulnerability: "observation_1"',
            description="description_1\n\n*Snippet*: {code}codeblock{code}\n\n*Branch:* branch_1\n\n*SecObserve observation:* https://secobserve.com/#/observations/1/show",
            labels=["label_1", "label_2"],
            issuetype="Vulnerability",
        )
        base_url_mock.assert_called_once()
        save_mock.assert_called_once()
        self.assertEqual("jira_issue_1", issue_id)
        self.assertEqual("Open", self.observation_1.issue_tracker_jira_initial_status)
        self.assertEqual(0, issue_tracker.jira._session.max_redirects)

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    def test_get_issue_not_found(self, issue_mock, jira_mock):
        issue_mock.return_value = None

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue = issue_tracker.get_issue(self.observation_1.product, "jira_1")

        self.assertIsNone(issue)
        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    def test_get_issue_success(self, issue_mock, jira_mock):
        issue_mock.return_value = JiraIssue(
            key="jira_issue_1",
            fields=JiraIssueFields(
                summary="title_1",
                description="description_1",
                labels=["label_1", "label_2"],
                status="Open",
            ),
        )

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue = issue_tracker.get_issue(self.observation_1.product, "jira_1")

        self.assertEqual(
            Issue(
                id="jira_1",
                title="title_1",
                description="description_1",
                labels="label_1,label_2",
            ),
            issue,
        )
        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    def test_update_issue_no_id(self, update_mock, issue_mock, jira_mock):
        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.update_issue(self.observation_1, None)

        issue_mock.assert_not_called()
        update_mock.assert_not_called()

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_update_issue_no_jira_issue(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        self.observation_1.issue_tracker_issue_id = "jira_1"
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        issue_mock.return_value = None

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.update_issue(self.observation_1, issue)

        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        update_mock.assert_not_called()
        transition_issue_mock.assert_not_called()

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_update_issue_success(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        self.observation_1.issue_tracker_issue_id = "jira_1"
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        jira_issue = JiraIssue(
            key="jira_issue_1",
            fields=JiraIssueFields(
                summary="title_old",
                description="description_old",
                labels=["label_1", "label_2"],
                status="Open",
            ),
        )
        issue_mock.return_value = jira_issue

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.update_issue(self.observation_1, issue)

        self.assertEqual('Critical vulnerability: "observation_1"', jira_issue.fields.summary)
        description = "description_1\n\n*Branch:* branch_1\n\n*SecObserve observation:* /#/observations/1/show"
        self.assertEqual(description, jira_issue.fields.description)
        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        transition_issue_mock.assert_not_called()

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_update_issue_success_transition(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        self.observation_1.issue_tracker_issue_id = "jira_1"
        self.observation_1.issue_tracker_jira_initial_status = "Open"
        self.observation_1.product.issue_tracker_status_closed = "Done"
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        jira_issue = JiraIssue(
            key="jira_issue_1",
            fields=JiraIssueFields(
                summary="title_old",
                description="description_old",
                labels=["label_1", "label_2"],
                status="Done",
            ),
        )
        issue_mock.return_value = jira_issue

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.update_issue(self.observation_1, issue)

        summary = 'Critical vulnerability: "observation_1"'
        self.assertEqual(summary, jira_issue.fields.summary)
        description = "description_1\n\n*Branch:* branch_1\n\n*SecObserve observation:* /#/observations/1/show"
        self.assertEqual(description, jira_issue.fields.description)
        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        transition_issue_mock.assert_called_with(
            JiraIssue(
                key="jira_issue_1",
                fields=JiraIssueFields(
                    summary=summary,
                    description=description,
                    labels=["label_1", "label_2"],
                    status="Done",
                ),
            ),
            "Open",
        )

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    def test_close_issue_no_id(self, update_mock, issue_mock, jira_mock):
        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.close_issue(self.observation_1, None)

        issue_mock.assert_not_called()
        update_mock.assert_not_called()

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_close_issue_no_jira_issue(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        self.observation_1.issue_tracker_issue_id = "jira_1"
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        issue_mock.return_value = None

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.close_issue(self.observation_1, issue)

        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        update_mock.assert_not_called()
        transition_issue_mock.assert_not_called()

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_close_issue_success(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        self.observation_1.issue_tracker_issue_id = "jira_1"
        self.observation_1.current_status = Status.STATUS_RESOLVED
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        jira_issue = JiraIssue(
            key="jira_issue_1",
            fields=JiraIssueFields(
                summary="title_old",
                description="description_old",
                labels=["label_1", "label_2"],
                status="Open",
            ),
        )
        issue_mock.return_value = jira_issue

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.close_issue(self.observation_1, issue)

        summary = 'Critical vulnerability: "observation_1"'
        self.assertEqual(summary, jira_issue.fields.summary)
        description = "description_1\n\n*Branch:* branch_1\n\n*SecObserve observation:* /#/observations/1/show\n\n*Observation status:* Resolved"
        self.assertEqual(description, jira_issue.fields.description)
        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        transition_issue_mock.assert_called_once_with(
            JiraIssue(
                key="jira_issue_1",
                fields=JiraIssueFields(
                    summary=summary,
                    description=description,
                    labels=["label_1", "label_2"],
                    status="Open",
                ),
            ),
            "Closed",
        )

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_close_deleted_issue_no_jira_issue(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        issue_mock.return_value = None

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.close_issue_for_deleted_observation(self.observation_1.product, issue)

        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        update_mock.assert_not_called()
        transition_issue_mock.assert_not_called()

    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.server_info")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.issue")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JiraIssue.update")
    @patch("application.issue_tracker.issue_trackers.jira_issue_tracker.JIRA.transition_issue")
    def test_close_deleted_issue_success(self, transition_issue_mock, update_mock, issue_mock, jira_mock):
        issue = Issue(
            id="jira_1",
            title="title_1",
            description="description_1",
            labels="label_1,label_2",
        )
        jira_issue = JiraIssue(
            key="jira_issue_1",
            fields=JiraIssueFields(
                summary="title_old",
                description="description_old",
                labels=["label_1", "label_2"],
                status="Open",
            ),
        )
        issue_mock.return_value = jira_issue

        issue_tracker = JiraIssueTracker(self.observation_1.product)
        issue_tracker.close_issue_for_deleted_observation(self.observation_1.product, issue)

        self.assertEqual("title_old", jira_issue.fields.summary)
        description = "*--- Observation has been deleted ---*\n\ndescription_old"
        self.assertEqual(description, jira_issue.fields.description)
        issue_mock.assert_called_once_with("jira_1", fields="summary,description,labels,status")
        transition_issue_mock.assert_called_once_with(
            JiraIssue(
                key="jira_issue_1",
                fields=JiraIssueFields(
                    summary="title_old",
                    description=description,
                    labels=["label_1", "label_2"],
                    status="Open",
                ),
            ),
            "Closed",
        )
