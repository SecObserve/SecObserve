from unittest.mock import patch

from django.core.management import call_command

from application.core.models import Observation
from application.import_observations.services.import_observations import (
    _set_evidences,
    _set_references,
)
from unittests.base_test_case import BaseTestCase


class TestSetReferencesAndEvidences(BaseTestCase):
    @classmethod
    @patch("application.core.signals.get_current_user")
    def setUpClass(cls, mock_user):
        mock_user.return_value = None
        call_command("loaddata", "unittests/fixtures/unittests_fixtures.json")
        super().setUpClass()

    def _urls(self, observation: Observation) -> list[str]:
        return list(observation.references.order_by("id").values_list("url", flat=True))

    def _evidences(self, observation: Observation) -> list[tuple[str, str]]:
        return list(observation.evidences.order_by("id").values_list("name", "evidence"))

    def test_references_are_written_and_replaced(self):
        observation = Observation.objects.get(id=1)

        _set_references(observation, ["https://example.com/1", "https://example.com/2"])
        self.assertEqual(["https://example.com/1", "https://example.com/2"], self._urls(observation))

        _set_references(observation, ["https://example.com/3"])
        self.assertEqual(["https://example.com/3"], self._urls(observation))

        _set_references(observation, [])
        self.assertEqual([], self._urls(observation))

    def test_unchanged_references_are_not_rewritten(self):
        observation = Observation.objects.get(id=1)
        _set_references(observation, ["https://example.com/1", "https://example.com/2"])

        # Only the query that compares them, no delete and no insert
        with self.assertNumQueries(1):
            _set_references(observation, ["https://example.com/1", "https://example.com/2"])

    def test_evidences_are_written_and_replaced(self):
        observation = Observation.objects.get(id=1)

        _set_evidences(observation, [["name_1", "evidence_1"], ["name_2", "evidence_2"]])
        self.assertEqual([("name_1", "evidence_1"), ("name_2", "evidence_2")], self._evidences(observation))

        _set_evidences(observation, [["name_1", "evidence_3"]])
        self.assertEqual([("name_1", "evidence_3")], self._evidences(observation))

        _set_evidences(observation, [])
        self.assertEqual([], self._evidences(observation))

    def test_unchanged_evidences_are_not_rewritten(self):
        observation = Observation.objects.get(id=1)
        _set_evidences(observation, [["name_1", "evidence_1"]])

        with self.assertNumQueries(1):
            _set_evidences(observation, [["name_1", "evidence_1"]])
