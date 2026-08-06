from unittest.mock import call, patch

from django.core.management import call_command

from application.access_control.models import User
from application.core.models import Branch, Observation, Product
from application.core.types import Severity, Status
from application.issue_tracker.issue_trackers.base_issue_tracker import Issue
from application.issue_tracker.issue_trackers.github_issue_tracker import (
    GitHubIssueTracker,
)
from application.issue_tracker.issue_trackers.gitlab_issue_tracker import (
    GitLabIssueTracker,
)
from application.issue_tracker.services.issue_tracker import (
    issue_tracker_factory,
    push_deleted_observation_to_issue_tracker,
    push_observation_to_issue_tracker,
    push_observations_to_issue_tracker,
)
from application.issue_tracker.types import Issue_Tracker
from unittests.base_test_case import BaseTestCase


class TestIssueTracker(BaseTestCase):
    def setUp(self):
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUp()

    # --- push_observations_to_issue_tracker ---

    @patch("application.issue_tracker.services.issue_tracker.push_observation_to_issue_tracker")
    def test_push_observations_to_issue_tracker_not_active(self, mock):
        product = Product.objects.get(pk=1)
        push_observations_to_issue_tracker(product, False)
        mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.push_observation_to_issue_tracker")
    @patch("application.issue_tracker.services.issue_tracker.get_current_user")
    def test_push_observations_to_issue_tracker(self, mock_current_user, mock_issue_tracker):
        product = Product.objects.get(pk=1)
        product.issue_tracker_active = True
        observation = Observation.objects.get(pk=1)
        user = User.objects.get(pk=1)
        mock_current_user.return_value = user

        push_observations_to_issue_tracker(product, {observation})

        mock_current_user.assert_called_once()
        mock_issue_tracker.assert_called_once_with(observation, user)

    # --- push_observation_to_issue_tracker / no minimum severity---

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_observation_to_issue_tracker_not_active(self, mock):
        observation = Observation.objects.get(pk=1)
        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)
        mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_observation_to_issue_tracker_not_default_branch(self, mock):
        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        not_default_branch = Branch.objects.get(pk=2)
        observation.branch = not_default_branch
        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)
        mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_open_no_id_no_issue(self, observation_mock, mock):
        mock.return_value.get_issue.return_value = None

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.current_status = Status.STATUS_OPEN

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        expected_calls = [call(observation.product), call().create_issue(observation)]
        mock.assert_has_calls(expected_calls, any_order=False)
        observation_mock.assert_called_once()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_open_with_id_with_issue(self, observation_mock, factory_mock):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        factory_mock.return_value.get_issue.return_value = issue

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.current_status = Status.STATUS_OPEN
        observation.issue_tracker_issue_id = "123"

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        observation_mock.assert_not_called()
        expected_calls = [
            call(observation.product),
            call().get_issue(observation.product, "123"),
            call().update_issue(observation, issue),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_closed_no_id_no_issue(self, observation_mock, factory_mock):
        factory_mock.return_value.get_issue.return_value = None

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.current_status = Status.STATUS_NOT_AFFECTED

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        expected_calls = [call(observation.product)]
        factory_mock.assert_has_calls(expected_calls, any_order=False)
        observation_mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_closed_with_id_with_issue(self, observation_mock, factory_mock):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        factory_mock.return_value.get_issue.return_value = issue

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.current_status = Status.STATUS_FALSE_POSITIVE
        observation.issue_tracker_issue_id = "123"

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        expected_calls = [
            call(observation.product),
            call().get_issue(observation.product, "123"),
            call().close_issue(observation, issue),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)
        observation_mock.assert_called_once()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.issue_tracker.services.issue_tracker.handle_task_exception")
    def test_push_observation_to_issue_tracker_exception(self, exception_mock, factory_mock):
        exception = Exception("error")
        factory_mock.side_effect = exception

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, self.user_internal)

        exception_mock.assert_called_with(exception, self.user_internal)

    # --- push_observation_to_issue_tracker / higher or same than minimum severity ---

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_with_issue_higher_than_minimum(self, observation_mock, factory_mock):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        factory_mock.return_value.get_issue.return_value = issue

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.product.issue_tracker_minimum_severity = Severity.SEVERITY_HIGH
        observation.current_status = Status.STATUS_OPEN
        observation.current_severity = Severity.SEVERITY_HIGH
        observation.numerical_severity = Severity.NUMERICAL_SEVERITIES.get(observation.current_severity, 99)
        observation.issue_tracker_issue_id = "123"

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        self.assertEqual(observation_mock.call_count, 2)
        expected_calls = [
            call(observation.product),
            call().get_issue(observation.product, "123"),
            call().create_issue(observation),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_with_issue_higher_than_minimum(self, observation_mock, factory_mock):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        factory_mock.return_value.get_issue.return_value = issue

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.product.issue_tracker_minimum_severity = Severity.SEVERITY_HIGH
        observation.current_status = Status.STATUS_OPEN
        observation.current_severity = Severity.SEVERITY_HIGH
        observation.numerical_severity = Severity.NUMERICAL_SEVERITIES.get(observation.current_severity, 99)
        observation.issue_tracker_issue_id = "123"

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        observation_mock.assert_not_called()
        expected_calls = [
            call(observation.product),
            call().get_issue(observation.product, "123"),
            call().update_issue(observation, issue),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)

    # --- push_observation_to_issue_tracker / lower than minimum severity ---

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_no_issue_lower_than_minimum(self, observation_mock, factory_mock):
        factory_mock.return_value.get_issue.return_value = None

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.product.issue_tracker_minimum_severity = Severity.SEVERITY_HIGH
        observation.current_status = Status.STATUS_OPEN
        observation.current_severity = Severity.SEVERITY_MEDIUM
        observation.numerical_severity = Severity.NUMERICAL_SEVERITIES.get(observation.current_severity, 99)

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        observation_mock.assert_not_called()
        expected_calls = [
            call(observation.product),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_with_issue_lower_than_minimum_not_closed(
        self, observation_mock, factory_mock
    ):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        factory_mock.return_value.get_issue.return_value = issue

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.product.issue_tracker_minimum_severity = Severity.SEVERITY_HIGH
        observation.current_status = Status.STATUS_OPEN
        observation.current_severity = Severity.SEVERITY_MEDIUM
        observation.numerical_severity = Severity.NUMERICAL_SEVERITIES.get(observation.current_severity, 99)
        observation.issue_tracker_issue_id = "123"

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        observation_mock.assert_called_once()
        expected_calls = [
            call(observation.product),
            call().get_issue(observation.product, "123"),
            call().close_issue(observation, issue),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.core.models.Observation.save")
    def test_push_observation_to_issue_tracker_with_issue_lower_than_minimum_already_closed(
        self, observation_mock, factory_mock
    ):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        factory_mock.return_value.get_issue.return_value = issue

        observation = Observation.objects.get(pk=1)
        observation.product.issue_tracker_active = True
        observation.product.issue_tracker_minimum_severity = Severity.SEVERITY_HIGH
        observation.current_status = Status.STATUS_OPEN
        observation.current_severity = Severity.SEVERITY_MEDIUM
        observation.numerical_severity = Severity.NUMERICAL_SEVERITIES.get(observation.current_severity, 99)
        observation.issue_tracker_issue_id = "123"
        observation.issue_tracker_issue_closed = True

        with self.captureOnCommitCallbacks(execute=True):
            push_observation_to_issue_tracker(observation, None)

        observation_mock.assert_not_called()
        expected_calls = [
            call(observation.product),
            call().get_issue(observation.product, "123"),
        ]
        factory_mock.assert_has_calls(expected_calls, any_order=False)

    # --- push_deleted_observation_to_issue_tracker ---

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_deleted_observation_not_active_no_id(self, mock):
        product = Product.objects.get(pk=1)
        with self.captureOnCommitCallbacks(execute=True):
            push_deleted_observation_to_issue_tracker(product, "", None)
        mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_deleted_observation_active_no_id(self, mock):
        product = Product.objects.get(pk=1)
        product.issue_tracker_active = True
        with self.captureOnCommitCallbacks(execute=True):
            push_deleted_observation_to_issue_tracker(product, "", None)
        mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_deleted_observation_not_active_with_id(self, mock):
        product = Product.objects.get(pk=1)
        with self.captureOnCommitCallbacks(execute=True):
            push_deleted_observation_to_issue_tracker(product, "123", None)
        mock.assert_not_called()

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_deleted_observation_active_with_id_no_issue(self, mock):
        mock.return_value.get_issue.return_value = None
        product = Product.objects.get(pk=1)
        product.issue_tracker_active = True
        with self.captureOnCommitCallbacks(execute=True):
            push_deleted_observation_to_issue_tracker(product, "123", None)
        expected_calls = [call(product), call().get_issue(product, "123")]
        mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    def test_push_deleted_observation_active_with_id_with_issue(self, mock):
        issue = Issue(id=1, title="title", description="description", labels="labels")
        mock.return_value.get_issue.return_value = issue
        product = Product.objects.get(pk=1)
        product.issue_tracker_active = True
        with self.captureOnCommitCallbacks(execute=True):
            push_deleted_observation_to_issue_tracker(product, "123", None)
        expected_calls = [
            call(product),
            call().get_issue(product, "123"),
            call().close_issue_for_deleted_observation(product, issue),
        ]
        mock.assert_has_calls(expected_calls, any_order=False)

    @patch("application.issue_tracker.services.issue_tracker.issue_tracker_factory")
    @patch("application.issue_tracker.services.issue_tracker.handle_task_exception")
    def test_push_deleted_observation_exception(self, exception_mock, factory_mock):
        exception = Exception("error")
        factory_mock.side_effect = exception

        product = Product.objects.get(pk=1)
        product.issue_tracker_active = True
        with self.captureOnCommitCallbacks(execute=True):
            push_deleted_observation_to_issue_tracker(product, "123", self.user_internal)

        exception_mock.assert_called_with(exception, self.user_internal)

    # --- issue_tracker_factory ---

    def test_issue_tracker_factory_GitHub(self):
        product = Product.objects.get(pk=1)
        product.issue_tracker_type = Issue_Tracker.ISSUE_TRACKER_GITHUB
        self.assertIsInstance(issue_tracker_factory(product), GitHubIssueTracker)

    def test_issue_tracker_factory_GitLab(self):
        product = Product.objects.get(pk=1)
        product.issue_tracker_type = Issue_Tracker.ISSUE_TRACKER_GITLAB
        self.assertIsInstance(issue_tracker_factory(product), GitLabIssueTracker)

    def test_issue_tracker_exception(self):
        product = Product.objects.get(pk=1)
        product.issue_tracker_type = "invalid"
        with self.assertRaises(ValueError):
            issue_tracker_factory(product)
