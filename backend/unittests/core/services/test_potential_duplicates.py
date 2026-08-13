from os import path
from unittest.mock import call, patch

from application.core.models import Observation, Potential_Duplicate, Product
from application.core.services.potential_duplicates import (
    DuplicateCandidate,
    _match_duplicate_candidates,
    find_potential_duplicates,
    set_potential_duplicate,
    set_potential_duplicate_both_ways,
)
from application.core.types import Status
from application.import_observations.management.commands.register_parsers import Command
from application.import_observations.models import Parser
from application.import_observations.services.import_observations import (
    FileUploadParameters,
    file_upload_observations,
)
from unittests.base_test_case import BaseTestCase


class TestSetPotentialDuplicate(BaseTestCase):
    def setUp(self):

        self.observation = Observation()
        self.observation.product = Product()
        self.observation.current_status = Status.STATUS_OPEN
        self.observation.has_potential_duplicates = True
        super().setUp()

    @patch("application.core.services.potential_duplicates.set_potential_duplicate")
    @patch("application.core.models.Potential_Duplicate.objects.filter")
    def test_set_potential_duplicate_both_ways(self, filter_mock, set_potential_duplicate_mock):
        potential_duplicate_observation = Observation(title="observation_2", product=self.product_1)

        potential_duplicate = Potential_Duplicate()
        potential_duplicate.observation = self.observation_1
        potential_duplicate.potential_duplicate_observation = potential_duplicate_observation

        filter_mock.return_value = [potential_duplicate]

        set_potential_duplicate_both_ways(self.observation)

        self.assertEqual(set_potential_duplicate_mock.call_count, 2)
        # set_potential_duplicate_mock.assert_has_calls([call(self.observation_1), call(potential_duplicate_observation)])

    @patch("application.core.models.Potential_Duplicate.objects.filter")
    @patch("application.core.models.Observation.save")
    def test_set_potential_duplicate_no_open_duplicates(self, save_mock, filter_mock):
        filter_mock.return_value.count.return_value = 0

        set_potential_duplicate(self.observation)

        self.assertFalse(self.observation.has_potential_duplicates)
        save_mock.assert_called_once()

    @patch("application.core.models.Potential_Duplicate.objects.filter")
    @patch("application.core.models.Observation.save")
    def test_set_potential_duplicate_with_open_duplicates(self, save_mock, filter_mock):
        filter_mock.return_value.count.return_value = 2

        set_potential_duplicate(self.observation)

        self.assertTrue(self.observation.has_potential_duplicates)
        save_mock.assert_not_called()

    @patch("application.core.models.Observation.save")
    def test_set_potential_duplicate_closed_observation(self, save_mock):
        self.observation.current_status = Status.STATUS_RESOLVED

        set_potential_duplicate(self.observation)

        self.assertFalse(self.observation.has_potential_duplicates)
        save_mock.assert_called_once()

    def test_find_potential_duplicates_components(self):
        # Register parsers
        command = Command()
        command.handle()

        product = Product.objects.get(id=1)
        product.has_potential_duplicates = False
        product.save()
        Observation.objects.filter(product=product).delete()

        with open(path.dirname(__file__) + "/files/duplicates_cdx.json") as testfile:
            file_upload_parameters = FileUploadParameters(
                product=Product.objects.get(id=1),
                branch=None,
                file=testfile,
                service_name="",
                docker_image_name_tag="",
                endpoint_url="",
                kubernetes_cluster="",
                kubernetes_namespace="",
                kubernetes_resource_type="",
                kubernetes_resource_name="",
                suppress_licenses=False,
                sbom=False,
            )
            with self.captureOnCommitCallbacks(execute=True):
                file_upload_observations(file_upload_parameters)

            observations = Observation.objects.filter(product=product)
            self.assertEqual(4, len(observations))
            for observation in observations:
                self.assertTrue(observation.has_potential_duplicates)
                for potential_duplicate in Potential_Duplicate.objects.filter(observation=observation):
                    self.assertEqual(
                        potential_duplicate.type,
                        Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT,
                    )

            product.refresh_from_db()
            self.assertTrue(product.has_potential_duplicates)

    def test_find_potential_duplicates_inactive_observation(self):
        # Register parsers
        command = Command()
        command.handle()

        product = Product.objects.get(id=1)
        Observation.objects.filter(product=product).delete()

        with open(path.dirname(__file__) + "/files/duplicates_cdx.json") as testfile:
            file_upload_parameters = FileUploadParameters(
                product=product,
                branch=None,
                file=testfile,
                service_name="",
                docker_image_name_tag="",
                endpoint_url="",
                kubernetes_cluster="",
                kubernetes_namespace="",
                kubernetes_resource_type="",
                kubernetes_resource_name="",
                suppress_licenses=False,
                sbom=False,
            )
            with self.captureOnCommitCallbacks(execute=True):
                file_upload_observations(file_upload_parameters)

        # The file has 2 vulnerabilities for 2 components each, so there are 2 pairs of
        # observations with the same title.
        inactive_observation = Observation.objects.filter(product=product).order_by("pk").first()
        former_duplicate = (
            Observation.objects.filter(product=product, title=inactive_observation.title)
            .exclude(pk=inactive_observation.pk)
            .get()
        )
        other_observations = Observation.objects.filter(product=product).exclude(title=inactive_observation.title)
        self.assertEqual(2, len(other_observations))

        # current_status is derived from the assessment status in normalize_observation_fields()
        inactive_observation.assessment_status = Status.STATUS_RESOLVED
        inactive_observation.save()
        self.assertEqual(Status.STATUS_RESOLVED, inactive_observation.current_status)

        find_potential_duplicates.call_local(product, None, None)

        # The inactive observation and its former duplicate are not potential duplicates anymore
        for observation in (inactive_observation, former_duplicate):
            observation.refresh_from_db()
            self.assertFalse(observation.has_potential_duplicates)
            self.assertEqual(0, Potential_Duplicate.objects.filter(observation=observation).count())
            self.assertEqual(
                0,
                Potential_Duplicate.objects.filter(potential_duplicate_observation=observation).count(),
            )

        # The other pair is unchanged
        for observation in other_observations:
            self.assertTrue(observation.has_potential_duplicates)
            self.assertEqual(1, Potential_Duplicate.objects.filter(observation=observation).count())


class TestMatchDuplicateCandidates(BaseTestCase):
    def _candidate(self, id, **kwargs):
        defaults = {
            "title": "",
            "origin_component_name": "",
            "origin_source_file": "",
            "origin_source_line_start": None,
            "scanner": "",
        }
        defaults.update(kwargs)
        return DuplicateCandidate(id=id, **defaults)

    def test_no_candidates(self):
        self.assertEqual({}, _match_duplicate_candidates([]))

    def test_component(self):
        candidates = [
            self._candidate(1, title="CVE-1", origin_component_name="component_1"),
            self._candidate(2, title="CVE-1", origin_component_name="component_2"),
            self._candidate(3, title="CVE-2", origin_component_name="component_3"),
        ]

        self.assertEqual(
            {(1, 2): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT},
            _match_duplicate_candidates(candidates),
        )

    def test_component_without_component_name(self):
        candidates = [
            self._candidate(1, title="CVE-1", origin_component_name="component_1"),
            self._candidate(2, title="CVE-1"),
        ]

        self.assertEqual({}, _match_duplicate_candidates(candidates))

    def test_component_more_than_two(self):
        candidates = [
            self._candidate(1, title="CVE-1", origin_component_name="component_1"),
            self._candidate(2, title="CVE-1", origin_component_name="component_2"),
            self._candidate(3, title="CVE-1", origin_component_name="component_3"),
        ]

        self.assertEqual(
            {
                (1, 2): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT,
                (1, 3): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT,
                (2, 3): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT,
            },
            _match_duplicate_candidates(candidates),
        )

    def test_source(self):
        candidates = [
            self._candidate(1, origin_source_file="file_1", origin_source_line_start=1, scanner="scanner_1"),
            self._candidate(2, origin_source_file="file_1", origin_source_line_start=1, scanner="scanner_2"),
            self._candidate(3, origin_source_file="file_1", origin_source_line_start=2, scanner="scanner_2"),
            self._candidate(4, origin_source_file="file_2", origin_source_line_start=1, scanner="scanner_2"),
        ]

        self.assertEqual(
            {(1, 2): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE},
            _match_duplicate_candidates(candidates),
        )

    def test_source_same_scanner(self):
        candidates = [
            self._candidate(1, origin_source_file="file_1", origin_source_line_start=1, scanner="scanner_1"),
            self._candidate(2, origin_source_file="file_1", origin_source_line_start=1, scanner="scanner_1"),
        ]

        self.assertEqual({}, _match_duplicate_candidates(candidates))

    def test_source_without_line_start(self):
        candidates = [
            self._candidate(1, origin_source_file="file_1", scanner="scanner_1"),
            self._candidate(2, origin_source_file="file_1", scanner="scanner_2"),
        ]

        self.assertEqual({}, _match_duplicate_candidates(candidates))

    def test_source_line_start_zero(self):
        candidates = [
            self._candidate(1, origin_source_file="file_1", origin_source_line_start=0, scanner="scanner_1"),
            self._candidate(2, origin_source_file="file_1", origin_source_line_start=0, scanner="scanner_2"),
        ]

        self.assertEqual(
            {(1, 2): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE},
            _match_duplicate_candidates(candidates),
        )

    def test_source_takes_precedence_over_component(self):
        candidates = [
            self._candidate(
                1,
                title="CVE-1",
                origin_component_name="component_1",
                origin_source_file="file_1",
                origin_source_line_start=1,
                scanner="scanner_1",
            ),
            self._candidate(
                2,
                title="CVE-1",
                origin_component_name="component_2",
                origin_source_file="file_1",
                origin_source_line_start=1,
                scanner="scanner_2",
            ),
        ]

        self.assertEqual(
            {(1, 2): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_SOURCE},
            _match_duplicate_candidates(candidates),
        )

    def test_id_pair_is_ordered_independently_of_the_candidate_order(self):
        candidates = [
            self._candidate(2, title="CVE-1", origin_component_name="component_2"),
            self._candidate(1, title="CVE-1", origin_component_name="component_1"),
        ]

        self.assertEqual(
            {(1, 2): Potential_Duplicate.POTENTIAL_DUPLICATE_TYPE_COMPONENT},
            _match_duplicate_candidates(candidates),
        )
