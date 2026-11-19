from application.core.models import Branch
from application.core.queries.observation import (
    count_active_observations_by_priority,
    count_active_observations_by_product_and_priority,
)
from application.core.types import Status
from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin


class TestCountActiveObservationsByPriority(ObservationFixtureMixin, BaseTestCase):
    def test_count_by_priority_only_active_on_default_branch(self):
        other = Branch.objects.create(product=self.product_1, name="other")
        self._observation("p1", priority=1)
        self._observation("p1 again", priority=1)
        self._observation("p2", priority=2)
        self._observation("no priority")
        self._observation("resolved", priority=1, status=Status.STATUS_RESOLVED)
        self._observation("other branch", priority=1, branch=other)

        self.assertEqual(count_active_observations_by_priority(self.product_1), {1: 2, 2: 1})
        self.assertEqual(count_active_observations_by_priority(self.product_1, other), {1: 1})

    def test_count_by_product_and_priority(self):
        self._observation("p1", priority=1)

        counts = count_active_observations_by_product_and_priority([self.product_1])

        self.assertEqual(counts, {self.product_1.pk: {1: 1}})
