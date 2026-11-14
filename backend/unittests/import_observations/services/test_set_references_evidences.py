from unittest.mock import patch

from django.core.management import call_command

from application.core.models import Evidence, Observation, Reference
from application.import_observations.services.import_observations import (
    _get_references_and_evidences,
    _md5,
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
        return Observation.objects.get(id=1)

    def _references_before(self) -> list[str]:
        # Read the same way as the import reads them
        references, _ = _get_references_and_evidences([self._observation()])
        return references.get(1, [])

    def _evidences_before(self) -> list[tuple[str, str]]:
        # Read the same way as the import reads them
        _, evidences = _get_references_and_evidences([self._observation()])
        return evidences.get(1, [])

    def _urls(self) -> list[str]:
        return list(Reference.objects.filter(observation_id=1).order_by("id").values_list("url", flat=True))

    def _evidences(self) -> list[tuple[str, str]]:
        return list(Evidence.objects.filter(observation_id=1).order_by("id").values_list("name", "evidence"))

    def test_get_references_and_evidences_no_observations(self):
        with self.assertNumQueries(0):
            references, evidences = _get_references_and_evidences([])

        self.assertEqual({}, references)
        self.assertEqual({}, evidences)

    def test_get_references_and_evidences(self):
        observation_1 = Observation.objects.get(id=1)
        observation_2 = Observation.objects.get(id=2)
        Reference.objects.create(observation=observation_1, url="https://example.com/2")
        Reference.objects.create(observation=observation_1, url="https://example.com/1")
        Reference.objects.create(observation=observation_2, url="https://example.com/3")
        Evidence.objects.create(observation=observation_1, name="name_1", evidence="evidence_1")
        Evidence.objects.create(observation=observation_2, name="name_2", evidence="evidence_2")

        # One query for the references and one for the evidences
        with self.assertNumQueries(2):
            references, evidences = _get_references_and_evidences([observation_1, observation_2])

        # In the order they have been written, the first evidences are from the fixtures
        self.assertEqual(
            {1: ["https://example.com/2", "https://example.com/1"], 2: ["https://example.com/3"]},
            references,
        )
        self.assertEqual(
            {
                1: [("db_evidence_internal", _md5("abc")), ("name_1", _md5("evidence_1"))],
                2: [("db_evidence_external", _md5("xyz")), ("name_2", _md5("evidence_2"))],
            },
            evidences,
        )

    def test_references_are_written_and_replaced(self):
        _update_references(
            self._observation(), ["https://example.com/1", "https://example.com/2"], self._references_before()
        )
        self.assertEqual(["https://example.com/1", "https://example.com/2"], self._urls())

        _update_references(self._observation(), ["https://example.com/3"], self._references_before())
        self.assertEqual(["https://example.com/3"], self._urls())

        _update_references(self._observation(), [], self._references_before())
        self.assertEqual([], self._urls())

    def test_unchanged_references_are_not_rewritten(self):
        _update_references(
            self._observation(), ["https://example.com/1", "https://example.com/2"], self._references_before()
        )
        observation = self._observation()
        references_before = self._references_before()

        # Compared with the references read before, no select, no delete and no insert
        with self.assertNumQueries(0):
            _update_references(observation, ["https://example.com/1", "https://example.com/2"], references_before)

    def test_evidences_are_written_and_replaced(self):
        _update_evidences(
            self._observation(), [["name_1", "evidence_1"], ["name_2", "evidence_2"]], self._evidences_before()
        )
        self.assertEqual([("name_1", "evidence_1"), ("name_2", "evidence_2")], self._evidences())

        _update_evidences(self._observation(), [["name_1", "evidence_3"]], self._evidences_before())
        self.assertEqual([("name_1", "evidence_3")], self._evidences())

        _update_evidences(self._observation(), [["name_2", "evidence_3"]], self._evidences_before())
        self.assertEqual([("name_2", "evidence_3")], self._evidences())

        _update_evidences(self._observation(), [], self._evidences_before())
        self.assertEqual([], self._evidences())

    def test_unchanged_evidences_are_not_rewritten(self):
        evidence = '{"finding": "äöü € 🙂"}'
        _update_evidences(self._observation(), [["name_1", evidence]], self._evidences_before())
        observation = self._observation()
        evidences_before = self._evidences_before()

        # Compared with the hashes read before, no select, no delete and no insert
        with self.assertNumQueries(0):
            _update_evidences(observation, [["name_1", evidence]], evidences_before)
