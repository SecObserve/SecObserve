import gzip
from decimal import Decimal
from unittest.mock import Mock, call, patch

from django.core.management import call_command

from application.core.models import Observation
from application.epss.models import EPSS_Score, EPSS_Status
from application.epss.services.epss import (
    apply_epss,
    epss_apply_observations,
    import_epss,
)
from unittests.base_test_case import BaseTestCase


class TestEPSS(BaseTestCase):
    @patch("application.epss.services.epss.requests.get")
    def test_import_epss_updates_existing_score(self, mock_get):
        EPSS_Score.objects.create(cve="CVE-2025-5642", epss_score=0.10000, epss_percentile=0.20000)
        mock_get.return_value = self._mock_epss_response(
            b"#model_version:v2024.03.14,score_date:2026-05-18\n"
            b"cve,epss,percentile\n"
            b"CVE-2025-5642,0.30000,0.40000\n"
        )

        message = import_epss()

        score = EPSS_Score.objects.get(cve="CVE-2025-5642")
        self.assertEqual(score.epss_score, Decimal("0.30000"))
        self.assertEqual(score.epss_percentile, Decimal("0.40000"))
        self.assertEqual(EPSS_Score.objects.count(), 1)
        self.assertEqual(message, "Imported 1 EPSS scores.")

    @patch("application.epss.services.epss.requests.get")
    def test_import_epss_deduplicates_feed_and_keeps_last_score(self, mock_get):
        mock_get.return_value = self._mock_epss_response(
            b"#model_version:v2024.03.14,score_date:2026-05-18\n"
            b"cve,epss,percentile\n"
            b"CVE-2025-5642,0.10000,0.20000\n"
            b"CVE-2025-5642,0.30000,0.40000\n"
        )

        message = import_epss()

        score = EPSS_Score.objects.get(cve="CVE-2025-5642")
        self.assertEqual(score.epss_score, Decimal("0.30000"))
        self.assertEqual(score.epss_percentile, Decimal("0.40000"))
        self.assertEqual(EPSS_Score.objects.count(), 1)
        self.assertEqual(EPSS_Status.load().score_date.isoformat(), "2026-05-18")
        self.assertEqual(message, "Imported 1 EPSS scores.")

    @staticmethod
    def _mock_epss_response(content: bytes) -> Mock:
        response = Mock()
        response.content = gzip.compress(content)
        response.raise_for_status.return_value = None
        return response

    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
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
