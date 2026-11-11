from unittest.mock import patch

from django.core.management import call_command

from application.core.models import Evidence, Observation, Reference
from application.import_observations.services.import_observations import (
    _prefetch_references_and_evidences,
    _update_evidences,
    _update_references,
)
from unittests.base_test_case import BaseTestCase


class TestUpdateReferencesAndEvidences(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def _observation(self) -> Observation:
        # Read the same way as the import reads the observations
        return _prefetch_references_and_evidences(Observation.objects.filter(id=1)).get()

    def _urls(self) -> list[str]:
        return list(Reference.objects.filter(observation_id=1).order_by("id").values_list("url", flat=True))

    def _evidences(self) -> list[tuple[str, str]]:
        return list(Evidence.objects.filter(observation_id=1).order_by("id").values_list("name", "evidence"))

    def test_references_are_written_and_replaced(self):
        _update_references(self._observation(), ["https://example.com/1", "https://example.com/2"])
        self.assertEqual(["https://example.com/1", "https://example.com/2"], self._urls())

        _update_references(self._observation(), ["https://example.com/3"])
        self.assertEqual(["https://example.com/3"], self._urls())

        _update_references(self._observation(), [])
        self.assertEqual([], self._urls())

    def test_unchanged_references_are_not_rewritten(self):
        _update_references(self._observation(), ["https://example.com/1", "https://example.com/2"])
        observation = self._observation()

        # Compared with the prefetched references, no select, no delete and no insert
        with self.assertNumQueries(0):
            _update_references(observation, ["https://example.com/1", "https://example.com/2"])

    def test_changed_references_drop_prefetched_references(self):
        observation = self._observation()

        _update_references(observation, ["https://example.com/1"])

        self.assertEqual(["https://example.com/1"], [reference.url for reference in observation.references.all()])

    def test_evidences_are_written_and_replaced(self):
        _update_evidences(self._observation(), [["name_1", "evidence_1"], ["name_2", "evidence_2"]])
        self.assertEqual([("name_1", "evidence_1"), ("name_2", "evidence_2")], self._evidences())

        _update_evidences(self._observation(), [["name_1", "evidence_3"]])
        self.assertEqual([("name_1", "evidence_3")], self._evidences())

        _update_evidences(self._observation(), [["name_2", "evidence_3"]])
        self.assertEqual([("name_2", "evidence_3")], self._evidences())

        _update_evidences(self._observation(), [])
        self.assertEqual([], self._evidences())

    def test_unchanged_evidences_are_not_rewritten(self):
        evidence = '{"finding": "äöü € 🙂"}'
        _update_evidences(self._observation(), [["name_1", evidence]])
        observation = self._observation()

        # Compared with the hashes of the prefetched evidences, no select, no delete and no insert
        with self.assertNumQueries(0):
            _update_evidences(observation, [["name_1", evidence]])

    def test_changed_evidences_drop_prefetched_evidences(self):
        observation = self._observation()

        _update_evidences(observation, [["name_1", "evidence_1"]])

        self.assertEqual(
            [("name_1", "evidence_1")],
            [(evidence.name, evidence.evidence) for evidence in observation.evidences.all()],
        )
