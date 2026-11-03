from django.db.models import Q

from application.core.models import Branch, Product
from application.core.queries.observation import count_active_observations_by_severity
from application.core.types import Status
from unittests.base_test_case import BaseTestCase
from unittests.core.observation_fixtures import ObservationFixtureMixin

KEV = Q(cve_found_in__icontains="CISA KEV")


class TestCountActiveObservationsBySeverity(ObservationFixtureMixin, BaseTestCase):
    def test_without_filter_counts_all_active_on_default_branch(self):
        self._observation("cve")
        self._observation("secret", vulnerability_id="")
        self._observation("resolved", status=Status.STATUS_RESOLVED)
        other = Branch.objects.create(name="other", product=self.product_1)
        self._observation("other-branch", branch=other)

        self.assertEqual(count_active_observations_by_severity(self.product_1)["Critical"], 2)

    def test_extra_filter_applies(self):
        self._observation("kev", cve_found_in="CISA KEV")
        self._observation("plain")

        self.assertEqual(count_active_observations_by_severity(self.product_1, extra_filter=KEV)["Critical"], 1)

    def test_branch_counts_only_that_branch(self):
        other = Branch.objects.create(name="other", product=self.product_1)
        self._observation("default")
        self._observation("other-1", branch=other)
        self._observation("other-2", branch=other)

        self.assertEqual(count_active_observations_by_severity(self.product_1, branch=other)["Critical"], 2)

    def test_all_products_when_product_is_none(self):
        product_2 = Product.objects.create(name="product_2")
        branch_2 = Branch.objects.create(name="main", product=product_2, is_default_branch=True)
        self._observation("one")
        self._observation("two", product=product_2, branch=branch_2)

        self.assertEqual(count_active_observations_by_severity(None)["Critical"], 2)

    def test_all_severities_present(self):
        counts = count_active_observations_by_severity(self.product_1)

        self.assertEqual(set(counts), {"Critical", "High", "Medium", "Low", "None", "Unknown"})
        self.assertEqual(sum(counts.values()), 0)
