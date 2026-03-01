from unittest.mock import patch

from application.core.models import Observation, Service
from application.core.types import Severity
from application.issue_tracker.issue_trackers.base_issue_tracker import BaseIssueTracker
from unittests.base_test_case import BaseTestCase


class TestBaseIssueTracker(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.observation_1.current_severity = Severity.SEVERITY_HIGH

    def test_get_title_no_origin(self):
        issue_tracker = BaseIssueTracker()
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual('High vulnerability: "observation_1"', title)

    def test_get_title_service(self):
        issue_tracker = BaseIssueTracker()
        service = Service(name="service_1")
        self.observation_1.origin_service = service
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual('High vulnerability: "observation_1" in service_1', title)

    def test_get_title_component(self):
        issue_tracker = BaseIssueTracker()
        self.observation_1.origin_component_name_version = "component_1:1.0.0"
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual('High vulnerability: "observation_1" in component_1:1.0.0', title)

    def test_get_title_docker_image(self):
        issue_tracker = BaseIssueTracker()
        self.observation_1.origin_docker_image_name_tag_short = "image_1:1.0.0"
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual('High vulnerability: "observation_1" in image_1:1.0.0', title)

    def test_get_title_endpoint(self):
        issue_tracker = BaseIssueTracker()
        self.observation_1.origin_endpoint_hostname = "hostname_1.example.com"
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual('High vulnerability: "observation_1" in hostname_1.example.com', title)

    def test_get_title_source(self):
        issue_tracker = BaseIssueTracker()
        self.observation_1.origin_source_file = "application.py"
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual('High vulnerability: "observation_1" in application.py', title)

    def test_get_title_all(self):
        issue_tracker = BaseIssueTracker()
        service = Service(name="service_1")
        self.observation_1.origin_service = service
        self.observation_1.origin_component_name_version = "component_1:1.0.0"
        self.observation_1.origin_docker_image_name_tag_short = "image_1:1.0.0"
        self.observation_1.origin_endpoint_hostname = "hostname_1.example.com"
        self.observation_1.origin_source_file = "application.py"
        title = issue_tracker._get_title(self.observation_1)
        self.assertEqual(
            'High vulnerability: "observation_1" in service_1 / component_1:1.0.0 / image_1:1.0.0 / hostname_1.example.com / application.py',
            title,
        )

    @patch("application.issue_tracker.issue_trackers.base_issue_tracker.get_base_url_frontend")
    def test_get_description_with_branch(self, base_url_mock):
        base_url_mock.return_value = "http://localhost:3000"
        self.observation_1.pk = 1
        self.observation_1.description = "description_1"

        issue_tracker = BaseIssueTracker()
        description = issue_tracker._get_description(self.observation_1)

        expected_description = """description_1

**Branch:** branch_1

**SecObserve observation:** [http://localhost:3000#/observations/1/show](http://localhost:3000#/observations/1/show)"""
        self.assertEqual(expected_description, description)
        base_url_mock.assert_called_once()

    @patch("application.issue_tracker.issue_trackers.base_issue_tracker.get_base_url_frontend")
    def test_get_description_without_branch(self, base_url_mock):
        base_url_mock.return_value = "http://localhost:3000"
        observation_2 = Observation(pk=2, product=self.product_1, description="description_2")

        issue_tracker = BaseIssueTracker()
        description = issue_tracker._get_description(observation_2)

        expected_description = """description_2

**SecObserve observation:** [http://localhost:3000#/observations/2/show](http://localhost:3000#/observations/2/show)"""
        self.assertEqual(expected_description, description)
        base_url_mock.assert_called_once()

    def test_get_description_for_deleted_observation_without_description(self):
        issue_tracker = BaseIssueTracker()
        description = issue_tracker._get_description_for_deleted_observation(None)

        expected_description = """**--- Observation has been deleted ---**

None"""
        self.assertEqual(expected_description, description)

    def test_get_description_for_deleted_observation_with_description(self):
        issue_tracker = BaseIssueTracker()
        description = issue_tracker._get_description_for_deleted_observation("original_description")

        expected_description = """**--- Observation has been deleted ---**

original_description"""
        self.assertEqual(expected_description, description)

    def test_normalize_base_url_with_trailing_slash(self):
        issue_tracker = BaseIssueTracker()
        base_url = issue_tracker._normalize_base_url("http://localhost:3000/")

        self.assertEqual("http://localhost:3000", base_url)

    def test_normalize_base_url_without_trailing_slash(self):
        issue_tracker = BaseIssueTracker()
        base_url = issue_tracker._normalize_base_url("http://localhost:3000")

        self.assertEqual("http://localhost:3000", base_url)
