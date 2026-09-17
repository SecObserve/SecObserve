from unittest.mock import call, patch

from django.core.management import call_command

from application.core.models import Observation
from application.core.types import Status
from application.epss.models import EPSS_Score
from application.epss.queries.epss_score import get_epss_scores_by_cves
from application.epss.services.epss import (
    apply_epss,
    batched_cve_observations,
    epss_apply_observations,
)
from unittests.base_test_case import BaseTestCase


class TestEPSS(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(self, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    @patch("application.core.models.Observation.objects.filter")
    @patch("application.core.models.Observation.objects.bulk_update")
    def test_epss_apply_observations(self, mock_bulk_update, mock_filter):
        observation_1 = Observation.objects.get(id=1)
        observation_1.vulnerability_id = "CVE-1"
        observation_1.save()
        observation_2 = Observation.objects.get(id=2)
        observation_2.vulnerability_id = "CVE-2"
        observation_2.save()

        EPSS_Score.objects.create(cve="CVE-1", epss_score=0.00383, epss_percentile=0.72606)

        mock_filter.return_value = Observation.objects.all()

        epss_apply_observations()

        mock_filter.assert_called_with(vulnerability_id__startswith="CVE-")
        mock_bulk_update.assert_has_calls([call([observation_1], ["epss_score", "epss_percentile"])])

    @patch("application.epss.models.EPSS_Score.objects.filter")
    def test_apply_epss_not_cve(self, mock_epss_score):
        apply_epss(Observation.objects.all()[0])
        mock_epss_score.assert_not_called()

    @patch("application.epss.models.EPSS_Score.objects.get")
    def test_apply_epss_no_epss(self, mock_epss_score):
        mock_epss_score.side_effect = EPSS_Score.DoesNotExist()
        cve_observation = Observation(vulnerability_id="CVE-2020-1234")

        apply_epss(cve_observation)

        mock_epss_score.assert_called_with(cve="CVE-2020-1234")

    @patch("application.epss.models.EPSS_Score.objects.get")
    def test_apply_epss_cve_different(self, mock_epss_score_get):
        mock_epss_score_get.return_value = EPSS_Score(cve="CVE-2020-1234", epss_score=1, epss_percentile=1)
        cve_observation = Observation(vulnerability_id="CVE-2020-1234")

        apply_epss(cve_observation)

        self.assertEqual(cve_observation.epss_score, 100)
        self.assertEqual(cve_observation.epss_percentile, 100)
        mock_epss_score_get.assert_called_with(cve="CVE-2020-1234")

    @patch("application.epss.models.EPSS_Score.objects.get")
    def test_apply_epss_cve_same(self, mock_epss_score_get):
        mock_epss_score_get.return_value = EPSS_Score(cve="CVE-2020-1234", epss_score=0.00383, epss_percentile=0.72606)
        cve_observation = Observation(vulnerability_id="CVE-2020-1234", epss_score=0.383, epss_percentile=72.606)

        apply_epss(cve_observation)

        self.assertEqual(cve_observation.epss_score, 0.383)
        self.assertEqual(cve_observation.epss_percentile, 72.606)
        mock_epss_score_get.assert_called_with(cve="CVE-2020-1234")


class TestBatchedCveObservations(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def _cve_observations(self):
        observations = list(Observation.objects.exclude(current_status=Status.STATUS_RESOLVED)[:3])
        for number, observation in enumerate(observations):
            observation.vulnerability_id = f"CVE-2020-{number}"
            observation.save()
        return observations

    def test_all_observations_are_returned_in_batches(self):
        observations = self._cve_observations()

        batches = list(batched_cve_observations(batch_size=2))

        self.assertEqual([2, 1], [len(batch) for batch in batches])
        self.assertEqual(
            sorted(observation.pk for observation in observations),
            sorted(observation.pk for batch in batches for observation in batch),
        )

    def test_scores_are_read_with_one_query_per_batch(self):
        self._cve_observations()
        for number in range(3):
            EPSS_Score.objects.create(cve=f"CVE-2020-{number}", epss_score=0.5, epss_percentile=0.5)

        # One query for the batch of observations and one for their scores, not one per observation
        with self.assertNumQueries(2):
            observations = next(iter(batched_cve_observations(batch_size=3)))
            epss_scores = get_epss_scores_by_cves(observation.vulnerability_id for observation in observations)

        self.assertEqual(3, len(epss_scores))
